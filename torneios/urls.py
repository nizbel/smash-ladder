"""
Configuração de URL para torneios
"""
from django.urls import path
from torneios import views

app_name='torneios'
urlpatterns = [
    # Torneios
    path(r'criar/', views.criar_torneio, name='criar_torneio'),
    path(r'detalhar/<int:torneio_id>/', views.detalhar_torneio, name='detalhar_torneio'),
    path(r'editar/<int:torneio_id>/', views.editar_torneio, name='editar_torneio'),
    path(r'listar/', views.listar_torneios, name='listar_torneios'),
    
    # Partidas
    path(r'detalhar/<int:torneio_id>/partida/<int:partida_id>/', views.detalhar_partida, name='detalhar_partida'),
    path(r'detalhar/<int:torneio_id>/partidas/', views.listar_partidas, name='listar_partidas'),
    
    # Jogadores
    path(r'detalhar/<int:torneio_id>/jogador/<int:jogador_id>/', views.detalhar_jogador, name='detalhar_jogador_torneio'),
    path(r'editar/<int:torneio_id>/jogador/<int:jogador_id>/', views.editar_jogador, name='editar_jogador_torneio'),
    path(r'detalhar/<int:torneio_id>/jogadores/', views.listar_jogadores, name='listar_jogadores_torneio'),
    
    # Análises
    path('analises/jogador/', views.analises_por_jogador, name='analises_torneio_por_jogador'),
    path('analises/jogador/resultado/', views.analise_resultado_torneio_para_um_jogador, name='analise_torneio_resultado_por_jogador'),
    path('analises/time/', views.analises_por_time, name='analises_torneio_por_time'),
    path('analises/time/resultado/', views.analise_resultado_torneio_para_um_time, name='analise_torneio_resultado_por_time'),
    
]
