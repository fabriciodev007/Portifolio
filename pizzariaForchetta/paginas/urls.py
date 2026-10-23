from django.urls import path
from .views import (
    ContatoView,
    IndexView,
    SobreView,
    ModeloView,
    CardapioPView,
    BebidasView,
    CarrinhoView,
    FormasPagamentoView,
    salvar_endereco,
    ConfirmacaoPedidoView,
    add_to_cart,
    add_beverage_to_cart,
    remove_from_cart,
    clear_cart,
    buscar_produtos,
    buscar_sugestoes,
)

urlpatterns = [
    path('', IndexView.as_view(), name='inicio'),
    path('sobre/', SobreView.as_view(), name='sobre'),
    path('contato/', ContatoView.as_view(), name='contato'),
    path('modelo/', ModeloView.as_view(), name='modelo'),
    path('cardapio/', CardapioPView.as_view(), name='cardaprincipal'),
    path('cardapio/adicionar/<int:pizza_id>/', add_to_cart, name='add-to-cart'),
    path('bebidas/', BebidasView.as_view(), name='bebidas'),
    path('bebidas/adicionar/<int:produto_id>/', add_beverage_to_cart, name='add-beverage-to-cart'),
    path('carrinho/', CarrinhoView.as_view(), name='carrinho'),
    path('carrinho/checkout/', FormasPagamentoView.as_view(), name='formas-pagamento'),
    path('carrinho/salvar-endereco/', salvar_endereco, name='salvar-endereco'),
    path('carrinho/confirmacao/', ConfirmacaoPedidoView.as_view(), name='confirmar-pedido'),
    path('carrinho/remover/<int:item_index>/', remove_from_cart, name='remover-do-carrinho'),
    path('carrinho/limpar/', clear_cart, name='limpar-carrinho'),
    path('buscar/', buscar_produtos, name='buscar'),
    path('buscar/sugestoes/', buscar_sugestoes, name='buscar-sugestoes'),
]

