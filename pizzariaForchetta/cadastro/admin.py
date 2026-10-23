from django.contrib import admin

from .models import Cliente, Endereco, Funcionario, Taxa, Entregador, Pizza, Fornecedor, Produto, Cardapio
# Register your models here.
admin.site.register(Cliente)
admin.site.register(Endereco)
admin.site.register(Funcionario)
admin.site.register(Taxa)
admin.site.register(Entregador)
admin.site.register(Pizza)
admin.site.register(Fornecedor)
admin.site.register(Produto)
admin.site.register(Cardapio)

