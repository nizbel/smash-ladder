# -*- coding: utf-8 -*-
import datetime

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from ladder.models import PosicaoLadder, HistoricoLadder, DesafioLadder


class Command(BaseCommand):
    help = 'Gera histórico de ladder para mês anterior ao mês atual'

    def handle(self, *args, **options):
        try:
            with transaction.atomic():
                copiar_info_ladder_atual_para_mes_passado()
        except:
            raise
        
def copiar_info_ladder_atual_para_mes_passado():
    try:
        with transaction.atomic():
            data_mes_passado = timezone.now().replace(day=1) - datetime.timedelta(days=1)
            mes = data_mes_passado.month
            ano = data_mes_passado.year
            if DesafioLadder.objects.filter(data_hora__month=mes, data_hora__year=ano).exists():
                for posicao_ladder in PosicaoLadder.objects.all().order_by('posicao'):
                    historico_ladder = HistoricoLadder(posicao=posicao_ladder.posicao, jogador=posicao_ladder.jogador,
                                                       mes=mes, ano=ano)
                    historico_ladder.save()
                
    except:
        raise