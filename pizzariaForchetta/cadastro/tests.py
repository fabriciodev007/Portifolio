from django.contrib.auth import get_user_model
from django.test import TestCase

from .forms import BordaPrecoForm, CardapioForm, ClienteRegisterForm, FuncionarioForm
from .models import BordaPreco


class ClienteRegisterFormTests(TestCase):
    def test_duplicate_username_with_different_casing_is_rejected(self):
        get_user_model().objects.create_user(
            username='admin',
            email='admin@example.com',
            password='senha1234',
        )

        form = ClienteRegisterForm(data={
            'username': 'ADMIN',
            'email': 'novo@example.com',
            'password1': 'senha1234',
            'password2': 'senha1234',
            'nome_cliente': 'Novo Cliente',
            'cpf': '12345678909',
            'tel_clente': '11999999999',
            'cep': '01000-000',
            'rua': 'Rua Teste',
            'numero': '123',
            'bairro': 'Centro',
            'cidade': 'São Paulo',
            'estado': 'SP',
        })

        self.assertFalse(form.is_valid())
        self.assertIn('username', form.errors)

    def test_duplicate_username_for_employee_is_rejected(self):
        get_user_model().objects.create_user(
            username='funcionario',
            email='funcionario@example.com',
            password='senha1234',
        )

        form = FuncionarioForm(data={
            'nomeFunc': 'Funcionário Teste',
            'cpf': '12345678909',
            'telFunc': '11999999999',
            'endFunc': '',
            'username': 'FUNCIONARIO',
            'email': 'outro@example.com',
            'password1': 'senha1234',
            'password2': 'senha1234',
        })

        self.assertFalse(form.is_valid())
        self.assertIn('username', form.errors)

    def test_borda_preco_form_allows_new_border_type(self):
        form = BordaPrecoForm(data={'borda': 'Cebola caramelizada', 'preco': '2.50'})

        self.assertTrue(form.is_valid(), form.errors)
        instance = form.save()
        self.assertEqual(instance.borda, 'Cebola caramelizada')
        self.assertEqual(instance.preco, 2.50)

    def test_cardapio_form_does_not_expose_borda_fields(self):
        form = CardapioForm()

        self.assertNotIn('borda', form.fields)
        self.assertNotIn('preco_borda', form.fields)
