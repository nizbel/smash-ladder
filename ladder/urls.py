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
    
    # Remoções
    path(r'cancelar-remocao/<int:remocao_id>/', views.cancelar_remocao_jogador_ladder, name='cancelar_remocao_jogador_ladder'),
    path(r'listar-remocoes/', views.listar_remocoes_jogador_ladder, name='listar_remocoes_jogador_ladder'),
    path(r'remover-jogador/', views.remover_jogador_ladder, name='remover_jogador_ladder'),
    
    # Permissões de aumento de range
    path(r'permissao-aumento-range/adicionar/', views.add_permissao_aumento_range, name='add_permissao_aumento_range'),
    path(r'permissao-aumento-range/remover/', views.remover_permissao_aumento_range, name='remover_permissao_aumento_range'),
    path(r'permissao-aumento-range/remover/<int:permissao_id>/', views.remover_permissao_aumento_range, name='remover_permissao_aumento_range'),
    
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
    
    # Análises
    path('analises/geral/', views.analises, name='analises'),
    path('analises/geral/resultado-acumulado-jogadores/', views.analise_resultado_acumulado_jogadores, name='analise_result_acum_jogadores'),
    path('analises/geral/resultado-posicao/', views.analise_resultado_por_posicao, name='analise_resultado_por_posicao'),
    path('analises/geral/resultado-diferenca-posicao/', views.analise_resultado_por_diferenca_posicao, name='analise_resultado_por_diferenca_posicao'),
    path('analises/geral/vitorias-por-personagem/', views.analise_vitorias_por_personagem, name='analise_vitorias_por_personagem'),
    path('analises/jogador/', views.analises_por_jogador, name='analises_por_jogador'),
    path('analises/jogador/resultado-acumulado-jogador/', views.analise_resultado_acumulado_para_um_jogador, name='analise_result_acum_jogador'),
    path('analises/jogador/resultado-contra-personagens-jogador/', views.analise_resultado_acumulado_contra_personagens_para_um_jogador, 
         name='analise_result_jogador_contra_personagens'),
    path('analises/jogador/resultado-stages-jogador/', views.analise_resultado_stages_para_um_jogador, name='analise_stages_jogador'),
    path('analises/jogador/vitorias-desafio/', views.analise_vitorias_desafio_para_um_jogador, name='analise_vitorias_desafio_jogador'),
]
