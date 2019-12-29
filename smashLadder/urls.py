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
from django.contrib import admin
from django.urls import include, path
from django.urls.conf import re_path
from django.views.defaults import page_not_found

from ladder.models import Lockdown
from smashLadder import views, settings


urlpatterns = []

# Verificar lockdown de seasons
try:
    if Lockdown.sistema_em_lockdown():
        urlpatterns.append(re_path(r'.*?', page_not_found, {'exception': Exception('Gerando nova Season')}))
except:
    pass
        
urlpatterns.extend([
    path('admin/', admin.site.urls),
    path('contas/', include('django.contrib.auth.urls')),
    path('', views.home, name='inicio'),
    
    path('jogadores/', include('jogadores.urls.urls_jogadores')),
    path('ladder/', include('ladder.urls')),
    path('personagens/', include('jogadores.urls.urls_personagens')),
    path('stages/', include('jogadores.urls.urls_stages')),
    path('torneios/', include('torneios.urls')),
    path('treinamento/', include('treinamento.urls')),
])

if settings.DEBUG:
    import debug_toolbar
    urlpatterns.append(path('__debug__/', include(debug_toolbar.urls)))