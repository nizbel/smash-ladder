# -*- coding: utf-8 -*-
"""Views para torneios"""
from django.shortcuts import render, get_object_or_404

from torneios.models import Torneio, Partida, JogadorTorneio
from django.contrib.auth.decorators import login_required


def detalhar_torneio(request, torneio_id):
    """Detalha um torneio"""
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