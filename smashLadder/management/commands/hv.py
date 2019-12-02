# -*- encoding: utf-8 -*-

import datetime

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from ladder.utils import recalcular_ladder
from performance.models import PerformanceRequisicao


class Command(BaseCommand):
    help = 'Corrigir horário de verão'

    def handle(self, *args, **options):
        try :
            with transaction.atomic():
                # Requisições
                inicio = timezone.localtime().replace(month=11, day=3, hour=0, minute=0)
                for performance in PerformanceRequisicao.objects.filter(data_hora_requisicao__gte=inicio):
                    print(performance, performance.data_hora_requisicao, performance.data_hora_resposta)
                    performance.data_hora_requisicao = performance.data_hora_requisicao - datetime.timedelta(hours=1)
                    performance.data_hora_resposta = performance.data_hora_resposta - datetime.timedelta(hours=1)
                    performance.save()
                    print(performance, performance.data_hora_requisicao, performance.data_hora_resposta)
                                    
                recalcular_ladder(mes=11, ano=2019)
                
        except Exception as e:
            print(e)