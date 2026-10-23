from decimal import Decimal

from django.conf import settings
from django.db import models



# Create your models here.

    
class Endereco(models.Model):
    rua = models.CharField(max_length=100, verbose_name="rua :")
    numero = models.CharField(max_length=20, verbose_name="Número", blank=True, null=True)
    complemento = models.CharField(max_length=100, verbose_name="Complemento", blank=True, null=True)
    cep = models.CharField(max_length=9, verbose_name="CEP", blank=True, null=True)
    bairro = models.CharField(max_length=100, verbose_name="Bairro")
    cidade = models.CharField(max_length=100, verbose_name="Cidade")
    estado = models.CharField(max_length=50, verbose_name="Estado")

    def __str__(self):
        numero = f", {self.numero}" if self.numero else ""
        return f"{self.rua}{numero} ({self.bairro})"
    

    
class Cliente(models.Model):
    nome_cliente = models.CharField(max_length=70, verbose_name="Nome Cliente")
    cpf = models.CharField(max_length=14, verbose_name="CPF", unique=True, blank=True, null=True)
    tel_clente = models.CharField(max_length=11,verbose_name="Telefone Cliente")
    usuario = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, blank=True, null=True, related_name='cliente', verbose_name='Usuario')
    end_cliente = models.OneToOneField(Endereco, on_delete=models.CASCADE, verbose_name="Endereço Cliente", null=True, blank=True)
    
    def __str__(self):
        return "{} ".format(self.nome_cliente)
    
    
class Funcionario(models.Model):
    nomeFunc = models.CharField(max_length=70, verbose_name="Nome Funcionario")
    cpf = models.CharField(max_length=14, verbose_name="CPF", unique=True, blank=True, null=True)
    telFunc = models.CharField(max_length=11, verbose_name="Telefone")
    endFunc = models.ForeignKey(Endereco, on_delete=models.CASCADE, verbose_name="Endereço Funcionário")
    usuario = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, blank=True, null=True, related_name='funcionario', verbose_name='Usuário')
    
    def __str__(self):
        return "{} - ({})".format(self.nomeFunc, self.telFunc)
    

class Taxa(models.Model):
    valorT = models.DecimalField(max_digits = 5,decimal_places=2)
    valorTT = models.DecimalField(max_digits = 5,decimal_places=2)
    edCliente = models.ForeignKey(Cliente, on_delete=models.PROTECT, verbose_name="Cliente")
    
    def __str__(self):
        return "{} - ({})".format(self.edCliente, self.valorTT)
    
class Entregador(models.Model):
    nomeEntreg = models.CharField(max_length=70, verbose_name="Nome Entregador")
    telEntreg = models.CharField(max_length=11, verbose_name="Telefone")
    endEntreg = models.ForeignKey(Endereco, on_delete=models.CASCADE, verbose_name="Endereço Entregador" )
    
    def __str__(self):
        return "{} - ({})".format(self.nomeEntreg, self.telEntreg)

class Pizza(models.Model):
    pizza = models.CharField(max_length=70,)
    desc = models.CharField(max_length=225, verbose_name="Descrição")
    vlbruto = models.DecimalField(max_digits = 6,decimal_places=2)
    vlvenda = models.DecimalField(max_digits = 6,decimal_places=2)
    vlr12pdc = models.DecimalField(max_digits = 6,decimal_places=2)
    
    def __str__(self):
        return "{} - ({})".format(self.pizza, self.vlvenda)
    
class Fornecedor(models.Model):
    nomeFornec = models.CharField(max_length=70, verbose_name="Nome Fornecedor")
    telFornec = models.CharField(max_length=11, verbose_name="Telefone")
    cnpj= models.CharField(max_length=18, verbose_name="CNPJ", unique=True)
    endFornec = models.ForeignKey(Endereco, on_delete=models.CASCADE, verbose_name="Endereço Fornecedor" )
    
    def __str__(self):
        return "{} - ( {} )".format(self.nomeFornec, self.cnpj)
    
    
class Produto(models.Model):
    nomeProd = models.CharField(max_length=70, verbose_name="Produto")
    descProd = models.CharField(max_length=225, verbose_name="Descrição")
    dataval = models.DateField(verbose_name= "Data validade")
    dataCompra = models.DateField(verbose_name= "Data Compra")
    vlUnid = models.DecimalField(max_digits = 6,decimal_places=2)
    vlT = models.DecimalField(max_digits = 6,decimal_places=2)
    
    fornec = models.ForeignKey(Fornecedor, on_delete=models.CASCADE,verbose_name="Fornecedor" )
    
    def __str__(self):
        return "{} - ( {} )".format(self.nomeProd, self.descProd)
    
class BordaPreco(models.Model):
    borda = models.CharField(max_length=50, unique=True, verbose_name='Borda')
    preco = models.DecimalField(max_digits=6, decimal_places=2, default=0, verbose_name='Preco da Borda')

    def __str__(self):
        return f"{self.borda} - R$ {self.preco}"


class Cardapio(models.Model):
    prod = models.ForeignKey(Produto, on_delete=models.CASCADE, verbose_name="Produto")
    pizz = models.ForeignKey(Pizza, on_delete=models.CASCADE, verbose_name="pizza")
    preco = models.DecimalField(max_digits=6, decimal_places=2, default=0, verbose_name='Preco')

    def save(self, *args, **kwargs):
        base_price = self.pizz.vlvenda if self.pizz_id else Decimal('0.00')
        self.preco = base_price
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.pizz} - R$ {self.preco}"
    