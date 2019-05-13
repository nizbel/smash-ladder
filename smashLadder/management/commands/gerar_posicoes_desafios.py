# -*- coding: utf-8 -*-
import datetime

from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models.aggregates import Sum

from jogadores.models import Jogador, RegistroFerias
from ladder.models import DesafioLadder, HistoricoLadder, PosicaoLadder, \
    InicioLadder, ResultadoDesafioLadder
from ladder.utils import alterar_ladder, desfazer_desafio, \
    desfazer_lote_desafios, recalcular_ladder


# ALTERAÇÕES MIZZ - MONKEY 21:50
#            MIZZ - TIO DA SAMUS 20:30
#            STEFAN - ACEBLIND 21:30
#            YALDA - ACEBLIND 21:40
#            ZOOL - CPU 10:50
# LADDER INICIAL ALTERAR POSIÇÕES PARA COBRIR PK
# FÉRIAS ALTERAR DATA DE FÉRIAS DO BACABAU, 29/04
# GERAR POSIÇÕES DESAFIOS
class Command(BaseCommand):
    help = 'Gera posições de desafiado para cada desafio'

    def handle(self, *args, **options):
        try:
            with transaction.atomic():
                # Apagar resultados anteriores
                ResultadoDesafioLadder.objects.all().delete()
                
                # Alterações necessárias
                ferias_bacabau = RegistroFerias.objects.get(jogador__nick='Bacabau')
                ferias_bacabau.data_inicio = datetime.datetime(2019, 4, 29)
                ferias_bacabau.save()
                
                desafio_mizz_monkey = DesafioLadder.objects.get(id=77)
                desafio_mizz_monkey.data_hora = desafio_mizz_monkey.data_hora.replace(hour=21, minute=50)
                desafio_mizz_monkey.save()
                desafio_mizz_tio = DesafioLadder.objects.get(id=76)
                desafio_mizz_tio.data_hora = desafio_mizz_monkey.data_hora.replace(hour=20, minute=30)
                desafio_mizz_tio.save()
                desafio_stefan_ace = DesafioLadder.objects.get(id=74)
                desafio_stefan_ace.data_hora = desafio_mizz_monkey.data_hora.replace(hour=21, minute=30)
                desafio_stefan_ace.save()
                desafio_yalda_ace = DesafioLadder.objects.get(id=79)
                desafio_yalda_ace.data_hora = desafio_mizz_monkey.data_hora.replace(hour=21, minute=40)
                desafio_yalda_ace.save()
                desafio_zool_cpu = DesafioLadder.objects.get(id=41)
                desafio_zool_cpu.data_hora = desafio_mizz_monkey.data_hora.replace(hour=10, minute=50)
                desafio_zool_cpu.save()
                
                for posicao_ladder in InicioLadder.objects.filter(posicao__gt=18).order_by('posicao'):
                    posicao_ladder.posicao -= 1
                    posicao_ladder.save()
                
                for desafio in DesafioLadder.validados.order_by('data_hora', 'id'):
                    posicao = desafio.desafiado.posicao_em(desafio.data_hora)
                    if posicao == 0:
                        posicao = Jogador.objects.count()
                    desafio.posicao_desafiado = posicao
                    desafio.posicao_desafiante = Jogador.objects.count() + 1
                    desafio.save()
                
                # Buscar mês/ano de primeiro histórico de ladder
                if HistoricoLadder.objects.all().exists():
                    historico_mais_antigo = HistoricoLadder.objects.all().order_by('ano', 'mes')[0]
                    mes = historico_mais_antigo.mes
                    ano = historico_mais_antigo.ano
                else:
                    mes = None
                    ano = None
                    
                # Testar recalculo
                recalcular_ladder(mes=mes, ano=ano)
                
                
                while HistoricoLadder.objects.filter(mes=mes, ano=ano).exists():
                    print('------------------------------------------------------')
                    print(mes, '/', ano)
                    print('------------------------------------------------------')
                    for historico in HistoricoLadder.objects.filter(mes=mes, ano=ano).order_by('posicao'):
                        print(historico)
                        
                    mes += 1
                    if mes == 13:
                        mes = 1
                        ano += 1
                
                print('------------------------------------------------------')
                print('ATUAL')
                print('------------------------------------------------------')
                for historico in PosicaoLadder.objects.all().order_by('posicao'):
                    print(historico)
                
        except:
            raise