from django.core.management.base import BaseCommand

from cadastro.models import Pizza


class Command(BaseCommand):
    help = 'Popula o banco com 50 pizzas de exemplo para o cardápio.'

    def handle(self, *args, **options):
        if Pizza.objects.count() >= 50:
            self.stdout.write(self.style.WARNING('Já existem 50 ou mais pizzas cadastradas.'))
            return

        sabores = [
            'Margherita', 'Pepperoni', 'Quatro Queijos', 'Calabresa', 'Frango com Catupiry',
            'Portuguesa', 'Napolitana', 'Vegetariana', 'Moda da Casa', 'Bacon',
            'Frango BBQ', 'Palmito', 'Atum', 'Marguerita Especial', 'Rúcula com Parma',
            'Chocolate', 'Romeu e Julieta', 'Strogonoff', 'Camarão', 'Alho e Óleo',
            'Escarola', 'Milho', 'Búfala', 'Champignon', 'Italiana',
            'Havaiana', 'Veneziana', 'Mexicana', 'Catupiry', 'Cheddar',
            'Carne Seca', 'Brócolis', 'Curry', 'Aliche', 'Muzarela',
            'Pesto', 'Parmegiana', 'Filé Mignon', 'Cupim', 'Picanha',
            'Abobrinha', 'Berinjela', 'Cordeiro', 'Barbecue', 'Oito Queijos',
            'Salame', 'Ricota', 'Molho Branco', 'Trufada', 'Champanhe',
        ]

        pizzas = []
        base_price = 25.00
        for index, sabor in enumerate(sabores[:50], start=1):
            pizzas.append(Pizza(
                pizza=sabor,
                desc=f'Pizza sabor {sabor} com ingredientes selecionados e massa crocante.',
                vlbruto=base_price + index * 0.50,
                vlvenda=base_price + index * 0.90,
                vlr12pdc=base_price + index * 1.20,
            ))

        Pizza.objects.bulk_create(pizzas)
        self.stdout.write(self.style.SUCCESS('50 pizzas cadastradas com sucesso.'))
