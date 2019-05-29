# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand
from django.db import transaction

from ladder.models import PosicaoLadder
from ladder.utils import avaliar_decaimento, decair_jogador


class Command(BaseCommand):
    help = 'Executa o decaimento automático de jogadores inativos'

    def handle(self, *args, **options):
        executar_decaimento()
        
def executar_decaimento():
    """Executa decaimento automático a partir do segundo da ladder"""
    try:
        with transaction.atomic():
            for posicao_ladder in PosicaoLadder.objects.filter(posicao__gte=2).order_by('posicao'):
                # Verificar se jogador pode decair
                decaimento = avaliar_decaimento(posicao_ladder.jogador)
                if decaimento:
                    decair_jogador(decaimento)
                    
    except:
        raise
    