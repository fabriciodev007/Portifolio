"""
URL configuration for Palestra project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.contrib.auth.views import LogoutView
from django.urls import path, include, reverse_lazy
from cadastro.views import ClientePasswordResetView, UserRegisterView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/register/', UserRegisterView.as_view(), name='register'),
    path('accounts/password_reset/', ClientePasswordResetView.as_view(), name='password_reset'),
    path('accounts/logout/', LogoutView.as_view(next_page=reverse_lazy('inicio')), name='logout'),
    path('accounts/', include('django.contrib.auth.urls')),
    path('', include('paginas.urls')),
    path('', include('cadastro.urls')),
]
