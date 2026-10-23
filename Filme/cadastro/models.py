from django.db import models


# Create your models here.
class CadastroUser(models.Model):
    nome = models.CharField(max_length=100)
    username = models.CharField(max_length=50, verbose_name="Nome de Usuário")
    email = models.EmailField(verbose_name="e-mail", unique=True)
    password_hash = models.CharField(max_length=128, verbose_name="Senha")

    def __str__(self):
        return self.username
