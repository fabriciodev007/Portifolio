from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cadastro', '0011_cliente_cpf_cliente_usuario'),
    ]

    operations = [
        migrations.AddField(
            model_name='endereco',
            name='complemento',
            field=models.CharField(max_length=100, null=True, blank=True, verbose_name='Complemento'),
        ),
    ]
