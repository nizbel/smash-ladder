# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand

import challonge
from conf.conf import CHALLONGE_USER, CHALLONGE_API_KEY


class Command(BaseCommand):
    help = 'Teste challonge'

    def handle(self, *args, **options):

        # Tell pychallonge about your [CHALLONGE! API credentials](http://api.challonge.com/v1).
        challonge.set_credentials(CHALLONGE_USER, CHALLONGE_API_KEY)
        
        # Retrieve a tournament by its id (or its url).
        tournament = challonge.tournaments.show('atevalhalla2')
        
        # Tournaments, matches, and participants are all represented as normal Python dicts.
        print(tournament['id'])
        print(tournament['name']) 
        print(tournament['started-at'])
        
        # Retrieve the participants for a given tournament.
        participants = challonge.participants.index(tournament['id'])
        print(len(participants))
        for participant in participants:
            print(participant['name'], participant['final-rank'])

        matches = challonge.matches.index(tournament['id'])
        print(len(matches))
        for match in matches:
            jogador_1 = jogador_por_id(participants, match['player1-id'])['name']
            jogador_2 = jogador_por_id(participants, match['player2-id'])['name']
            print(f'{jogador_1} {match["scores-csv"]} {jogador_2}')
            
def jogador_por_id(jogadores, jogador_id):
    for jogador in jogadores:
        if jogador['id'] == jogador_id:
            return jogador
    return None