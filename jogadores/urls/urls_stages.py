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

app_name='stages'
urlpatterns = [
    path(r'listar/', views.listar_stages, name='listar_stages'),
    path(r'detalhar/<int:stage_id>/', views.detalhar_stage_id, name='detalhar_stage_por_id'),
    path(r'editar-stages-validas/', views.editar_stages_validas, name='editar_stages_validas'),
    path(r'listar-stages-validas/', views.listar_stages, {'apenas_validas_ladder': True}, name='listar_stages_validas'),
]
