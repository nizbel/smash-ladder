# -*- coding: utf-8 -*-
import datetime
from importlib import reload
import random
import sys
import traceback

from django.core.mail import mail_admins
from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models.aggregates import Max
from django.urls.base import clear_url_caches
from django.utils import timezone

from configuracao.models import ConfiguracaoLadder
from ladder.models import Lockdown, SeasonPosicaoInicial, \
    InicioLadder, Season, SeasonPosicaoFinal, PosicaoLadder, HistoricoLadder, \
    DesafioLadder
from smashLadder import settings


class Command(BaseCommand):
    help = 'Gera histórico de ladder para mês anterior ao mês atual'

    def handle(self, *args, **options):
        # Evitar que a geração de seasons aconteça antes de 2020
        if settings.DEBUG == False and timezone.localtime().year < 2020:
            return
        
        # Se houver seasons
        # Verificar se Season atual já chegou ao fim
        if Season.objects.exists():
            ultima_season = Season.objects.all().order_by('-data_fim')[0]
            # Se season for indeterminada, manter
            if ultima_season.data_fim != None and timezone.localtime().date() > ultima_season.data_fim:
                pass
            else:
                return
        # Se não houver, criar a primeira de acordo com a configuração atual
        else:
            try:
                with transaction.atomic():
                    gerar_season_inicial()
                    return
            except:
                mail_admins("Erro em gerar seasons", traceback.format_exc())
                raise
        
        try:
            with transaction.atomic():
                iniciar_lockdown()
                
                guardar_dados_season_anterior()
                 
                apagar_ladder_season_anterior()
                 
                gerar_season_nova()
                 
                encerrar_lockdown()
        except:
            encerrar_lockdown()
            mail_admins("Erro em gerar seasons", traceback.format_exc())
            raise


def gerar_season_inicial():
    try:
        with transaction.atomic():
            # Data de início é a data do primeiro desafio ou a data atual
            if DesafioLadder.validados.exists():
                data_inicio = DesafioLadder.validados.order_by('data_hora')[0].data_hora.date()
            else:
                data_inicio = timezone.localdate()
            nova_season = Season(ano=timezone.localtime().year, indice=1, data_inicio=data_inicio, data_fim=None)
            nova_season.save()
    except:
        raise

def iniciar_lockdown():
    """Bloqueia URLs durante geração de season"""
    status_lockdown = Lockdown.buscar()
    status_lockdown.valido = True
    status_lockdown.save()
    
    recarregar_urls()
    
def encerrar_lockdown():
    """Desbloqueia URLs durante geração de season"""
    status_lockdown = Lockdown.buscar()
    status_lockdown.valido = False
    status_lockdown.save()
    
    recarregar_urls()
    
def guardar_dados_season_anterior():
    """Guardar posições inicial e final da season anterior"""
    # Verificar se não há Season para guardar período sem Season
#     if not Season.objects.exists():
#         # Guardar posição inicial
#         for inicio in InicioLadder.objects.all().order_by('posicao'):
#             posicao_inicial = SeasonPosicaoInicial(jogador=inicio.jogador, posicao=inicio.posicao)
#             posicao_inicial.save()
#             
#         # Guardar posição final
#         for fim in PosicaoLadder.objects.all().order_by('posicao'):
#             posicao_final = SeasonPosicaoFinal(jogador=fim.jogador, posicao=fim.posicao)
#             posicao_final.save()
#     
#     # Se há, buscar a última
#     else:
    ultima_season = Season.objects.all().order_by('-data_inicio')[0]
    # Guardar posição inicial
    for inicio in InicioLadder.objects.all().order_by('posicao'):
        posicao_inicial = SeasonPosicaoInicial(season=ultima_season, jogador=inicio.jogador, posicao=inicio.posicao)
        posicao_inicial.save()
        
    # Guardar posição final
    for fim in PosicaoLadder.objects.all().order_by('posicao'):
        posicao_final = SeasonPosicaoFinal(season=ultima_season, jogador=fim.jogador, posicao=fim.posicao)
        posicao_final.save()
            
def apagar_ladder_season_anterior():
    """Apagar dados relacionados a season anterior"""
    InicioLadder.objects.all().delete()
    HistoricoLadder.objects.all().delete()
    PosicaoLadder.objects.all().delete()
    # Apaga desafios não validados
    DesafioLadder.objects.filter(cancelamentodesafioladder__isnull=True, admin_validador__isnull=True).delete()
    
def gerar_season_nova():
    """Gerar nova Season"""
    horario_atual = timezone.localtime()
    # Gerar Season
    ano_atual = horario_atual.year
    indice = (Season.objects.filter(ano=ano_atual).aggregate(maior_indice=Max('indice'))['maior_indice'] or 0) + 1
    
    # Definir data de fim
    if Season.PERIODO_SEASON == ConfiguracaoLadder.VALOR_SEASON_INDETERMINADO:
        data_fim = None
    else:
        mes_atual = horario_atual.month
        meses_duracao = 0
        if Season.PERIODO_SEASON == ConfiguracaoLadder.VALOR_SEASON_TRIMESTRAL:
            meses_duracao = 3
        elif Season.PERIODO_SEASON == ConfiguracaoLadder.VALOR_SEASON_QUADRIMESTRAL:
            meses_duracao = 4
        elif Season.PERIODO_SEASON == ConfiguracaoLadder.VALOR_SEASON_SEMESTRAL:
            meses_duracao = 6
            
        mes_fim = mes_atual + meses_duracao
        ano_fim = ano_atual
        if mes_fim > 12:
            ano_fim += 1
            mes_fim -= 12
        
        data_fim = datetime.date(ano_fim, mes_fim, 1) - datetime.timedelta(days=1)
        
    nova_season = Season(ano=ano_atual, indice=indice, data_inicio=horario_atual.date(), data_fim=data_fim)
    nova_season.save()
    
    # Gerar posição inicial
    # Buscar última season
    if Season.objects.all().exclude(id=nova_season.id).exists():
        season_id = Season.objects.all().order_by('-data_inicio')[0].id
    else:
        season_id = None
        
    # Guardar posições finais de última season
    posicoes_finais = list(SeasonPosicaoFinal.objects.filter(season__id=season_id).order_by('posicao'))
    
    nova_ladder = []
    for posicao_final in posicoes_finais:
        nova_ladder.append(InicioLadder(posicao=posicao_final.posicao))
    
    # Enviar 10 primeiros para o final
    posicao_atual = 1
    while (posicao_atual <= 10 and posicao_atual <= len(nova_ladder)):
        nova_ladder[-posicao_atual].jogador = posicoes_finais[posicao_atual-1].jogador
        
        posicao_atual += 1
        
    # Randomizar o resto
    if posicao_atual <= len(nova_ladder):
        jogadores_restantes = posicoes_finais[10:]
        # Reordenar restante
        random.shuffle(jogadores_restantes)
        
        # Atualizar lita
        posicao_atual = 0
        for jogador_restante in jogadores_restantes:
            nova_ladder[posicao_atual].jogador = jogador_restante.jogador
            posicao_atual += 1
    
    # Salvar posições iniciais
    for posicao_inicial in nova_ladder:
        posicao_inicial.save()
        posicao_atual = PosicaoLadder(posicao=posicao_inicial.posicao, jogador=posicao_inicial.jogador)
        posicao_atual.save()
    
def recarregar_urls():
    """Recarrega URLConf"""
    urlconf = settings.ROOT_URLCONF
    if urlconf in sys.modules:
        clear_url_caches()
        reload(sys.modules[urlconf])
