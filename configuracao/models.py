# -*- coding: utf-8 -*-
from django.contrib.auth.models import User
from django.db import models

from smashLadder.utils import DateTimeFieldTz


class ConfiguracaoLadder(models.Model):
    CONFIGURACAO_LIMITE_POSICOES_DESAFIO = 'limite_posicoes_desafio'
    CONFIGURACAO_MELHOR_DE = 'melhor_de'
    CONFIGURACAO_PERIODO_SEASON = 'periodo_season'
    
    PADRAO_LIMITE_POSICOES_DESAFIO = 3
    PADRAO_MELHOR_DE = 5
    
    VALOR_SEASON_TRIMESTRAL = 1
    DESCRICAO_SEASON_TRIMESTRAL = 'Trimestral'
    VALOR_SEASON_QUADRIMESTRAL = 2
    DESCRICAO_SEASON_QUADRIMESTRAL = 'Quadrimestral'
    VALOR_SEASON_SEMESTRAL = 3
    DESCRICAO_SEASON_SEMESTRAL = 'Semestral'
    CHOICES_PERIODO_SEASON = [(VALOR_SEASON_TRIMESTRAL, DESCRICAO_SEASON_TRIMESTRAL), 
                              (VALOR_SEASON_QUADRIMESTRAL, DESCRICAO_SEASON_QUADRIMESTRAL), 
                              (VALOR_SEASON_SEMESTRAL, DESCRICAO_SEASON_SEMESTRAL)]
    PADRAO_PERIODO_SEASON = VALOR_SEASON_TRIMESTRAL
    
    
    
    # Altera DesafioLadder.LIMITE_POSICOES_DESAFIO
    limite_posicoes_desafio = models.SmallIntegerField('Limite de posições para desafiar', default=PADRAO_LIMITE_POSICOES_DESAFIO)
    melhor_de = models.SmallIntegerField('Formato melhor de', default=PADRAO_MELHOR_DE)
    periodo_season = models.SmallIntegerField('Período de uma Season', default=PADRAO_PERIODO_SEASON, 
                                              choices=CHOICES_PERIODO_SEASON)
    
    def __str__(self):
        return 'Configurações de Ladder'
    
    @staticmethod
    def buscar_configuracao(lista_configuracoes):
        try:
            return ConfiguracaoLadder.objects.all().values(*lista_configuracoes)[0]
        except IndexError:
            # Se não existir configurações, gerar padrão
            config = ConfiguracaoLadder(
                limite_posicoes_desafio=ConfiguracaoLadder.PADRAO_LIMITE_POSICOES_DESAFIO,
                melhor_de=ConfiguracaoLadder.PADRAO_MELHOR_DE,
                periodo_season=ConfiguracaoLadder.PADRAO_PERIODO_SEASON
                )
            config.save()
            
            return ConfiguracaoLadder.objects.all().values(*lista_configuracoes)[0]

class HistoricoConfiguracaoLadder(models.Model):
    limite_posicoes_desafio = models.SmallIntegerField('Limite de posições para desafiar', blank=True, null=True)
    melhor_de = models.SmallIntegerField('Limite máximo de partidas em um desafio', blank=True, null=True)
    # Guardar responsável pela alteração
    responsavel = models.ForeignKey(User, blank=True, null=True, on_delete=models.CASCADE, related_name='responsavel_alteracao')
    data_hora = DateTimeFieldTz(u'Data e hora do resultado', auto_now_add=True)
    