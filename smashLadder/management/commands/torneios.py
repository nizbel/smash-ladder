# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

import challonge
from conf.conf import CHALLONGE_USER, CHALLONGE_API_KEY
from jogadores.models import Jogador
from torneios.models import Torneio, JogadorTorneio, VitoriaAusencia, Partida, \
    Time, Round
from torneios.utils import buscar_torneio_challonge, gerar_torneio_challonge,\
    buscar_jogadores_challonge, gerar_partidas_challonge


class Command(BaseCommand):
    help = 'Teste challonge'

    def handle(self, *args, **options):
        try:
            with transaction.atomic():
                # Tell pychallonge about your [CHALLONGE! API credentials](http://api.challonge.com/v1).
                challonge.set_credentials(CHALLONGE_USER, CHALLONGE_API_KEY)
                
                # Retrieve a tournament by its id (or its url).
#                 tournament = challonge.tournaments.show('atevalhalla2')
                tournament = buscar_torneio_challonge('atevalhalla2')
                
                # Torneio
#                 torneio = Torneio(nome=tournament['name'], data=timezone.localtime(tournament['started-at']).date(),
#                                   url=tournament['full-challonge-url'], adicionado_por=Jogador.objects.get(nick='Niz'))
                torneio = gerar_torneio_challonge(tournament)
                torneio.adicionado_por = Jogador.objects.get(nick='Niz')
                torneio.save()
                
                # Retrieve the participants for a given tournament.
#                 participants = challonge.participants.index(tournament['id'])
                participants = buscar_jogadores_challonge(torneio.id_challonge)
                for participant in participants:
                    # Verificar time
                    delimitador_time = '|'
                    if ' | ' in participant['name']:
                        nome_time = participant['name'].split(delimitador_time)[0].strip()
                        nome = participant['name'].split(delimitador_time)[1].strip()
                        if Time.objects.filter(nome=nome_time).exists():
                            time = Time.objects.get(nome=nome_time)
                        else:
                            time = Time(nome=nome_time)
                            time.save()
                    else:
                        time = None
                        nome = participant['name'].strip()
                    jogador = JogadorTorneio(nome=nome, posicao_final=participant['final-rank'], torneio=torneio,
                                             time=time, id_challonge=participant['id'])
                    jogador.save()
        
                matches = challonge.matches.index(tournament['id'])
                partidas, rounds, vitorias_por_ausencia = gerar_partidas_challonge(matches, torneio)
                for round_torneio in rounds:
                    round_torneio.save()
                for partida in partidas:
                    partida.round_id = partida.round.id
                    partida.save()
                for vitoria_por_ausencia in vitorias_por_ausencia:
                    vitoria_por_ausencia.partida_id = vitoria_por_ausencia.partida.id
                    vitoria_por_ausencia.save()
#                 for match in matches:
# 
#                     # Verificar se round já está registrado
#                     if Round.objects.filter(torneio=torneio, indice=match['round']).exists():
#                         round_torneio = Round.objects.get(torneio=torneio, indice=match['round'])
#                     else:
#                         # TODO Gerar nome de torneio
#                         round_torneio = Round(torneio=torneio, indice=match['round'])
#                         round_torneio.save()
#                     
#                     ganhador = JogadorTorneio.objects.get(id_no_torneio=match['winner-id'])
#                     jogador_1 = JogadorTorneio.objects.get(id_no_torneio=match['player1-id'])
#                     jogador_2 = JogadorTorneio.objects.get(id_no_torneio=match['player2-id'])
#                     
#                     score_1 = int(match['scores-csv'][: match['scores-csv'][1:].find('-') + 1])
#                     score_2 = int(match['scores-csv'][match['scores-csv'][1:].find('-') + 2 :])
#                     
#                     partida = Partida(ganhador=ganhador, jogador_1=jogador_1, jogador_2=jogador_2, score_1=score_1,
#                                       score_2=score_2, round=round_torneio)
#                     partida.save()
#                     if score_1 == score_2 or score_1 < 0 or score_2 < 0:
#                         vitoria_por_ausencia = VitoriaAusencia(partida=partida)
#                         vitoria_por_ausencia.save()
                
                print(torneio, torneio.data)
                for jogador in JogadorTorneio.objects.filter(torneio=torneio):
                    if jogador.time:
                        print(f'{jogador.time} | {jogador.nome}')
                    else:
                        print(jogador.nome)
                    
                for partida in Partida.objects.filter(jogador_1__torneio=torneio):
                    print(f'{partida.jogador_1} {partida.score_1} vs {partida.score_2} {partida.jogador_2} -> {partida.ganhador} {partida.vitoria_por_ausencia()}')
                
                raise ValueError('TESTE')
        except:
            raise
        
            
def jogador_por_id(jogadores, jogador_id):
    for jogador in jogadores:
        if jogador['id'] == jogador_id:
            return jogador
    return None
