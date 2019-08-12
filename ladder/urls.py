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

from ladder import views

app_name='ladder'
urlpatterns = [
    # Ladder
    path(r'atual/', views.detalhar_ladder_atual, name='detalhar_ladder_atual'),
    path(r'historico/<int:ano>/<int:mes>/', views.detalhar_ladder_historico, name='detalhar_ladder_historico'),
    path(r'historico/listar/', views.listar_ladder_historico, name='listar_ladder_historico'),
    path(r'atual/listar-desafios/', views.listar_desafios_ladder, name='listar_desafios_ladder_atual'),
    path(r'historico/<int:ano>/<int:mes>/listar-desafios/', views.listar_desafios_ladder, name='listar_desafios_ladder_historico'),
    path(r'remover-jogador/', views.remover_jogador_ladder, name='remover_jogador_ladder'),
    path(r'permissao-aumento-range/adicionar/', views.add_permissao_aumento_range, name='add_permissao_aumento_range'),
    
    # Desafios de ladder
    path(r'desafio/adicionar/', views.add_desafio_ladder, name='adicionar_desafio_ladder'),
    path(r'desafio/cancelar/<int:desafio_id>/', views.cancelar_desafio_ladder, name='cancelar_desafio_ladder'),
    path(r'desafio/detalhar/<int:desafio_id>/', views.detalhar_desafio_ladder, name='detalhar_desafio_ladder'),
    path(r'desafio/editar/<int:desafio_id>/', views.editar_desafio_ladder, name='editar_desafio_ladder'),
    path(r'desafio/listar-pendentes/', views.listar_desafios_ladder_pendentes_validacao, name='listar_desafios_ladder_pendentes_validacao'),
    path(r'desafio/validar/<int:desafio_id>/', views.validar_desafio_ladder, name='validar_desafio_ladder'),
    
    # Regras
    path(r'regras/', views.detalhar_regras, name='detalhar_regras_ladder'),
    
    # Lutas
    path(r'lutas/detalhar/<int:luta_id>/', views.detalhar_luta, name='detalhar_luta'),
]
