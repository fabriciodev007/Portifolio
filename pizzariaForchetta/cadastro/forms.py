from decimal import Decimal

from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import Permission
from django.db import transaction
from django.db.utils import OperationalError

from .models import BordaPreco, Cardapio, Cliente, Endereco, Funcionario, Pizza, Produto


def _has_duplicate_username(username, instance=None):
    user_model = get_user_model()
    normalized_username = username.strip()
    if not normalized_username:
        return False

    queryset = user_model.objects.filter(username__iexact=normalized_username)
    if instance is not None:
        user = getattr(instance, 'usuario', None)
        if user is not None and getattr(user, 'pk', None) is not None:
            queryset = queryset.exclude(pk=user.pk)
    return queryset.exists()


class EnderecoForm(forms.ModelForm):
    class Meta:
        model = Endereco
        fields = ['cep', 'rua', 'numero', 'bairro', 'cidade', 'estado']
        widgets = {
            'cep': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Digite o CEP',
                'maxlength': '9',
            }),
            'rua': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Rua',
            }),
            'numero': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Número',
            }),
            'bairro': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Bairro',
            }),
            'cidade': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Cidade',
            }),
            'estado': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Estado',
            }),
        }


class BordaPrecoForm(forms.ModelForm):
    class Meta:
        model = BordaPreco
        fields = ['borda', 'preco']
        widgets = {
            'borda': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex.: Catupiry'}),
            'preco': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': '0.00'}),
        }

    def clean_borda(self):
        borda = self.cleaned_data.get('borda', '').strip()
        if not borda:
            raise forms.ValidationError('Informe o nome da borda.')

        queryset = BordaPreco.objects.filter(borda__iexact=borda)
        if self.instance and self.instance.pk:
            queryset = queryset.exclude(pk=self.instance.pk)
        if queryset.exists():
            raise forms.ValidationError('Este tipo de borda ja existe.')
        return borda


class CardapioForm(forms.ModelForm):
    class Meta:
        model = Cardapio
        fields = ['prod', 'pizz']
        widgets = {
            'prod': forms.Select(attrs={'class': 'form-select'}),
            'pizz': forms.Select(attrs={'class': 'form-select'}),
        }


class FuncionarioForm(forms.Form):
    nomeFunc = forms.CharField(
        label='Nome completo',
        max_length=70,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nome completo'}),
    )
    cpf = forms.CharField(
        label='CPF',
        max_length=14,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '000.000.000-00'}),
    )
    telFunc = forms.CharField(
        label='Telefone',
        max_length=15,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '11999999999'}),
    )
    endFunc = forms.ModelChoiceField(
        label='Endereço',
        queryset=Endereco.objects.all(),
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    username = forms.CharField(
        label='Usuário',
        max_length=150,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Usuário para login'}),
    )
    email = forms.EmailField(
        label='E-mail',
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'funcionario@email.com'}),
    )
    password1 = forms.CharField(
        label='Senha',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Senha'}),
    )
    password2 = forms.CharField(
        label='Confirmar senha',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirmar senha'}),
    )

    def __init__(self, *args, **kwargs):
        self.instance = kwargs.pop('instance', None)
        super().__init__(*args, **kwargs)
        if self.instance:
            self.fields['nomeFunc'].initial = self.instance.nomeFunc
            self.fields['cpf'].initial = self.instance.cpf
            self.fields['telFunc'].initial = self.instance.telFunc
            self.fields['endFunc'].initial = self.instance.endFunc
            self.fields['username'].initial = self.instance.usuario.username if self.instance.usuario else ''
            self.fields['email'].initial = self.instance.usuario.email if self.instance.usuario else ''
            self.fields['password1'].required = False
            self.fields['password2'].required = False

    def clean_cpf(self):
        cpf = ''.join(filter(str.isdigit, self.cleaned_data.get('cpf', '')))
        if len(cpf) != 11:
            raise forms.ValidationError('Informe um CPF com 11 digitos.')
        if Funcionario.objects.filter(cpf=cpf).exclude(pk=getattr(self.instance, 'pk', None)).exists():
            raise forms.ValidationError('Este CPF ja esta cadastrado.')
        return cpf

    def clean_username(self):
        username = self.cleaned_data.get('username', '').strip()
        if _has_duplicate_username(username, self.instance):
            raise forms.ValidationError('Este usuário ja esta cadastrado.')
        return username

    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()
        user_model = get_user_model()
        if user_model.objects.filter(email__iexact=email).exclude(pk=getattr(self.instance.usuario, 'pk', None) if self.instance and self.instance.usuario else None).exists():
            raise forms.ValidationError('Este e-mail ja esta cadastrado.')
        return email

    def clean_password2(self):
        password1 = self.cleaned_data.get('password1', '')
        password2 = self.cleaned_data.get('password2', '')
        if password1 or password2:
            if password1 != password2:
                raise forms.ValidationError('As senhas nao conferem.')
            if len(password1) < 8:
                raise forms.ValidationError('A senha deve ter pelo menos 8 caracteres.')
        elif not self.instance:
            raise forms.ValidationError('Informe uma senha para o usuário.')
        return password2

    @transaction.atomic
    def save(self):
        user_model = get_user_model()
        user = self.instance.usuario if self.instance and self.instance.usuario else None
        if user is None:
            user = user_model.objects.create_user(
                username=self.cleaned_data['username'],
                email=self.cleaned_data['email'],
                password=self.cleaned_data['password1'],
                is_staff=True,
                is_active=True,
            )
        else:
            user.username = self.cleaned_data['username']
            user.email = self.cleaned_data['email']
            if self.cleaned_data.get('password1'):
                user.set_password(self.cleaned_data['password1'])
            user.is_staff = True
            user.is_active = True
            user.save()

        user.first_name = self.cleaned_data['nomeFunc']
        user.save(update_fields=['first_name', 'email', 'is_staff', 'is_active'])

        funcionario = self.instance or Funcionario()
        funcionario.nomeFunc = self.cleaned_data['nomeFunc']
        funcionario.cpf = self.cleaned_data['cpf']
        funcionario.telFunc = self.cleaned_data['telFunc']
        funcionario.endFunc = self.cleaned_data['endFunc']
        funcionario.usuario = user
        funcionario.save()

        permissions = Permission.objects.filter(
            content_type__app_label='cadastro',
            codename__in=['add_produto', 'change_produto', 'view_produto', 'add_fornecedor', 'change_fornecedor', 'view_fornecedor', 'add_entregador', 'change_entregador', 'view_entregador'],
        )
        user.user_permissions.set(list(permissions))
        return funcionario


class ClienteRegisterForm(UserCreationForm):
    nome_cliente = forms.CharField(
        label='Nome completo',
        max_length=70,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nome completo'}),
    )
    cpf = forms.CharField(
        label='CPF',
        max_length=14,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '000.000.000-00'}),
    )
    tel_clente = forms.CharField(
        label='Telefone',
        max_length=15,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '11999999999'}),
    )
    email = forms.EmailField(
        label='E-mail',
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'voce@email.com'}),
    )
    cep = forms.CharField(
        label='CEP',
        max_length=9,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '00000-000'}),
    )
    rua = forms.CharField(
        label='Rua',
        max_length=100,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Rua'}),
    )
    numero = forms.CharField(
        label='Numero',
        max_length=20,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Numero'}),
    )
    bairro = forms.CharField(
        label='Bairro',
        max_length=100,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Bairro'}),
    )
    cidade = forms.CharField(
        label='Cidade',
        max_length=100,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Cidade'}),
    )
    estado = forms.CharField(
        label='Estado',
        max_length=50,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Estado'}),
    )

    class Meta(UserCreationForm.Meta):
        model = get_user_model()
        fields = ('username', 'email', 'password1', 'password2')
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nome de usuario'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Nome de usuario'})
        self.fields['password1'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Senha'})
        self.fields['password2'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Confirmar senha'})

    def clean_username(self):
        username = self.cleaned_data.get('username', '').strip()
        if _has_duplicate_username(username):
            raise forms.ValidationError('Este usuário ja esta cadastrado.')
        return username

    def clean_cpf(self):
        cpf = ''.join(filter(str.isdigit, self.cleaned_data.get('cpf', '')))
        if len(cpf) != 11:
            raise forms.ValidationError('Informe um CPF com 11 digitos.')
        try:
            if Cliente.objects.filter(cpf=cpf).exists():
                raise forms.ValidationError('Este CPF ja esta cadastrado.')
        except OperationalError:
            pass
        return cpf

    def clean_tel_clente(self):
        telefone = ''.join(filter(str.isdigit, self.cleaned_data.get('tel_clente', '')))
        if len(telefone) not in (10, 11):
            raise forms.ValidationError('Informe um telefone com DDD valido.')
        if len(telefone) == 10:
            # Ajusta telefone para 11 dígitos ao salvar, assumindo formato brasileiro com DDD + 8 dígitos
            telefone = f'{telefone[:2]}9{telefone[2:]}'
        return telefone

    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()
        user_model = get_user_model()
        if user_model.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError('Este e-mail ja esta cadastrado.')
        return email

    @transaction.atomic
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['nome_cliente']
        if commit:
            user.save()
            endereco = Endereco.objects.create(
                cep=self.cleaned_data['cep'],
                rua=self.cleaned_data['rua'],
                numero=self.cleaned_data['numero'],
                bairro=self.cleaned_data['bairro'],
                cidade=self.cleaned_data['cidade'],
                estado=self.cleaned_data['estado'],
            )
            Cliente.objects.create(
                nome_cliente=self.cleaned_data['nome_cliente'],
                cpf=self.cleaned_data['cpf'],
                tel_clente=self.cleaned_data['tel_clente'],
                end_cliente=endereco,
                usuario=user,
            )
        return user
