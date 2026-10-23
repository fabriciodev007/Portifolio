from decimal import Decimal

from django.contrib.auth import get_user_model
from django.contrib.sessions.middleware import SessionMiddleware
from django.test import RequestFactory, TestCase

from cadastro.models import Cliente, Endereco, Fornecedor, Pizza, Produto, Taxa
from paginas.views import FormasPagamentoView, _build_whatsapp_url, _raw_address_matches, buscar_produtos, buscar_sugestoes


class SearchViewTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def test_search_redirects_to_internal_page_when_query_matches(self):
        request = self.factory.get('/buscar/', {'q': 'contato'})
        response = buscar_produtos(request)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/contato/')

    def test_search_returns_matching_pizzas_and_products(self):
        endereco = Endereco.objects.create(
            rua='Rua das Pizzas',
            numero='123',
            bairro='Centro',
            cidade='São Paulo',
            estado='SP',
            cep='01000-000',
        )
        fornecedor = Fornecedor.objects.create(
            nomeFornec='Fornecedor Teste',
            telFornec='11999999999',
            cnpj='12.345.678/0001-90',
            endFornec=endereco,
        )
        Pizza.objects.create(
            pizza='Calabresa',
            desc='Sabor calabresa',
            vlbruto=Decimal('20.00'),
            vlvenda=Decimal('30.00'),
            vlr12pdc=Decimal('40.00'),
        )
        Produto.objects.create(
            nomeProd='Refrigerante Cola',
            descProd='Bebida gelada',
            dataval='2030-01-01',
            dataCompra='2025-01-01',
            vlUnid=Decimal('5.00'),
            vlT=Decimal('5.00'),
            fornec=fornecedor,
        )

        request = self.factory.get('/buscar/', {'q': 'calab'})
        response = buscar_produtos(request)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Calabresa')
        self.assertContains(response, 'Resultados para "calab"')

    def test_autocomplete_returns_suggestions_for_pages_and_items(self):
        request = self.factory.get('/buscar/sugestoes/', {'q': 'cont'})
        response = buscar_sugestoes(request)
        payload = response.content.decode('utf-8')

        self.assertEqual(response.status_code, 200)
        self.assertIn('Contato', payload)


class FormasPagamentoViewTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.user = get_user_model().objects.create_user(
            username='cliente',
            email='cliente@example.com',
            password='12345',
        )

    def _make_request(self):
        request = self.factory.get('/carrinho/checkout/')
        request.user = self.user
        middleware = SessionMiddleware(lambda req: None)
        middleware.process_request(request)
        request.session.save()
        return request

    def test_delivery_fee_is_added_to_total(self):
        cliente = Cliente.objects.create(
            nome_cliente='Cliente Teste',
            cpf='12345678909',
            tel_clente='11999999999',
        )
        Taxa.objects.create(valorT=Decimal('3.50'), valorTT=Decimal('3.50'), edCliente=cliente)

        request = self._make_request()
        request.session['cart'] = [
            {
                'label': 'Pizza Média',
                'type': 'single',
                'quantity': 1,
                'price': '20.00',
            }
        ]
        request.session.save()

        view = FormasPagamentoView()
        view.setup(request)
        context = view.get_context_data()

        self.assertEqual(context['subtotal'], Decimal('20.00'))
        self.assertEqual(context['delivery_fee'], Decimal('3.50'))
        self.assertEqual(context['total'], Decimal('23.50'))

    def test_pickup_uses_zero_delivery_fee(self):
        request = self._make_request()
        request.session['cart'] = [
            {
                'label': 'Pizza Média',
                'type': 'single',
                'quantity': 1,
                'price': '20.00',
            }
        ]
        request.session['order_type'] = 'pickup'
        request.session.save()

        view = FormasPagamentoView()
        view.setup(request)
        context = view.get_context_data()

        self.assertEqual(context['order_type'], 'pickup')
        self.assertEqual(context['delivery_fee'], Decimal('0.00'))
        self.assertEqual(context['total'], Decimal('20.00'))

    def test_build_whatsapp_url_uses_click_to_chat_endpoint(self):
        message = 'Pedido Pizzaria Palestra\n\nItens:\n- Pizza Média'
        url = _build_whatsapp_url('5519992571719', message)

        self.assertTrue(url.startswith('https://wa.me/5519992571719?text='))
        self.assertIn('Pedido%20Pizzaria%20Palestra', url)

    def test_raw_address_matches_allows_same_city_state_with_different_cep(self):
        target = {
            'cidade': 'Hortolândia',
            'estado': 'SP',
            'cep': '13188-160',
        }
        raw = {
            'city': 'Hortolândia',
            'state': 'São Paulo',
            'postcode': '13183-080',
        }

        self.assertTrue(_raw_address_matches(raw, target))
