from django.urls import path
from .views import CadastroCreate, LoginView

urlpatterns = [
    path('', CadastroCreate.as_view(), name='cadastro'),
    path('login/', LoginView.as_view(), name='login')
]
