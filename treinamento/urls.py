"""
Configuração de URL para treinamento
"""
from django.urls import path

from treinamento import views


app_name='treinamento'
urlpatterns = [
    path(r'', views.painel_treinamento, name='painel_treinamento'),
    
    # Registros de treinamento
    path(r'registro/<int:registro_id>/adicionar-resultado/', views.add_resultado_treinamento, name='add_resultado_treinamento'),
    path(r'registro/<int:registro_id>/apagar/', views.apagar_registro_treinamento, name='apagar_registro_treinamento'),
    path(r'registro/<int:registro_id>/detalhar/', views.detalhar_registro_treinamento, name='detalhar_registro_treinamento'),
    path(r'registro/<int:registro_id>/editar/', views.editar_registro_treinamento, name='editar_registro_treinamento'),
    path(r'registro/adicionar/', views.add_registro_treinamento, name='add_registro_treinamento'),
    path(r'registro/listar/', views.listar_registros_treinamento, name='listar_registros_treinamento'),
    
    # Anotações
    path(r'anotacao/adicionar/', views.add_anotacao, name='add_anotacao'),
    path(r'anotacao/<int:anotacao_id>/apagar/', views.apagar_anotacao, name='apagar_anotacao'),
    path(r'anotacao/listar/', views.listar_anotacoes, name='listar_anotacoes'),
    
    # Métricas
    path(r'metrica/adicionar/', views.add_metrica, name='add_metrica'),
    path(r'metrica/<int:metrica_id>/apagar/', views.apagar_metrica, name='apagar_metrica'),
    path(r'metrica/<int:metrica_id>/detalhar/', views.detalhar_metrica, name='detalhar_metrica'),
    path(r'metrica/<int:metrica_id>/editar/', views.editar_metrica, name='editar_metrica'),
    path(r'metrica/listar/', views.listar_metricas, name='listar_metricas'),
    
]
