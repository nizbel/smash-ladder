# -*- coding: utf-8 -*-
"""Views para torneios"""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.shortcuts import render, get_object_or_404

from torneios.forms import CriarTorneioForm
from torneios.models import Torneio, Partida, JogadorTorneio
from torneios.utils import buscar_torneio_challonge, gerar_torneio_challonge, \
    buscar_jogadores_challonge, gerar_jogadores_challonge, \
    buscar_partidas_challonge, gerar_partidas_challonge


@login_required
def criar_torneio(request):
    """Cria um torneio vinculado ao Challonge"""
    # Precisa ser admin para gerar um torneio
    if not request.user.jogador.admin:
        raise PermissionDenied
    
    if request.POST:
        form_criar_torneio = CriarTorneioForm(request.POST)
        
        if form_criar_torneio.is_valid():
            identificador_torneio = form_criar_torneio.cleaned_data['identificador_torneio']
            site = form_criar_torneio.cleaned_data['site']
            delimitador_time = form_criar_torneio.cleaned_data['delimitador_time']
            
            if site == Torneio.SITE_CHALLONGE_ID:
                # Criar um torneio vinculado ao Challonge
                try:
                    with transaction.atomic():
                        # Verificar se identificador é uma URL
                        if Torneio.SITE_CHALLONGE_URL in identificador_torneio:
                            identificador_torneio = identificador_torneio.split('/')[-1]
                        
                        # Buscar torneio
                        dados_torneio = buscar_torneio_challonge(identificador_torneio)
                        torneio = gerar_torneio_challonge(dados_torneio)
                        torneio.save()
                        
                        # Buscar jogadores
                        dados_jogadores = buscar_jogadores_challonge(identificador_torneio)
                        jogadores, times = gerar_jogadores_challonge(dados_jogadores, torneio, delimitador_time)
                        for time in times:
                            time.save()
                        for jogador in jogadores:
                            if jogador.time.id:
                                jogador.time_id = jogador.time.id
                            jogador.save()
                        
                        # Buscar partidas
                        dados_partidas = buscar_partidas_challonge(identificador_torneio)
                        partidas, rounds, vitorias_por_ausencia = gerar_partidas_challonge(dados_partidas, torneio)
                        for round_torneio in rounds:
                            round_torneio.save()
                        for partida in partidas:
                            partida.round_id = partida.round.id
                            partida.save()
                        for vitoria_por_ausencia in vitorias_por_ausencia:
                            vitoria_por_ausencia.partida_id = vitoria_por_ausencia.partida.id
                            vitoria_por_ausencia.save()
                        
                except Exception as e:
                    messages.error(request, str(e))
            else:
                raise ValueError(Torneio.MENSAGEM_ERRO_SITE_INVALIDO)
            
        else:
            for erro in form_criar_torneio.non_field_errors():
                messages.error(request, erro)
    
    else:
        form_criar_torneio = CriarTorneioForm()
    
    return render(request, 'torneios/criar_torneio.html', {'opcoes_site': Torneio.OPCOES_SITE, 'form_criar_torneio': form_criar_torneio})
    
def detalhar_torneio(request, torneio_id):
    """Detalha um torneio"""
    torneio = get_object_or_404(Torneio, id=torneio_id)
    
    dados_torneio = {}
    
    dados_torneio['top_3'] = JogadorTorneio.objects.filter(torneio=torneio, posicao_final__lte=3).order_by('posicao_final')
    
    return render(request, 'torneios/detalhar_torneio.html', {'torneio': torneio, 'dados_torneio': dados_torneio})

@login_required
def editar_torneio(request, torneio_id):
    """Edita um torneio"""
    # Precisa ser admin para gerar um torneio
    if not request.user.jogador.admin:
        raise PermissionDenied
    torneio = get_object_or_404(Torneio, id=torneio_id)
    
    dados_torneio = {}
    
    dados_torneio['top_3'] = JogadorTorneio.objects.filter(torneio=torneio, posicao_final__lte=3).order_by('posicao_final')
    
    return render(request, 'torneios/detalhar_torneio.html', {'torneio': torneio, 'dados_torneio': dados_torneio})

def listar_torneios(request):
    """Lista torneios cadastrados"""
    torneios = Torneio.objects.all()
    
    return render(request, 'torneios/listar_torneios.html', {'torneios': torneios})

def detalhar_partida(request, torneio_id, partida_id):
    """Detalha uma partida"""
    partida = get_object_or_404(Partida, id=partida_id)
    
    return render(request, 'torneios/detalhar_partida.html', {'partida': partida})

def listar_partidas(request, torneio_id):
    """Lista partidas cadastrados"""
    partidas = Partida.objects.filter(torneio__id=torneio_id)
    
    return render(request, 'partidas/listar_partidas.html', {'partidas': partidas})

def detalhar_jogador(request, torneio_id, jogador_id):
    """Detalha um jogador de um torneio"""
    jogador = get_object_or_404(JogadorTorneio, id=jogador_id)
    
    return render(request, 'torneios/listar_torneios.html', {'jogador': jogador})

@login_required
def editar_jogador(request, torneio_id, jogador_id):
    """Detalha um jogador de um torneio"""
    jogador = get_object_or_404(JogadorTorneio, id=jogador_id)
    
    return render(request, 'torneios/listar_torneios.html', {'jogador': jogador})

def listar_jogadores(request, torneio_id):
    """Lista partidas cadastrados"""
    jogadores = JogadorTorneio.objects.filter(torneio__id=torneio_id)
    
    return render(request, 'partidas/listar_partidas.html', {'jogadores': jogadores})