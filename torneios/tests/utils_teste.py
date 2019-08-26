# -*- coding: utf-8 -*-
from django.db.models.aggregates import Max
from django.utils import timezone

from jogadores.models import Jogador
from torneios.models import Torneio, JogadorTorneio, Time, Round, Partida


JOGADORES_TORNEIO_TESTE = [
    {'nome': 'WindWalker', 'posicao_final': 4, 'id_challonge': 1},
    {'nome': 'Yalda', 'posicao_final': 1, 'id_challonge': 2},
    {'nome': 'Tsun', 'posicao_final': 9, 'id_challonge': 3},
    {'nome': 'Monkey', 'posicao_final': 13, 'id_challonge': 4},
    {'nome': 'Aceblind', 'time': 'CdL', 'posicao_final': 2, 'id_challonge': 5},
    {'nome': 'bløwer', 'posicao_final': 3, 'id_challonge': 6},
    {'nome': 'aju', 'time': 'Hitbox','posicao_final': 13, 'id_challonge': 7},
    {'nome': 'Stefan', 'time': 'Grk', 'posicao_final': 7, 'id_challonge': 8},
    {'nome': 'Mad', 'posicao_final': 13, 'id_challonge': 9},
    {'nome': 'LePabs', 'posicao_final': 13, 'id_challonge': 10},
    {'nome': 'Haze', 'posicao_final': 13, 'id_challonge': 11},
    {'nome': 'LuLoko', 'posicao_final': 13, 'id_challonge': 12},
    {'nome': 'Teets', 'time': 'CdL', 'posicao_final': 13, 'id_challonge': 13},
    {'nome': 'Blue9002', 'posicao_final': 13, 'id_challonge': 14},
    {'nome': 'TXR', 'time': 'CdL', 'posicao_final': 13, 'id_challonge': 15},
    {'nome': 'Gatho', 'posicao_final':13 , 'id_challonge': 16},
    {'nome': 'Midorima', 'posicao_final': 13, 'id_challonge': 17},
    {'nome': 'Bacabau', 'posicao_final': 13, 'id_challonge': 18},
    {'nome': 'CDX', 'posicao_final': 13, 'id_challonge': 19},
    {'nome': 'Tiovski', 'time': 'CdL', 'posicao_final': 13, 'id_challonge': 20},
    {'nome': 'Niz', 'posicao_final': 13, 'id_challonge': 21},
    {'nome': 'Miźenkai', 'posicao_final': 13, 'id_challonge': 22},
    {'nome': 'Barba', 'time': 'CdL', 'posicao_final': 13, 'id_challonge': 23},
    {'nome': 'Sena', 'posicao_final': 7, 'id_challonge': 24},
    {'nome': 'Phils', 'posicao_final': 13, 'id_challonge': 25},
    {'nome': 'Mat?', 'posicao_final': 7, 'id_challonge': 26},
    {'nome': 'Zeta', 'posicao_final': 13, 'id_challonge': 27},
    {'nome': 'Tio da Samus', 'posicao_final': 13, 'id_challonge': 28},
    {'nome': 'Onmalamo', 'posicao_final': 13, 'id_challonge': 29},
    {'nome': 'Szayoi', 'posicao_final': 13, 'id_challonge': 30},
    {'nome': 'Bye1', 'posicao_final': 13, 'id_challonge': 31},
    {'nome': 'Dankid', 'posicao_final': 13, 'id_challonge': 32}
    ]

def criar_torneio_teste(nome='Torneio 1', data=None):
    """Gera um torneio para teste"""
    if data == None:
        data = timezone.localtime()
        
    torneio = Torneio.objects.create(nome=nome, data=data, adicionado_por=Jogador.objects.filter(admin=True)[0], 
                                     id_challonge=(Torneio.objects.aggregate(max_id=Max('id_challonge'))['max_id'] or 1),
                                     url='teste')
    return torneio

def criar_jogadores_torneio_teste(torneio):
    """Gera jogadores em um torneio para teste"""
    for jogador in JOGADORES_TORNEIO_TESTE:
        jogador_torneio = JogadorTorneio.objects.create(nome=jogador['nome'], posicao_final=jogador['posicao_final'], 
                                                        id_challonge=jogador['id_challonge'], torneio=torneio)
        if 'time' in jogador:
            jogador_torneio.time = Time.objects.get_or_create(nome=jogador['time'])[0]
            jogador_torneio.save()
            
def criar_partidas_teste(torneio):
    """Gera partidas em um torneio para teste"""
    aceblind = JogadorTorneio.objects.get(nome='Aceblind')
    blower = JogadorTorneio.objects.get(nome='bløwer')
    yalda = JogadorTorneio.objects.get(nome='Yalda')
    
    round_7 = Round.objects.create(torneio=torneio, indice=7)
    
    round_6 = Round.objects.create(torneio=torneio, indice=6)
    
    round_8 = Round.objects.create(torneio=torneio, indice=8)
    
    partida_1 = Partida.objects.create(jogador_1=aceblind, jogador_2=blower, round=round_7, score_1=2, score_2=1, ganhador=aceblind)
    partida_2 = Partida.objects.create(jogador_1=blower, jogador_2=yalda, round=round_6, score_1=2, score_2=0, ganhador=blower)
    partida_3 = Partida.objects.create(jogador_1=aceblind, jogador_2=yalda, round=round_8, score_1=1, score_2=2, ganhador=yalda)
    