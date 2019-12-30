# -*- coding: utf-8 -*-
from django.contrib.auth.models import User
from django.db import models

from smashLadder.utils import DateTimeFieldTz


class ConfiguracaoLadder(models.Model):
    CONFIGURACAO_LIMITE_POSICOES_DESAFIO = 'limite_posicoes_desafio'
    CONFIGURACAO_MELHOR_DE = 'melhor_de'
    CONFIGURACAO_PERIODO_SEASON = 'periodo_season'
    CONFIGURACAO_ABONAR_PRIMEIRO_DECAIMENTO = 'abonar_primeiro_decaimento'
    CONFIGURACAO_PERIODO_INATIVIDADE = 'periodo_inatividade'
    CONFIGURACAO_USO_CORINGA = 'uso_coringa'
    
    PADRAO_LIMITE_POSICOES_DESAFIO = 3
    PADRAO_MELHOR_DE = 5
    
    VALOR_SEASON_INDETERMINADO = 0
    DESCRICAO_SEASON_INDETERMINADO = 'Indeterminado'
    VALOR_SEASON_TRIMESTRAL = 1
    DESCRICAO_SEASON_TRIMESTRAL = 'Trimestral'
    VALOR_SEASON_QUADRIMESTRAL = 2
    DESCRICAO_SEASON_QUADRIMESTRAL = 'Quadrimestral'
    VALOR_SEASON_SEMESTRAL = 3
    DESCRICAO_SEASON_SEMESTRAL = 'Semestral'
    CHOICES_PERIODO_SEASON = [(VALOR_SEASON_INDETERMINADO, DESCRICAO_SEASON_INDETERMINADO),
                              (VALOR_SEASON_TRIMESTRAL, DESCRICAO_SEASON_TRIMESTRAL), 
                              (VALOR_SEASON_QUADRIMESTRAL, DESCRICAO_SEASON_QUADRIMESTRAL), 
                              (VALOR_SEASON_SEMESTRAL, DESCRICAO_SEASON_SEMESTRAL)]
    PADRAO_PERIODO_SEASON = VALOR_SEASON_INDETERMINADO
    
    PADRAO_ABONAR_PRIMEIRO_DECAIMENTO = False
    PADRAO_PERIODO_INATIVIDADE = 30
    PADRAO_USO_CORINGA = True
    
    
    # Altera DesafioLadder.LIMITE_POSICOES_DESAFIO
    limite_posicoes_desafio = models.SmallIntegerField('Limite de posições para desafiar', default=PADRAO_LIMITE_POSICOES_DESAFIO)
    melhor_de = models.SmallIntegerField('Formato melhor de', default=PADRAO_MELHOR_DE)
    periodo_season = models.SmallIntegerField('Período de uma Season', default=PADRAO_PERIODO_SEASON, 
                                              choices=CHOICES_PERIODO_SEASON)
    abonar_primeiro_decaimento = models.BooleanField('Abonar primeiro decaimento?', default=PADRAO_ABONAR_PRIMEIRO_DECAIMENTO)
    periodo_inatividade = models.SmallIntegerField('Período de inatividade para cair', default=PADRAO_PERIODO_INATIVIDADE)
    uso_coringa = models.BooleanField('Permitido coringa?', default=PADRAO_USO_CORINGA)
    
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
                periodo_season=ConfiguracaoLadder.PADRAO_PERIODO_SEASON,
                abonar_primeiro_decaimento=ConfiguracaoLadder.PADRAO_ABONAR_PRIMEIRO_DECAIMENTO,
                periodo_inatividade=ConfiguracaoLadder.PADRAO_PERIODO_INATIVIDADE,
                uso_coringa=ConfiguracaoLadder.PADRAO_USO_CORINGA
                )
            config.save()
            return ConfiguracaoLadder.objects.all().values(*lista_configuracoes)[0]
        
    @staticmethod
    def realizar_alteracoes():
        from ladder.models import DesafioLadder, Season, DecaimentoJogador
        DesafioLadder.alterar_melhor_de()
        DesafioLadder.alterar_limite_posicoes_desafio()
        Season.alterar_periodo_season()
        DecaimentoJogador.alterar_abonar_primeiro_decaimento()
        DecaimentoJogador.alterar_periodo_inatividade()
        DesafioLadder.alterar_uso_coringa()

class HistoricoConfiguracaoLadder(models.Model):
    limite_posicoes_desafio = models.SmallIntegerField('Limite de posições para desafiar', blank=True, null=True)
    melhor_de = models.SmallIntegerField('Formato melhor de', blank=True, null=True)
    periodo_season = models.SmallIntegerField('Período de uma Season', blank=True, null=True)
    abonar_primeiro_decaimento = models.BooleanField('Abonar primeiro decaimento?', blank=True, null=True)
    periodo_inatividade = models.SmallIntegerField('Período de inatividade para cair', blank=True, null=True)
    uso_coringa = models.BooleanField('Permitido coringa?', blank=True, null=True)
    # Guardar responsável pela alteração
    responsavel = models.ForeignKey(User, blank=True, null=True, on_delete=models.CASCADE, related_name='responsavel_alteracao')
    data_hora = DateTimeFieldTz(u'Data e hora do resultado', auto_now_add=True)
    