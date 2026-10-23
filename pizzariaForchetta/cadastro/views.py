import re
import urllib.request
import urllib.error
import xml.etree.ElementTree as ET
from urllib.parse import urlparse

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login as auth_login
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.views import PasswordResetView
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic.edit import CreateView, UpdateView, DeleteView, FormView
from django.views.generic.list import ListView 

from .models import Endereco, Cliente, Funcionario, Taxa, Entregador, Pizza, Fornecedor, Produto, Cardapio, BordaPreco
from .forms import BordaPrecoForm, CardapioForm, ClienteRegisterForm, EnderecoForm, FuncionarioForm

from django.urls import reverse_lazy

class AdminRequiredMixin(UserPassesTestMixin):
    raise_exception = True

    def test_func(self):
        return self.request.user.is_active and self.request.user.is_staff

# Create your views here.
# todos os Create 
class ClienteCreate(LoginRequiredMixin, AdminRequiredMixin, CreateView):
    model = Cliente
    fields =['nome_cliente', 'cpf', 'tel_clente', 'end_cliente']
    template_name = 'cadastro/formC.html'

    def form_valid(self, form):
        self.object = form.save()
        messages.success(self.request, 'Cliente cadastrado com sucesso!')
        context = self.get_context_data(form=self.get_form_class()())
        return self.render_to_response(context)

class EnderecoCreate(LoginRequiredMixin, AdminRequiredMixin, CreateView):
    model = Endereco
    form_class = EnderecoForm
    template_name = 'cadastro/form_endereco.html'

    def form_valid(self, form):
        self.object = form.save()
        messages.success(self.request, 'Endereço cadastrado com sucesso!')
        context = self.get_context_data(form=self.get_form_class()())
        return self.render_to_response(context)
    
class FuncCreate(LoginRequiredMixin, AdminRequiredMixin, CreateView):
    model = Funcionario
    form_class = FuncionarioForm
    template_name = 'cadastro/form.html'

    def form_valid(self, form):
        self.object = form.save()
        messages.success(self.request, 'Funcionário cadastrado com sucesso!')
        context = self.get_context_data(form=self.get_form_class()())
        return self.render_to_response(context)

class TaxaCreate(LoginRequiredMixin, AdminRequiredMixin, CreateView):
    model = Taxa
    fields =['valorT', 'valorTT', 'edCliente']
    template_name = 'cadastro/form.html'
    success_url = reverse_lazy('inicio')
    
class EntregCreate(LoginRequiredMixin, AdminRequiredMixin, CreateView):
    model = Entregador
    fields =['nomeEntreg', 'telEntreg', 'endEntreg']
    template_name = 'cadastro/form.html'

    def form_valid(self, form):
        self.object = form.save()
        messages.success(self.request, 'Entregador cadastrado com sucesso!')
        context = self.get_context_data(form=self.get_form_class()())
        return self.render_to_response(context)
    
class PizzaCreate(LoginRequiredMixin, AdminRequiredMixin, CreateView):
    model = Pizza
    fields =['pizza', 'desc', 'vlbruto', 'vlvenda', 'vlr12pdc']
    template_name = 'cadastro/form.html'
    success_url = reverse_lazy('inicio')
    
class FornecedCreate(LoginRequiredMixin, AdminRequiredMixin, CreateView):
    model = Fornecedor
    fields =['nomeFornec', 'telFornec', 'cnpj', 'endFornec']
    template_name = 'cadastro/form.html'

    def form_valid(self, form):
        self.object = form.save()
        messages.success(self.request, 'Fornecedor cadastrado com sucesso!')
        context = self.get_context_data(form=self.get_form_class()())
        return self.render_to_response(context)
    
class ProdutoCreate(LoginRequiredMixin, AdminRequiredMixin, CreateView):
    model = Produto
    fields =['nomeProd', 'descProd', 'dataval', 'dataCompra', 'vlUnid', 'vlT', 'fornec']
    template_name = 'cadastro/form.html'

    def form_valid(self, form):
        self.object = form.save()
        messages.success(self.request, 'Produto cadastrado com sucesso!')
        context = self.get_context_data(form=self.get_form_class()())
        return self.render_to_response(context)
    
class CardapCreate(LoginRequiredMixin, AdminRequiredMixin, CreateView):
    model = Cardapio
    form_class = CardapioForm
    template_name = 'cadastro/form.html'
    success_url = reverse_lazy('inicio')
    
    
###################  UpdateView  #####################
    
    
class ClienteUpdate(LoginRequiredMixin, AdminRequiredMixin, UpdateView):
    model = Cliente
    fields =['nome_cliente', 'cpf', 'tel_clente', 'end_cliente']
    template_name = 'cadastro/form.html'
    success_url = reverse_lazy('inicio')

class EnderecoUpdate(LoginRequiredMixin, AdminRequiredMixin, UpdateView):
    model = Endereco
    form_class = EnderecoForm
    template_name = 'cadastro/form_endereco.html'
    success_url = reverse_lazy('inicio')
    

class UserRegisterView(FormView):
    template_name = 'registration/register.html'
    form_class = ClienteRegisterForm
    success_url = reverse_lazy('cardaprincipal')

    def form_valid(self, form):
        user = form.save()
        auth_login(self.request, user)
        self.request.session['cart'] = []
        self.request.session.pop('half_pending', None)
        self.request.session.pop('half_message', None)
        messages.success(self.request, 'Cadastro realizado com sucesso!')
        return super().form_valid(form)


class ClienteRegisterView(UserRegisterView):
    template_name = 'registration/register_cliente.html'


class ClientePasswordResetView(PasswordResetView):
    template_name = 'registration/password_reset_form.html'
    email_template_name = 'registration/password_reset_email.html'
    subject_template_name = 'registration/password_reset_subject.txt'
    success_url = reverse_lazy('password_reset_done')

    def _build_extra_email_context(self):
        base_url = (getattr(settings, 'PASSWORD_RESET_BASE_URL', '') or '').strip()
        if not base_url:
            return None

        parsed = urlparse(base_url)
        if not parsed.scheme:
            parsed = urlparse(f'https://{base_url}')

        return {
            'domain': parsed.netloc,
            'protocol': parsed.scheme,
        }

    def form_valid(self, form):
        self.extra_email_context = self._build_extra_email_context()
        return super().form_valid(form)


@require_GET
def consulta_cep_correios(request):
    cep = request.GET.get('cep', '')
    cep = re.sub(r'\D', '', cep)
    if len(cep) != 8:
        return JsonResponse({'success': False, 'error': 'CEP inválido'}, status=400)

    envelope = '''<?xml version="1.0" encoding="UTF-8"?>
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:cli="http://cliente.bean.master.sigep.bsb.correios.com.br/">
  <soapenv:Header/>
  <soapenv:Body>
    <cli:consultaCEP>
      <cep>%s</cep>
    </cli:consultaCEP>
  </soapenv:Body>
</soapenv:Envelope>''' % cep

    headers = {
        'Content-Type': 'text/xml; charset=utf-8',
        'User-Agent': 'Mozilla/5.0 (compatible; Python/Django)',
        'SOAPAction': '"consultaCEP"',
    }

    try:
        request_obj = urllib.request.Request(
            'https://apps.correios.com.br/SigepMasterJPA/AtendeClienteService/AtendeCliente',
            data=envelope.encode('utf-8'),
            headers=headers,
            method='POST',
        )
        with urllib.request.urlopen(request_obj, timeout=20) as response:
            raw = response.read()
    except urllib.error.HTTPError as exc:
        return JsonResponse({'success': False, 'error': f'Correios retornou HTTP {exc.code}'}, status=502)
    except urllib.error.URLError as exc:
        return JsonResponse({'success': False, 'error': f'Erro ao conectar com Correios: {exc.reason}'}, status=502)

    try:
        tree = ET.fromstring(raw)
    except ET.ParseError:
        return JsonResponse({'success': False, 'error': 'Resposta inválida dos Correios'}, status=502)

    return_node = None
    for node in tree.iter():
        if node.tag.endswith('return'):
            return_node = node
            break
    if return_node is None:
        return JsonResponse({'success': False, 'error': 'Resposta do Correios sem dados'}, status=502)

    data = {child.tag.split('}')[-1]: (child.text or '').strip() for child in return_node}
    if not data or not data.get('cep'):
        return JsonResponse({'success': False, 'error': 'CEP não encontrado pelos Correios'}, status=404)
    if data.get('resultado') and data.get('resultado') != '1':
        return JsonResponse({'success': False, 'error': data.get('resultado_txt', 'CEP não encontrado')}, status=404)

    rua = data.get('logradouro', '') or ''
    tipo = data.get('tipoLogradouro', '') or ''
    if tipo and rua and not rua.startswith(tipo):
        rua = f'{tipo} {rua}'

    return JsonResponse({
        'success': True,
        'cep': data.get('cep', ''),
        'rua': rua,
        'bairro': data.get('bairro', ''),
        'cidade': data.get('localidade', ''),
        'estado': data.get('uf', ''),
    })


class FuncUpdate(LoginRequiredMixin, AdminRequiredMixin, UpdateView):
    model = Funcionario
    form_class = FuncionarioForm
    template_name = 'cadastro/form.html'
    success_url = reverse_lazy('listar-funcionario')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['instance'] = self.object
        return kwargs

    def form_valid(self, form):
        form.save()
        return super().form_valid(form)

class TaxaUpdate(LoginRequiredMixin, AdminRequiredMixin, UpdateView):
    model = Taxa
    fields =['valorT', 'valorTT', 'edCliente']
    template_name = 'cadastro/form.html'
    success_url = reverse_lazy('inicio')
    
class EntregUpdate(LoginRequiredMixin, AdminRequiredMixin, UpdateView):
    model = Entregador
    fields =['nomeEntreg', 'telEntreg', 'endEntreg']
    template_name = 'cadastro/form.html'
    success_url = reverse_lazy('inicio')
    
class PizzaUpdate(LoginRequiredMixin, AdminRequiredMixin, UpdateView):
    model = Pizza
    fields =['pizza', 'desc', 'vlbruto', 'vlvenda', 'vlr12pdc']
    template_name = 'cadastro/form.html'
    success_url = reverse_lazy('inicio')
    
class FornecUpdate(LoginRequiredMixin, AdminRequiredMixin, UpdateView):
    model = Fornecedor
    fields =['nomeFornec', 'telFornec', 'cnpj', 'endFornec']
    template_name = 'cadastro/form.html'
    success_url = reverse_lazy('inicio')
    
class ProdutoUpdate(LoginRequiredMixin, AdminRequiredMixin, UpdateView):
    model = Produto
    fields =['nomeProd', 'descProd', 'dataval', 'dataCompra', 'vlUnid', 'vlT', 'fornec']
    template_name = 'cadastro/form.html'
    success_url = reverse_lazy('inicio')
    
class CardapUpdate(LoginRequiredMixin, AdminRequiredMixin, UpdateView):
    model = Cardapio
    form_class = CardapioForm
    template_name = 'cadastro/form.html'
    success_url = reverse_lazy('inicio')
    
    
    
    ########### DELETAR #####################
    
class ClienteDelete(LoginRequiredMixin, AdminRequiredMixin, DeleteView):
    model = Cliente
    template_name = 'cadastro/form-excluir.html'
    success_url = reverse_lazy('listar-cliente')

    
class EndDelete(LoginRequiredMixin, AdminRequiredMixin, DeleteView):
    model = Endereco
    template_name = 'cadastro/form-excluir.html'
    success_url = reverse_lazy('inicio')
    

    
class TaxaDelete(LoginRequiredMixin, AdminRequiredMixin, DeleteView):
    model = Taxa
    template_name = 'cadastro/form-excluir.html'
    success_url = reverse_lazy('inicio')

    
class FuncDelete(LoginRequiredMixin, AdminRequiredMixin, DeleteView):
    model = Funcionario
    template_name = 'cadastro/form-excluir.html'
    success_url = reverse_lazy('inicio')
    
    
class EntregDelete(LoginRequiredMixin, AdminRequiredMixin, DeleteView):
    model = Entregador
    template_name = 'cadastro/form-excluir.html'
    success_url = reverse_lazy('inicio')
    
    
class PizzaDelete(LoginRequiredMixin, AdminRequiredMixin, DeleteView):
    model = Pizza
    template_name = 'cadastro/form-excluir.html'
    success_url = reverse_lazy('inicio')
    
    
class FornecDelete(LoginRequiredMixin, AdminRequiredMixin, DeleteView):
    model = Fornecedor
    template_name = 'cadastro/form-excluir.html'
    success_url = reverse_lazy('inicio')
    
    
class ProdutoDelete(LoginRequiredMixin, AdminRequiredMixin, DeleteView):
    model = Produto
    template_name = 'cadastro/form-excluir.html'
    success_url = reverse_lazy('inicio')
    
    
class CardapDelete(LoginRequiredMixin, AdminRequiredMixin, DeleteView):
    model = Cardapio
    template_name = 'cadastro/form-excluir.html'
    success_url = reverse_lazy('inicio')
    
    
############## LISTA ###########

class ClienteList(LoginRequiredMixin, AdminRequiredMixin, ListView):
    model = Cliente
    template_name= 'cadastro/lista/cliente-list.html'
    
class EndList(LoginRequiredMixin, AdminRequiredMixin, ListView):
    model = Endereco
    template_name= 'cadastro/lista/endereco.html'
    
class TaxaList(LoginRequiredMixin, AdminRequiredMixin, ListView):
    model = Taxa
    template_name= 'cadastro/lista/taxa.html'
    
class FuncList(LoginRequiredMixin, AdminRequiredMixin, ListView):
    model = Funcionario
    template_name= 'cadastro/lista/funcionario-list.html'
    
class EntregList(LoginRequiredMixin, AdminRequiredMixin, ListView):
    model = Entregador
    template_name= 'cadastro/lista/Entregador.html'

class PizzaList(LoginRequiredMixin, AdminRequiredMixin, ListView):
    model =Pizza
    template_name= 'cadastro/lista/pizza.html'

class FornecList(LoginRequiredMixin, AdminRequiredMixin, ListView):
    model = Cliente
    template_name= 'cadastro/lista/fornecedor.html'
    

class ProdutoList(LoginRequiredMixin, AdminRequiredMixin, ListView):
    model = Cliente
    template_name= 'cadastro/lista/produto.html'
    
class CardapioList(LoginRequiredMixin, AdminRequiredMixin, ListView):
    model = Cardapio
    template_name= 'cadastro/lista/cardapio.html'


class BordaPrecoCreate(LoginRequiredMixin, AdminRequiredMixin, CreateView):
    model = BordaPreco
    form_class = BordaPrecoForm
    template_name = 'cadastro/form.html'
    success_url = reverse_lazy('listar-borda-preco')


class BordaPrecoUpdate(LoginRequiredMixin, AdminRequiredMixin, UpdateView):
    model = BordaPreco
    form_class = BordaPrecoForm
    template_name = 'cadastro/form.html'
    success_url = reverse_lazy('listar-borda-preco')


class BordaPrecoDelete(LoginRequiredMixin, AdminRequiredMixin, DeleteView):
    model = BordaPreco
    template_name = 'cadastro/form-excluir.html'
    success_url = reverse_lazy('listar-borda-preco')


class BordaPrecoList(LoginRequiredMixin, AdminRequiredMixin, ListView):
    model = BordaPreco
    template_name = 'cadastro/lista/borda-preco.html'