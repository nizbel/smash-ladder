"""smashLadder URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.2/topics/http/urls/
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

from django.urls import path
from jogadores import views

app_name='jogadores'
urlpatterns = [
    path(r'detalhar/<slug:username>/', views.detalhar_jogador, name='detalhar_jogador'),
    path(r'editar/<slug:username>/', views.editar_jogador, name='editar_jogador'),
    path(r'listar/', views.listar_jogadores, name='listar_jogadores'),
    path(r'listar-desafios/<slug:username>/', views.listar_desafios_jogador, name='listar_desafios_jogador'),
]
