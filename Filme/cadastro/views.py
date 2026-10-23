from django.views.generic.edit import CreateView
from .models import CadastroUser
from django.urls import reverse_lazy


class CadastroCreate(CreateView):
    model = CadastroUser
    fields = ['nome', 'username', 'email', 'password_hash']
    template_name = 'cadastro/form.html'
    success_url = reverse_lazy('login')

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        for field in form.fields.values():
            field.widget.attrs['class'] = 'form-control'
        return form

class LoginView(CreateView):
    model = CadastroUser
    fields = ['username', 'password_hash']
    template_name = 'cadastro/login.html'
    success_url = reverse_lazy('inicio')

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        for field in form.fields.values():
            field.widget.attrs['class'] = 'form-control'
        return form