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
from torneios import views

app_name='torneios'
urlpatterns = [
    path(r'detalhar/<int:torneio_id>/', views.detalhar_torneio, name='detalhar_torneio'),
    path(r'listar/', views.listar_torneios, name='listar_torneios'),
    
    path(r'detalhar/<int:torneio_id>/partida/<int:partida_id>/', views.detalhar_partida, name='detalhar_partida'),
    path(r'detalhar/<int:torneio_id>/partidas/', views.listar_partidas, name='listar_partidas'),
    
    path(r'detalhar/<int:torneio_id>/jogador/<int:jogador_id>/', views.detalhar_jogador, name='detalhar_jogador_torneio'),
    path(r'detalhar/<int:torneio_id>/jogador/<int:jogador_id>/editar', views.editar_jogador, name='editar_jogador_torneio'),
    path(r'detalhar/<int:torneio_id>/jogadores/', views.listar_jogadores, name='listar_jogadores_torneio'),
    
]
