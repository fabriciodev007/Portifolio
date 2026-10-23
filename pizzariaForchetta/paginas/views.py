from decimal import Decimal
from functools import lru_cache
from math import ceil
import re
from urllib.parse import quote

from django import forms
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.mail import send_mail
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views.generic import FormView, TemplateView

from geopy.distance import geodesic
from geopy.exc import GeocoderServiceError
from geopy.geocoders import Nominatim

from cadastro.models import BordaPreco, Cardapio, Cliente, Endereco, Pizza, Produto, Taxa


PIZZARIA_ADDRESS = {
    'rua': 'Avenida Tarsila do Amaral',
    'numero': '1235',
    'bairro': 'Jardim Amanda II',
    'cidade': 'Hortolândia',
    'estado': 'SP',
    'cep': '13188-160',
}

PIZZARIA_COORDS = (-22.905049, -47.2401812)


def _build_whatsapp_url(phone_number, message):
    normalized_phone = ''.join(filter(str.isdigit, str(phone_number)))
    encoded_text = quote(message, safe='')
    return f'https://wa.me/{normalized_phone}?text={encoded_text}'


def _address_to_dict(address):
    if address is None:
        return {}

    if isinstance(address, dict):
        data = address
    else:
        data = {
            'rua': getattr(address, 'rua', ''),
            'numero': getattr(address, 'numero', ''),
            'bairro': getattr(address, 'bairro', ''),
            'cidade': getattr(address, 'cidade', ''),
            'estado': getattr(address, 'estado', ''),
            'cep': getattr(address, 'cep', ''),
        }
    return {k: (v or '').strip() for k, v in data.items()}


def _address_to_string(address):
    data = _address_to_dict(address)
    parts = [
        data.get('rua'),
        data.get('numero'),
        data.get('bairro'),
        data.get('cidade'),
        data.get('estado'),
        data.get('cep'),
        'Brasil',
    ]
    return ', '.join(part for part in parts if part)


import unicodedata

def _normalize_token(value):
    if not value:
        return ''
    normalized = unicodedata.normalize('NFD', str(value).lower())
    normalized = ''.join(ch for ch in normalized if unicodedata.category(ch) != 'Mn')
    cleaned = re.sub(r'[^0-9a-z]+', '', normalized)
    return cleaned if cleaned else ''


_BRAZIL_STATE_ALIASES = {
    'ac': 'ac', 'acre': 'ac',
    'al': 'al', 'alagoas': 'al',
    'am': 'am', 'amazonas': 'am',
    'ap': 'ap', 'amapa': 'ap',
    'ba': 'ba', 'bahia': 'ba',
    'ce': 'ce', 'ceara': 'ce',
    'df': 'df', 'distritofederal': 'df',
    'es': 'es', 'espiritosanto': 'es',
    'go': 'go', 'goias': 'go',
    'ma': 'ma', 'maranhao': 'ma',
    'mg': 'mg', 'minasgerais': 'mg',
    'ms': 'ms', 'matogrossodosul': 'ms',
    'mt': 'mt', 'matogrosso': 'mt',
    'pa': 'pa', 'para': 'pa',
    'pb': 'pb', 'paraiba': 'pb',
    'pe': 'pe', 'pernambuco': 'pe',
    'pi': 'pi', 'piaui': 'pi',
    'pr': 'pr', 'parana': 'pr',
    'rj': 'rj', 'riodejaneiro': 'rj',
    'rn': 'rn', 'riograndedonorte': 'rn',
    'ro': 'ro', 'rondonia': 'ro',
    'rr': 'rr', 'roraima': 'rr',
    'rs': 'rs', 'riograndedosul': 'rs',
    'sc': 'sc', 'santacatarina': 'sc',
    'se': 'se', 'sergipe': 'se',
    'sp': 'sp', 'saopaulo': 'sp',
    'to': 'to', 'tocantins': 'to',
}


def _normalize_state(value):
    token = _normalize_token(value)
    return _BRAZIL_STATE_ALIASES.get(token, token)


def _raw_address_matches(raw, target):
    if not raw or not isinstance(raw, dict):
        return True

    city = _normalize_token(target.get('cidade'))
    state = _normalize_state(target.get('estado'))
    postcode = _normalize_token(target.get('cep'))

    raw_city = _normalize_token(raw.get('city') or raw.get('town') or raw.get('village') or raw.get('municipality'))
    raw_state = _normalize_state(raw.get('state'))
    raw_postcode = _normalize_token(raw.get('postcode'))

    if city and state:
        if raw_city != city or raw_state != state:
            return False

    if postcode and raw_postcode:
        if raw_postcode.startswith(postcode[:5]):
            return True
        if city and state and raw_city == city and raw_state == state:
            return True
        return False

    return True


def _build_geocode_queries(address):
    data = _address_to_dict(address)
    queries = []

    if isinstance(address, str):
        query = address.strip()
        if query:
            queries.append(query)
            if 'brasil' not in query.lower():
                queries.append(f'{query}, Brasil')

        cep_tokens = [token for token in re.split(r'[,;]', query) if '-' in token and token.strip().replace('-', '').isdigit()]
        if cep_tokens:
            queries.extend([f'{token.strip()}, Brasil' for token in cep_tokens])
        return [query for query in queries if query]

    full_address = _address_to_string(data)
    if full_address:
        queries.append(full_address)

    cep = data.get('cep')
    if cep:
        queries.append(f'{cep}, Brasil')

    rua = data.get('rua')
    numero = data.get('numero')
    bairro = data.get('bairro')
    cidade = data.get('cidade')
    estado = data.get('estado')

    if rua and numero and bairro and cidade and estado:
        queries.append(f'{rua}, {numero}, {bairro}, {cidade}, {estado}, Brasil')
    if bairro and cidade and estado:
        queries.append(f'{bairro}, {cidade}, {estado}, Brasil')
    if cidade and estado:
        queries.append(f'{cidade}, {estado}, Brasil')

    return [query for query in queries if query]


@lru_cache(maxsize=128)
def _geocode_address_cached(query_string, target_items):
    if not query_string:
        return None

    target_data = dict(target_items)
    geolocator = Nominatim(
        user_agent=getattr(settings, 'GEOPY_USER_AGENT', 'pizzaria_forchetta'),
        timeout=getattr(settings, 'GEOPY_GEOCODER_TIMEOUT', 10),
        scheme='https',
    )

    for query in _build_geocode_queries(query_string):
        try:
            locations = geolocator.geocode(query, exactly_one=False, limit=5, country_codes='br', addressdetails=True)
        except GeocoderServiceError:
            continue

        if not locations:
            continue
        if not isinstance(locations, list):
            locations = [locations]

        for location in locations:
            raw = location.raw.get('address', {})
            if _raw_address_matches(raw, target_data):
                return (location.latitude, location.longitude)

    return None


def _geocode_address(address_input):
    if isinstance(address_input, dict):
        target_data = _address_to_dict(address_input)
        query_string = _address_to_string(address_input)
    elif isinstance(address_input, str):
        target_data = _address_to_dict(address_input)
        query_string = address_input.strip()
    else:
        target_data = _address_to_dict(address_input)
        query_string = _address_to_string(address_input)

    target_items = tuple(sorted(target_data.items()))
    return _geocode_address_cached(query_string, target_items)


def _get_delivery_distance(customer_address, store_address=PIZZARIA_ADDRESS):
    store_coords = PIZZARIA_COORDS
    customer_coords = _geocode_address(customer_address)

    if store_coords is None or customer_coords is None:
        return None

    return geodesic(store_coords, customer_coords).km


def _calculate_delivery_fee_from_distance(distance_km):
    if distance_km is None:
        return None

    if distance_km <= 2:
        return Decimal('6.00')
    if distance_km <= 5:
        return Decimal('8.00')

    extra_km = ceil(distance_km) - 5
    fee = Decimal('8.00') + Decimal('1.50') * Decimal(extra_km)
    return fee.quantize(Decimal('0.01'))


def _get_borda_config():
    borda_options = [{
        'value': 'sem_borda',
        'label': 'Sem borda',
        'price': '0.00',
    }]

    borda_labels = {'sem_borda': 'Sem borda'}
    borda_prices = {'sem_borda': Decimal('0.00')}

    for borda_cfg in BordaPreco.objects.order_by('borda'):
        value = borda_cfg.borda
        label = borda_cfg.borda
        price = borda_cfg.preco or Decimal('0.00')
        borda_options.append({
            'value': value,
            'label': label,
            'price': f"{price:.2f}",
        })
        borda_labels[value] = label
        borda_prices[value] = price

    return borda_options, borda_labels, borda_prices


def _get_cart(request):
    if not hasattr(request, 'session'):
        return []

    cart = request.session.get('cart', [])
    _, borda_labels, _ = _get_borda_config()
    if isinstance(cart, dict):
        converted = []
        for pizza_id, quantity in cart.items():
            try:
                pizza = Pizza.objects.get(pk=int(pizza_id))
            except Pizza.DoesNotExist:
                continue
            converted.append({
                'type': 'single',
                'label': pizza.pizza,
                'borda': 'sem_borda',
                'borda_label': borda_labels.get('sem_borda', 'Sem borda'),
                'borda_price': 0,
                'pizza_ids': [pizza.id],
                'quantity': quantity,
                'price': float(pizza.vlvenda),
            })
        cart = converted
        request.session['cart'] = cart
    return cart


def _save_cart(request, cart):
    if hasattr(request, 'session'):
        request.session['cart'] = cart


def _add_item(cart, item):
    for existing in cart:
        if (
            existing['type'] == item['type']
            and existing['label'] == item['label']
            and existing.get('borda', 'sem_borda') == item.get('borda', 'sem_borda')
        ):
            existing['quantity'] += item['quantity']
            return
    cart.append(item)


def _get_cliente_for_user(user):
    if not user.is_authenticated:
        return None
    cliente = Cliente.objects.select_related('end_cliente').filter(usuario=user).first()
    if cliente is None:
        # create a Cliente record automatically for authenticated users without one
        nome = user.get_full_name() or (user.first_name or user.username)
        cliente = Cliente.objects.create(nome_cliente=nome, tel_clente='', usuario=user)
    return cliente


def _get_dados_entrega_initial(user, cliente=None):
    initial = {
        'email': user.email or '',
    }

    if not cliente:
        return initial

    initial.update({
        'nome_cliente': cliente.nome_cliente,
        'cpf': cliente.cpf or '',
        'tel_clente': cliente.tel_clente,
    })

    if cliente.end_cliente_id:
        endereco = cliente.end_cliente
        initial.update({
            'cep': endereco.cep or '',
            'rua': endereco.rua,
            'numero': endereco.numero or '',
            'complemento': getattr(endereco, 'complemento', '') or '',
            'bairro': endereco.bairro,
            'cidade': endereco.cidade,
            'estado': endereco.estado,
        })

    return initial


def _save_dados_entrega(user, form, cliente=None):
    if cliente and cliente.end_cliente_id:
        endereco = cliente.end_cliente
        endereco.cep = form.cleaned_data['cep']
        endereco.rua = form.cleaned_data['rua']
        endereco.numero = form.cleaned_data['numero']
        endereco.complemento = form.cleaned_data.get('complemento', '')
        endereco.bairro = form.cleaned_data['bairro']
        endereco.cidade = form.cleaned_data['cidade']
        endereco.estado = form.cleaned_data['estado']
        endereco.save()
    else:
        endereco = Endereco.objects.create(
            cep=form.cleaned_data['cep'],
            rua=form.cleaned_data['rua'],
            numero=form.cleaned_data['numero'],
            complemento=form.cleaned_data.get('complemento', ''),
            bairro=form.cleaned_data['bairro'],
            cidade=form.cleaned_data['cidade'],
            estado=form.cleaned_data['estado'],
        )

    if cliente:
        cliente.nome_cliente = form.cleaned_data['nome_cliente']
        cliente.cpf = form.cleaned_data['cpf']
        cliente.tel_clente = form.cleaned_data['tel_clente']
        cliente.end_cliente = endereco
        cliente.save()
    else:
        cliente = Cliente.objects.create(
            nome_cliente=form.cleaned_data['nome_cliente'],
            cpf=form.cleaned_data['cpf'],
            tel_clente=form.cleaned_data['tel_clente'],
            end_cliente=endereco,
            usuario=user,
        )

    user.email = form.cleaned_data['email']
    user.first_name = form.cleaned_data['nome_cliente']
    user.save(update_fields=['email', 'first_name'])

    return cliente


def buscar_sugestoes(request):
    query = (request.GET.get('q') or '').strip().lower()
    if not query:
        return JsonResponse([], safe=False)

    page_suggestions = [
        {'label': 'Início', 'url': reverse_lazy('inicio')},
        {'label': 'Sobre', 'url': reverse_lazy('sobre')},
        {'label': 'Contato', 'url': reverse_lazy('contato')},
        {'label': 'Carrinho', 'url': reverse_lazy('carrinho')},
        {'label': 'Cardápio', 'url': reverse_lazy('cardaprincipal')},
        {'label': 'Bebidas', 'url': reverse_lazy('bebidas')},
    ]

    suggestions = []
    for item in page_suggestions:
        label = item['label'].lower()
        if query in label or any(word.startswith(query) for word in label.split()):
            suggestions.append(item)

    pizzas = Pizza.objects.filter(Q(pizza__icontains=query) | Q(desc__icontains=query)).order_by('pizza')[:4]
    for pizza in pizzas:
        suggestions.append({'label': pizza.pizza, 'url': reverse_lazy('cardaprincipal')})

    bebidas = Produto.objects.filter(Q(nomeProd__icontains=query) | Q(descProd__icontains=query)).order_by('nomeProd')[:4]
    for bebida in bebidas:
        suggestions.append({'label': bebida.nomeProd, 'url': reverse_lazy('bebidas')})

    return JsonResponse(suggestions[:8], safe=False)


def buscar_produtos(request):
    query = (request.GET.get('q') or '').strip().lower()

    page_routes = {
        'inicio': 'inicio',
        'home': 'inicio',
        'principal': 'inicio',
        'pagina inicial': 'inicio',
        'página inicial': 'inicio',
        'sobre': 'sobre',
        'quem somos': 'sobre',
        'quem somos nós': 'sobre',
        'sobre nós': 'sobre',
        'contato': 'contato',
        'fale conosco': 'contato',
        'entre em contato': 'contato',
        'carrinho': 'carrinho',
        'pedido': 'carrinho',
        'meu pedido': 'carrinho',
        'cardapio': 'cardaprincipal',
        'cardápio': 'cardaprincipal',
        'menu': 'cardaprincipal',
        'cardapio principal': 'cardaprincipal',
        'pizzas': 'cardaprincipal',
        'pizza': 'cardaprincipal',
        'bebidas': 'bebidas',
        'bebida': 'bebidas',
        'refrigerante': 'bebidas',
        'suco': 'bebidas',
    }

    for keyword, route_name in page_routes.items():
        if keyword in query:
            return redirect(route_name)

    pizzas = Pizza.objects.none()
    bebidas = Produto.objects.none()

    if query:
        pizzas = Pizza.objects.filter(Q(pizza__icontains=query) | Q(desc__icontains=query)).order_by('pizza')
        bebidas = Produto.objects.filter(Q(nomeProd__icontains=query) | Q(descProd__icontains=query)).order_by('nomeProd')

    context = {
        'query': query,
        'pizzas': pizzas,
        'bebidas': bebidas,
        'cart_count': sum(item.get('quantity', 0) for item in _get_cart(request)),
    }
    return render(request, 'busca.html', context)


class IndexView(TemplateView):
    template_name = 'index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        promo_images = [
            'img/marguerita.jpg',
            'img/mussarela.jpg',
            'img/Pizza-4-queijos.jpg',
            'img/bacon.jpg',
            'img/milho.jpeg',
            'img/calabresa.jpeg',
        ]
        promotions = list(Pizza.objects.all().order_by('id')[:6])
        if promotions:
            for i, pizza in enumerate(promotions):
                setattr(pizza, 'image', promo_images[i % len(promo_images)])
        else:
            promotions = [
                {
                    'pizza': 'Margherita',
                    'desc': 'Molho de tomate, muçarela e manjericão fresco.',
                    'vlvenda': '28.90',
                    'image': 'img/1.png',
                },
                {
                    'pizza': 'Calabresa Especial',
                    'desc': 'Calabresa, cebola e azeitonas pretas.',
                    'vlvenda': '32.90',
                    'image': 'img/2.png',
                },
                {
                    'pizza': 'Portuguesa',
                    'desc': 'Presunto, ovos, cebola, ervilha e muçarela.',
                    'vlvenda': '34.90',
                    'image': 'img/imgpizza.jpg',
                },
                {
                    'pizza': 'Frango com Catupiry',
                    'desc': 'Frango desfiado, catupiry e milho.',
                    'vlvenda': '33.90',
                    'image': 'img/1.png',
                },
                {
                    'pizza': 'Quatro Queijos',
                    'desc': 'Muçarela, parmesão, gorgonzola e provolone.',
                    'vlvenda': '35.90',
                    'image': 'img/2.png',
                },
                {
                    'pizza': 'Pepperoni',
                    'desc': 'Pepperoni crocante com queijo derretido.',
                    'vlvenda': '36.90',
                    'image': 'img/imgpizza.jpg',
                },
            ]
        context['promotions'] = promotions
        return context


class SobreView(TemplateView):
    template_name = 'sobre.html'


class ContactForm(forms.Form):
    nome = forms.CharField(
        label='Nome',
        max_length=100,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Seu nome'}),
    )
    email = forms.EmailField(
        label='E-mail',
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'contato@pizzariapalestra.com'}),
    )
    telefone = forms.CharField(
        label='Telefone',
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '(19) 99112-3456'}),
    )
    mensagem = forms.CharField(
        label='Mensagem',
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 5, 'placeholder': 'Escreva sua mensagem aqui...'}),
    )


class ContatoView(FormView):
    template_name = 'contato.html'
    form_class = ContactForm
    success_url = reverse_lazy('contato')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['contact_sent'] = self.request.session.pop('contact_sent', False)
        context['contact_error'] = self.request.session.pop('contact_error', None)
        return context

    def form_valid(self, form):
        subject = f'Novo contato - {form.cleaned_data["nome"]}'
        message = (
            f"Nome: {form.cleaned_data['nome']}\n"
            f"E-mail: {form.cleaned_data['email']}\n"
            f"Telefone: {form.cleaned_data['telefone']}\n\n"
            f"Mensagem:\n{form.cleaned_data['mensagem']}"
        )
        recipient = [settings.DEFAULT_FROM_EMAIL]
        try:
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                recipient,
                fail_silently=False,
            )
            self.request.session['contact_sent'] = True
        except Exception as error:
            self.request.session['contact_error'] = str(error)
        return super().form_valid(form)


class ModeloView(TemplateView):
    template_name = 'modelo.html'


class CardapioPView(TemplateView):
    template_name = 'cardapio-principal.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        borda_options, _, _ = _get_borda_config()
        context['pizzas'] = Pizza.objects.all().order_by('id')[:50]
        context['cart_count'] = sum(item.get('quantity', 0) for item in _get_cart(self.request))
        context['half_pending'] = self.request.session.get('half_pending')
        context['half_message'] = self.request.session.pop('half_message', None)
        context['borda_options'] = borda_options
        return context


class BebidasView(TemplateView):
    template_name = 'bebidas.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['bebidas'] = Produto.objects.all().order_by('id')[:50]
        context['cart_count'] = sum(item.get('quantity', 0) for item in _get_cart(self.request))
        return context


class CarrinhoView(TemplateView):
    template_name = 'carrinho.html'

    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect(f"{reverse_lazy('login')}?next={reverse_lazy('carrinho')}")

        cliente = _get_cliente_for_user(request.user)
        form = DadosEntregaForm(request.POST, current_user=request.user)

        if form.is_valid():
            _save_dados_entrega(request.user, form, cliente)
            messages.success(request, 'Dados de entrega atualizados com sucesso.')
            return redirect('carrinho')

        context = self.get_context_data(delivery_form=form)
        return self.render_to_response(context)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        cart = _get_cart(self.request)
        total = Decimal('0.00')

        for item in cart:
            subtotal = Decimal(str(item.get('price', 0))) * item.get('quantity', 1)
            item['subtotal'] = subtotal
            total += subtotal

        cliente = _get_cliente_for_user(self.request.user)
        delivery_form = kwargs.get('delivery_form')
        if self.request.user.is_authenticated and delivery_form is None:
            initial = _get_dados_entrega_initial(self.request.user, cliente)
            delivery_form = DadosEntregaForm(initial=initial, current_user=self.request.user)

        context['items'] = cart
        context['total'] = total
        context['cart_count'] = sum(item.get('quantity', 0) for item in cart)
        context['cliente'] = cliente
        context['endereco_entrega'] = cliente.end_cliente if cliente else None
        context['delivery_form'] = delivery_form
        return context


class DadosEntregaForm(forms.Form):
    nome_cliente = forms.CharField(
        label='Nome completo',
        max_length=70,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
    )
    cpf = forms.CharField(
        label='CPF',
        max_length=14,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
    )
    tel_clente = forms.CharField(
        label='Telefone',
        max_length=15,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
    )
    email = forms.EmailField(
        label='E-mail',
        widget=forms.EmailInput(attrs={'class': 'form-control'}),
    )
    cep = forms.CharField(
        label='CEP',
        max_length=9,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
    )
    complemento = forms.CharField(
        label='Complemento',
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
    )
    rua = forms.CharField(
        label='Rua',
        max_length=100,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
    )
    numero = forms.CharField(
        label='Numero',
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
    )
    bairro = forms.CharField(
        label='Bairro',
        max_length=100,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
    )
    cidade = forms.CharField(
        label='Cidade',
        max_length=100,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
    )
    estado = forms.CharField(
        label='Estado',
        max_length=50,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
    )

    def __init__(self, *args, **kwargs):
        self.current_user = kwargs.pop('current_user', None)
        super().__init__(*args, **kwargs)

    def clean_cpf(self):
        cpf = ''.join(filter(str.isdigit, self.cleaned_data.get('cpf', '')))
        if len(cpf) != 11:
            raise forms.ValidationError('Informe um CPF com 11 digitos.')
        qs = Cliente.objects.filter(cpf=cpf)
        if self.current_user is not None:
            qs = qs.exclude(usuario=self.current_user)
        if qs.exists():
            raise forms.ValidationError('Este CPF ja esta em uso por outro cadastro.')
        return cpf

    def clean_tel_clente(self):
        telefone = ''.join(filter(str.isdigit, self.cleaned_data.get('tel_clente', '')))
        if len(telefone) not in (10, 11):
            raise forms.ValidationError('Informe um telefone valido com DDD.')
        return telefone


class PaymentForm(forms.Form):
    PAYMENT_CHOICES = [
        ('cartao', 'Cartão de crédito'),
        ('pix', 'Pix'),
        ('dinheiro', 'Dinheiro'),
    ]

    payment_method = forms.ChoiceField(
        label='Forma de pagamento',
        choices=PAYMENT_CHOICES,
        widget=forms.RadioSelect,
    )
    delivery_option = forms.ChoiceField(
        label='Tipo de pedido',
        choices=[('delivery', 'Entrega'), ('pickup', 'Retirada na pizzaria')],
        widget=forms.RadioSelect,
        required=False,
    )


class FormasPagamentoView(LoginRequiredMixin, FormView):
    template_name = 'formas-pagamento.html'
    form_class = PaymentForm
    success_url = reverse_lazy('confirmar-pedido')

    def _get_order_type(self, form=None):
        if form is not None and form.is_bound and form.is_valid():
            selected = form.cleaned_data.get('delivery_option')
            if selected:
                return selected

        if form is not None and form.data.get('delivery_option'):
            return form.data.get('delivery_option')

        return self.request.session.get('order_type', 'delivery')

    def _get_delivery_fee(self, user=None, cliente=None, order_type='delivery'):
        if order_type == 'pickup':
            return Decimal('0.00')

        if user is None:
            user = self.request.user

        if cliente is None and user is not None and user.is_authenticated:
            cliente = _get_cliente_for_user(user)

        if cliente is not None and cliente.end_cliente_id:
            distance_km = _get_delivery_distance(cliente.end_cliente)
            delivery_fee = _calculate_delivery_fee_from_distance(distance_km)
            if delivery_fee is not None:
                return delivery_fee

            taxa = (
                Taxa.objects.filter(edCliente=cliente)
                .order_by('-id')
                .first()
            )
            if taxa is not None:
                if taxa.valorTT is not None:
                    return Decimal(str(taxa.valorTT))
                if taxa.valorT is not None:
                    return Decimal(str(taxa.valorT))

        taxa_global = Taxa.objects.order_by('-id').first()
        if taxa_global is not None:
            if taxa_global.valorTT is not None:
                return Decimal(str(taxa_global.valorTT))
            if taxa_global.valorT is not None:
                return Decimal(str(taxa_global.valorT))

        return Decimal('0.00')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        cart = _get_cart(self.request)
        subtotal = Decimal('0.00')
        cliente = _get_cliente_for_user(self.request.user)

        for item in cart:
            item_subtotal = Decimal(str(item.get('price', 0))) * item.get('quantity', 1)
            item['subtotal'] = item_subtotal
            subtotal += item_subtotal

        order_type = self._get_order_type(context.get('form'))
        if not order_type:
            order_type = 'delivery'
        delivery_fee = self._get_delivery_fee(user=self.request.user, cliente=cliente, order_type=order_type)
        total = subtotal + (delivery_fee if order_type == 'delivery' else Decimal('0.00'))

        context['items'] = cart
        context['subtotal'] = subtotal
        context['delivery_fee'] = delivery_fee
        context['total'] = total
        context['order_type'] = order_type
        context['show_delivery_info'] = order_type == 'delivery'
        context['show_pickup_info'] = order_type == 'pickup'
        context['pickup_address'] = PIZZARIA_ADDRESS
        context['cart_count'] = sum(item.get('quantity', 0) for item in cart)
        context['cliente'] = cliente
        context['endereco_entrega'] = cliente.end_cliente if cliente else None
        context['can_finalize_checkout'] = bool(cliente and (order_type == 'pickup' or cliente.end_cliente_id))
        # include delivery form to allow inline correction of address on payment page
        delivery_form = kwargs.get('delivery_form')
        if self.request.user.is_authenticated and delivery_form is None:
            initial = _get_dados_entrega_initial(self.request.user, cliente)
            delivery_form = DadosEntregaForm(initial=initial, current_user=self.request.user)
        context['delivery_form'] = delivery_form
        return context

    def form_valid(self, form):
        cliente = _get_cliente_for_user(self.request.user)
        order_type = self._get_order_type(form)

        if order_type != 'pickup' and (not cliente or not cliente.end_cliente_id):
            messages.error(
                self.request,
                'Nao foi possivel finalizar: complete seu cadastro com endereco de entrega antes de continuar.',
            )
            return redirect('carrinho')

        cart = _get_cart(self.request)
        total = Decimal('0.00')
        order_lines = []
        order_snapshot = []

        for item in cart:
            subtotal = Decimal(str(item.get('price', 0))) * item.get('quantity', 1)
            total += subtotal
            line = f"{item['label']}"
            if item.get('borda_label'):
                line += f" (Borda: {item['borda_label']})"
            if item.get('type') == 'half':
                line += ' - Meio a meio'
            line += f" x{item.get('quantity', 1)} = R$ {Decimal(str(item['price'])):,.2f}"
            order_lines.append(line)
            order_snapshot.append({
                'label': item.get('label'),
                'borda_label': item.get('borda_label'),
                'price': f"{Decimal(str(item.get('price', 0))):.2f}",
                'quantity': item.get('quantity', 1),
                'subtotal': f"{subtotal:.2f}",
            })

        payment_map = {
            'cartao': 'Cartão de crédito',
            'pix': 'Pix',
            'dinheiro': 'Dinheiro',
        }
        payment_method = payment_map.get(form.cleaned_data['payment_method'], 'Não selecionado')
        delivery_fee = self._get_delivery_fee(user=self.request.user, cliente=cliente, order_type=order_type)
        endereco = cliente.end_cliente if cliente else None

        if order_type == 'pickup':
            delivery_label = 'Tipo de pedido: Retirada na pizzaria'
            delivery_address_lines = []
        else:
            delivery_label = 'Tipo de pedido: Entrega'
            complemento = f" - {endereco.complemento}" if endereco and endereco.complemento else ''
            delivery_address_lines = [
                'Endereço de entrega:',
                f"Rua: {endereco.rua if endereco else '-'}{endereco.numero or 's/n' if endereco else ''}{complemento}",
                f"Bairro: {endereco.bairro if endereco else '-'}",
                f"Cidade/UF: {endereco.cidade if endereco else '-'} / {endereco.estado if endereco else '-'}",
                f"CEP: {endereco.cep if endereco and endereco.cep else '-'}",
            ]

        loja_endereco = (
            f"Rua: {PIZZARIA_ADDRESS['rua']}, {PIZZARIA_ADDRESS['numero']} - {PIZZARIA_ADDRESS['bairro']}"
            f" - {PIZZARIA_ADDRESS['cidade']}/{PIZZARIA_ADDRESS['estado']}"
            f" - CEP: {PIZZARIA_ADDRESS['cep']}"
        )
        loja_cnpj = 'CNPJ: 66.955.849/0001-27'

        message = [
            'Pedido Pizzaria Forchetta D oro',
            '',
            'Dados da loja:',
            loja_endereco,
            loja_cnpj,
            '',
            'Itens do pedido:',
        ]
        message += [f"- {line}" for line in order_lines]
        message += [
            '',
            f'Subtotal: R$ {total:,.2f}',
        ]
        if order_type == 'delivery':
            message.append(f'Taxa de entrega: R$ {delivery_fee:,.2f}')
        total_with_fee = total + (delivery_fee if order_type == 'delivery' else Decimal('0.00'))
        message += [
            f'Total: R$ {total_with_fee:,.2f}',
            '',
            'Dados do cliente:',
            f'Nome: {cliente.nome_cliente}',
            f'CPF: {cliente.cpf or "-"}',
            f'Telefone: {cliente.tel_clente}',
            f'E-mail: {self.request.user.email or "-"}',
            '',
            delivery_label,
        ]
        message += delivery_address_lines
        message += [
            '',
            f'Forma de pagamento: {payment_method}',
        ]

        whatsapp_number = '5519992571719'
        whatsapp_url = _build_whatsapp_url(whatsapp_number, '\n'.join(message))
        self.request.session['order_snapshot'] = {
            'items': order_snapshot,
            'total': f"{total + (delivery_fee if order_type == 'delivery' else Decimal('0.00')):.2f}",
            'delivery_fee': f"{delivery_fee:.2f}",
            'payment_method': form.cleaned_data['payment_method'],
            'whatsapp_order_url': whatsapp_url,
        }
        self.request.session['cart'] = []
        self.request.session.pop('half_pending', None)
        self.request.session.pop('half_message', None)
        self.request.session['payment_method'] = form.cleaned_data['payment_method']
        self.request.session['order_type'] = order_type
        self.request.session['delivery_fee'] = f"{delivery_fee:.2f}"
        self.request.session['whatsapp_order_url'] = whatsapp_url
        self.request.session['cart'] = []
        self.request.session.pop('half_pending', None)
        self.request.session.pop('half_message', None)
        return redirect(self.get_success_url())


class ConfirmacaoPedidoView(LoginRequiredMixin, TemplateView):
    template_name = 'confirmacao-pedido.html'

    def dispatch(self, request, *args, **kwargs):
        if not request.session.get('order_snapshot'):
            return redirect('inicio')
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        order_snapshot = self.request.session.get('order_snapshot')
        cliente = _get_cliente_for_user(self.request.user)

        if order_snapshot:
            cart = order_snapshot.get('items', [])
            total = Decimal(order_snapshot.get('total', '0.00'))
            delivery_fee = Decimal(order_snapshot.get('delivery_fee', '0.00'))
            payment_method = order_snapshot.get('payment_method', '')
        else:
            cart = _get_cart(self.request)
            subtotal = Decimal('0.00')
            for item in cart:
                item_subtotal = Decimal(str(item.get('price', 0))) * item.get('quantity', 1)
                item['subtotal'] = item_subtotal
                subtotal += item_subtotal
            delivery_fee = Decimal(self.request.session.get('delivery_fee', '0.00'))
            total = subtotal + (delivery_fee if order_type == 'delivery' else Decimal('0.00'))
            payment_method = self.request.session.get('payment_method', '')

        order_type = self.request.session.get('order_type', 'delivery')

        payment_map = {
            'cartao': 'Cartão de crédito',
            'pix': 'Pix',
            'dinheiro': 'Dinheiro',
        }

        context['items'] = cart
        context['total'] = total
        context['delivery_fee'] = delivery_fee
        context['order_type'] = order_type
        context['show_delivery_info'] = order_type == 'delivery'
        context['show_pickup_info'] = order_type == 'pickup'
        context['pickup_address'] = PIZZARIA_ADDRESS
        context['payment_method'] = payment_map.get(payment_method, 'Não selecionado')
        context['payment_method_code'] = payment_method
        context['whatsapp_url'] = self.request.session.get('whatsapp_order_url', '')
        context['cart_count'] = sum(item.get('quantity', 0) for item in cart)
        context['cliente'] = cliente
        context['endereco_entrega'] = cliente.end_cliente if cliente else None

        return context


def add_to_cart(request, pizza_id):
    if request.method != 'POST':
        return redirect('cardaprincipal')

    pizza = get_object_or_404(Pizza, pk=pizza_id)
    _, borda_labels, borda_prices = _get_borda_config()
    choice = request.POST.get('sabor_type', 'unique')
    borda = request.POST.get('borda', 'sem_borda')
    if borda not in borda_labels:
        borda = 'sem_borda'
    borda_label = borda_labels[borda]
    borda_price = borda_prices.get(borda, Decimal('0.00'))

    cart = _get_cart(request)
    half_pending = request.session.get('half_pending')

    if half_pending and half_pending.get('pizza_id') != pizza.id:
        pending_base_price = Decimal(str(half_pending.get('base_price', half_pending.get('price', 0))))
        current_base_price = Decimal(str(pizza.vlvenda))
        pending_borda_price = Decimal(str(half_pending.get('borda_price', 0)))
        final_price = max(pending_base_price, current_base_price) + pending_borda_price
        final_borda = half_pending.get('borda', 'sem_borda')
        final_borda_label = half_pending.get('borda_label') or borda_labels.get(final_borda, borda_labels['sem_borda'])
        item = {
            'type': 'half',
            'label': f"Meio a meio: {half_pending['name']} / {pizza.pizza}",
            'borda': final_borda,
            'borda_label': final_borda_label,
            'borda_price': float(pending_borda_price),
            'pizza_ids': [half_pending['pizza_id'], pizza.id],
            'quantity': 1,
            'price': float(final_price),
        }
        _add_item(cart, item)
        _save_cart(request, cart)
        request.session.pop('half_pending', None)
        request.session['half_message'] = (
            f'Meio a meio adicionado ao carrinho: {item["label"]} com borda {final_borda_label} por R$ {item["price"]:.2f}.'
        )
        return redirect('carrinho')

    if choice == 'half':
        request.session['half_pending'] = {
            'pizza_id': pizza.id,
            'name': pizza.pizza,
            'base_price': float(pizza.vlvenda),
            'price': float(Decimal(str(pizza.vlvenda)) + borda_price),
            'borda': borda,
            'borda_label': borda_label,
            'borda_price': float(borda_price),
        }
        request.session['half_message'] = (
            f'Você escolheu meio a meio: {pizza.pizza} com borda {borda_label}. Adicional de borda: R$ {borda_price:.2f}. Escolha outra pizza para completar.'
        )
        return redirect('cardaprincipal')

    final_price = Decimal(str(pizza.vlvenda)) + borda_price
    item = {
        'type': 'single',
        'label': pizza.pizza,
        'borda': borda,
        'borda_label': borda_label,
        'borda_price': float(borda_price),
        'pizza_ids': [pizza.id],
        'quantity': 1,
        'price': float(final_price),
    }
    _add_item(cart, item)
    _save_cart(request, cart)
    request.session['half_message'] = (
        f'Pizza {pizza.pizza} com borda {borda_label} adicionada ao carrinho por R$ {final_price:.2f}.'
    )
    return redirect('cardaprincipal')


def salvar_endereco(request):
    if request.method != 'POST':
        return redirect('formas-pagamento')
    if not request.user.is_authenticated:
        return redirect(f"{reverse_lazy('login')}?next={reverse_lazy('formas-pagamento')}")

    form = DadosEntregaForm(request.POST, current_user=request.user)
    cliente = _get_cliente_for_user(request.user)
    if form.is_valid():
        _save_dados_entrega(request.user, form, cliente)
        messages.success(request, 'Endereço atualizado com sucesso.')
    else:
        messages.error(request, 'Corrija os erros do formulário de endereço.')
    return redirect('formas-pagamento')


def add_beverage_to_cart(request, produto_id):
    if request.method != 'POST':
        return redirect('bebidas')

    produto = get_object_or_404(Produto, pk=produto_id)
    cart = _get_cart(request)
    item = {
        'type': 'beverage',
        'label': produto.nomeProd,
        'product_ids': [produto.id],
        'quantity': 1,
        'price': float(produto.vlUnid),
    }
    _add_item(cart, item)
    _save_cart(request, cart)
    request.session['half_message'] = f'Bebida {produto.nomeProd} adicionada ao carrinho.'
    return redirect('carrinho')


def remove_from_cart(request, item_index):
    cart = _get_cart(request)
    try:
        index = int(item_index)
        if 0 <= index < len(cart):
            cart.pop(index)
    except (ValueError, TypeError):
        pass
    _save_cart(request, cart)
    return redirect('carrinho')


def clear_cart(request):
    request.session['cart'] = []
    request.session.pop('half_pending', None)
    request.session.pop('half_message', None)
    return redirect('carrinho')
