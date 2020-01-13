# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from ladder.models import HistoricoLadder, PosicaoLadder
from ladder.utils import recalcular_ladder
from smashLadder.utils import mes_ano_prox


MES = 1
ANO = 2020

class Command(BaseCommand):
    help = 'Recalcular ladder geral'

    def handle(self, *args, **options):
        try:
            with transaction.atomic():
                if MES != timezone.localtime().month or ANO != timezone.localtime().year:
                    recalcular_ladder(mes=MES, ano=ANO)
                else:
                    recalcular_ladder()
                
                mes = MES
                ano = ANO
                
                while mes != timezone.localtime().month or ano != timezone.localtime().year:
                    print(f'{mes} / {ano}\n')
                    for _ in HistoricoLadder.objects.filter(mes=mes, ano=ano).order_by('posicao'):
                        print(f'{_.posicao}: {_.jogador}')
                    
                    mes, ano = mes_ano_prox(mes, ano)
                
                print('ATUAL\n')
                for _ in PosicaoLadder.objects.all().order_by('posicao'):
                    print(f'{_.posicao}: {_.jogador}')
                    
                
        except:
            raise
        