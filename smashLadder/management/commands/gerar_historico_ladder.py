# -*- coding: utf-8 -*-
import datetime

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from ladder.models import PosicaoLadder, HistoricoLadder



class Command(BaseCommand):
    help = 'Gera histórico de ladder para mês anterior ao mês atual'

    def handle(self, *args, **options):
        try:
            with transaction.atomic():
                copiar_info_atual_para_mes_passado()
        except:
            raise
        
def copiar_info_atual_para_mes_passado():
    HistoricoLadder.objects.all().delete()
    try:
        with transaction.atomic():
            data_mes_passado = timezone.now().replace(day=1) - datetime.timedelta(days=1)
            mes = data_mes_passado.month
            ano = data_mes_passado.year
            for posicao_ladder in PosicaoLadder.objects.all().order_by('posicao'):
                historico_ladder = HistoricoLadder(posicao=posicao_ladder.posicao, jogador=posicao_ladder.jogador,
                                                   mes=mes, ano=ano)
                historico_ladder.save()
                
                
            # TODO apagar isso aqui
            for _ in range(13):
                mes -= 1
                if mes == 0:
                    mes = 12
                    ano -= 1
                for posicao_ladder in PosicaoLadder.objects.all().order_by('posicao'):
                    historico_ladder = HistoricoLadder(posicao=posicao_ladder.posicao, jogador=posicao_ladder.jogador,
                                                       mes=mes, ano=ano)
                    historico_ladder.save()
                    
    except:
        raise