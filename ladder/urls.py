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
    path(r'atual/listar-registros/', views.listar_registros_ladder, name='listar_registros_ladder_atual'),
    path(r'historico/<int:ano>/<int:mes>/listar-registros/', views.listar_registros_ladder, name='listar_registros_ladder_historico'),
    
    # Registros de ladder
    path(r'registro/adicionar/', views.add_registro_ladder, name='adicionar_registro_ladder'),
    path(r'registro/cancelar/<int:registro_id>/', views.cancelar_registro_ladder, name='cancelar_registro_ladder'),
    path(r'registro/detalhar/<int:registro_id>/', views.detalhar_registro_ladder, name='detalhar_registro_ladder'),
    path(r'registro/editar/<int:registro_id>/', views.editar_registro_ladder, name='editar_registro_ladder'),
    path(r'registro/listar-pendentes/', views.listar_registros_ladder_pendentes_validacao, name='listar_registros_ladder_pendentes_validacao'),
    path(r'registro/validar/<int:registro_id>/', views.validar_registro_ladder, name='validar_registro_ladder'),
    
    # Regras
    path(r'regras/', views.detalhar_regras, name='detalhar_regras_ladder'),
    
    # Lutas
    path(r'lutas/detalhar/<int:luta_id>/', views.detalhar_luta, name='detalhar_luta'),
]
