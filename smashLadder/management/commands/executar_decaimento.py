# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand
from django.db import transaction

from jogadores.models import Jogador
from ladder.models import PosicaoLadder, RemocaoJogador
from ladder.utils import avaliar_decaimento, decair_jogador, remover_jogador


class Command(BaseCommand):
    help = 'Executa o decaimento automático de jogadores inativos'

    def handle(self, *args, **options):
        executar_decaimento()
        
def executar_decaimento():
    """Executa decaimento automático a partir do segundo da ladder"""
    try:
        with transaction.atomic():
            lista_decaimentos = list()
            for posicao_ladder in PosicaoLadder.objects.filter(posicao__gte=2).order_by('-posicao'):
                # Verificar se jogador pode decair
                decaimento = avaliar_decaimento(posicao_ladder.jogador)
                if decaimento:
                    lista_decaimentos.append(decaimento)
            
                    # Verificar se deve apenas decair ou deve remover jogador
                    if decaimento.qtd_periodos_inatividade < 3:
                        decair_jogador(decaimento)
                    else:
                        # Usar qualquer admin como admin removedor
                        remocao = RemocaoJogador(jogador=decaimento.jogador, admin_removedor=Jogador.objects.filter(admin=True)[0],
                                                 data=decaimento.data, posicao_jogador=decaimento.posicao_inicial,
                                                 remocao_por_inatividade=True)
                        remocao.save()
                        remover_jogador(remocao)
                        decaimento.delete()
                        
    except:
        raise
    