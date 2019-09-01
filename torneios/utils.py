# -*- coding: utf-8 -*-
import datetime

from django.db.models.aggregates import Max, Min
from django.utils import timezone

import challonge
from conf.conf import CHALLONGE_USER, CHALLONGE_API_KEY
from jogadores.models import Jogador
from torneios.models import Torneio, Time, JogadorTorneio, Round, Partida, \
    VitoriaAusencia


def logar_challonge():
    """Loga com as credenciais no Challonge"""
    challonge.set_credentials(CHALLONGE_USER, CHALLONGE_API_KEY)

def buscar_torneio_challonge(identificador_torneio):
    """Busca dados de um torneio a partir de um identificador (ID ou URL)"""
    dados_torneio = challonge.tournaments.show(identificador_torneio)
    
    return dados_torneio

def gerar_torneio_challonge(dados_torneio):
    """Gera um torneio com base em dados do Challonge"""
    torneio = Torneio(nome=dados_torneio['name'], data=timezone.localtime(dados_torneio['started-at']).date(),
                                  url=dados_torneio['full-challonge-url'], id_site=dados_torneio['id'])
                
    return torneio

def buscar_jogadores_challonge(identificador_torneio):
    """Busca dados de jogadores de um torneio a partir de um identificador (ID ou URL)"""
    dados_jogadores = challonge.participants.index(identificador_torneio)
    
    return dados_jogadores

def gerar_jogadores_challonge(dados_jogadores, torneio, delimitador_time='|'):
    """Gera jogadores de um torneio com base em dados do Challonge"""
    times = list()
    jogadores = list()
    for dados_jogador in dados_jogadores:
        # Verificar time
        if delimitador_time in dados_jogador['name']:
            nome_time = dados_jogador['name'].split(delimitador_time)[0].strip()
            nome = dados_jogador['name'].split(delimitador_time)[1].strip()
            if Time.objects.filter(nome=nome_time).exists():
                time = Time.objects.get(nome=nome_time)
            elif nome_time in [time.nome for time in times]:
                time = [time for time in times if time.nome == nome_time][0]
            else:
                time = Time(nome=nome_time)
                times.append(time)
        else:
            time = None
            nome = dados_jogador['name'].strip()
        jogador = JogadorTorneio(nome=nome, posicao_final=dados_jogador['final-rank'], torneio=torneio,
                                 time=time, id_site=dados_jogador['id'], seed=dados_jogador['seed'])
        jogadores.append(jogador)
                
    return (jogadores, times)

def buscar_partidas_challonge(identificador_torneio):
    """Busca dados de partidas de um torneio a partir de um identificador (ID ou URL)"""
    dados_partidas = challonge.matches.index(identificador_torneio)
    
    return dados_partidas

def gerar_partidas_challonge(dados_partidas, torneio):
    """Gera objetos de partidas de um torneio com base em dados do Challonge"""
    partidas = list()
    rounds = list()
    vitorias_ausencia = list()
    for dados_partida in dados_partidas:
        # Verificar se round já está registrado
        if Round.objects.filter(torneio=torneio, indice=dados_partida['round']).exists():
            round_torneio = Round.objects.get(torneio=torneio, indice=dados_partida['round'])
        elif dados_partida['round'] in [round_torneio.indice for round_torneio in rounds]:
            round_torneio = [round_torneio for round_torneio in rounds if round_torneio.indice == dados_partida['round']][0]
        else:
            # Gerar nome de torneio
            nome_round = f'Winners {dados_partida["round"]}' if  dados_partida['round'] >= 0 else f'Losers {abs(dados_partida["round"])}'
            
            round_torneio = Round(torneio=torneio, indice=dados_partida['round'], nome=nome_round)
            rounds.append(round_torneio)
            
        ganhador = JogadorTorneio.objects.get(id_site=dados_partida['winner-id'])
        jogador_1 = JogadorTorneio.objects.get(id_site=dados_partida['player1-id'])
        jogador_2 = JogadorTorneio.objects.get(id_site=dados_partida['player2-id'])
        
        score_1 = int(dados_partida['scores-csv'][: dados_partida['scores-csv'][1:].find('-') + 1])
        score_2 = int(dados_partida['scores-csv'][dados_partida['scores-csv'][1:].find('-') + 2 :])
        
        partida = Partida(ganhador=ganhador, jogador_1=jogador_1, jogador_2=jogador_2, score_1=score_1,
                          score_2=score_2, round=round_torneio)
        
        if score_1 == score_2 or score_1 < 0 or score_2 < 0:
            vitoria_por_ausencia = VitoriaAusencia(partida=partida)
            vitorias_ausencia.append(vitoria_por_ausencia)
        
        partidas.append(partida)
        
    return (partidas, rounds, vitorias_ausencia)

def vincular_automaticamente_jogadores_torneio_a_ladder(torneio):
    """Vincula jogadores do torneio a jogadores da ladder"""
    # Comparar nomes sempre em minúsculo
    nicks_jogador_ladder = [nick.lower() for nick in Jogador.objects.all().values_list('nick', flat=True)]
    for jogador_torneio in JogadorTorneio.objects.filter(torneio=torneio):
        jogador_torneio.nome_lower = jogador_torneio.nome.lower()
        if jogador_torneio.nome_lower in nicks_jogador_ladder:
            jogador_torneio.jogador = Jogador.objects.get(nick__iexact=jogador_torneio.nome)
            jogador_torneio.save()
            
        # Os que não tiveram vínculo automático, buscar por torneios passados
        else:
            if JogadorTorneio.objects.filter(torneio__data__range=[torneio.data - datetime.timedelta(days=Torneio.PERIODO_TORNEIO_RECENTE), torneio.data], 
                                             nome=jogador_torneio.nome, jogador__isnull=False).exists():
                jogador_torneio.jogador = JogadorTorneio.objects.filter(torneio__data__lt=torneio.data, nome=jogador_torneio.nome, jogador__isnull=False) \
                .order_by('-torneio__data')[0].jogador
                jogador_torneio.save()
                
def alterar_nome_rounds(torneio):
    """Altera nomes de rounds finais"""
    ultimo_round_winners = Round.objects.filter(torneio=torneio).aggregate(ultimo_round=Max('indice'))['ultimo_round']
    Round.objects.filter(torneio=torneio, indice=(ultimo_round_winners-2)).update(nome='Winners Semis')
    Round.objects.filter(torneio=torneio, indice=(ultimo_round_winners-1)).update(nome='Winners Finals')
    Round.objects.filter(torneio=torneio, indice=ultimo_round_winners).update(nome='Grand Finals')
    
    ultimo_round_losers = Round.objects.filter(torneio=torneio).aggregate(ultimo_round=Min('indice'))['ultimo_round']
    Round.objects.filter(torneio=torneio, indice=(ultimo_round_losers-1)).update(nome='Losers Semis')
    Round.objects.filter(torneio=torneio, indice=ultimo_round_losers).update(nome='Losers Finals')
