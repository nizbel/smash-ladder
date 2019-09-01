# -*- coding: utf-8 -*-
"""Modelos usados para guardar torneios"""
from django.db import models
        
class Torneio(models.Model):
    PERIODO_TORNEIO_RECENTE = 60
    
    SITE_CHALLONGE_URL = 'https://challonge.com/'
    SITE_CHALLONGE_DESCRICAO = 'Challonge'
    SITE_CHALLONGE_ID = 1
    
    MENSAGEM_SUCESSO_CRIACAO_TORNEIO = 'Torneio criado com sucesso'
    MENSAGEM_SUCESSO_EDICAO_TORNEIO = 'Torneio editado com sucesso'
    MENSAGEM_ERRO_URL_TORNEIO_JA_EXISTENTE = 'Já existe um torneio com a URL informada'
    MENSAGEM_ERRO_SITE_INVALIDO = 'Site inválido'
    
    OPCOES_SITE = [(SITE_CHALLONGE_ID, SITE_CHALLONGE_DESCRICAO)]
    
    data = models.DateField('Data do torneio')
    nome = models.CharField('Nome do torneio', max_length=100)
    url = models.URLField('URL do torneio')
    adicionado_por = models.ForeignKey('jogadores.Jogador', on_delete=models.CASCADE)
    id_site = models.IntegerField('Código de identificação no site')
    
    class Meta:
        unique_together = (('url',), ('id_site',), ('nome', 'data'))
        
    def __str__(self):
        return self.nome
    
class Round(models.Model):
    indice = models.SmallIntegerField('Índice do round')
    nome = models.CharField('Nome do round', max_length=20, default='')
    torneio = models.ForeignKey('Torneio', on_delete=models.CASCADE)
    
    class Meta:
        unique_together = ('indice', 'torneio')
        
    def __str__(self):
        if self.nome:
            return self.nome
        return f'{self.indice}'
    
class Partida(models.Model):
    jogador_1 = models.ForeignKey('JogadorTorneio', on_delete=models.CASCADE, related_name='jogador_1')
    jogador_2 = models.ForeignKey('JogadorTorneio', on_delete=models.CASCADE, related_name='jogador_2')
    score_1 = models.SmallIntegerField('Resultado do jogador 1')
    score_2 = models.SmallIntegerField('Resultado do jogador 2')
    round = models.ForeignKey('Round', on_delete=models.CASCADE)
    ganhador = models.ForeignKey('JogadorTorneio', on_delete=models.CASCADE, related_name='ganhador')
    
    def vitoria_por_ausencia(self):
        return hasattr(self, 'vitoriaausencia')
    
class VitoriaAusencia(models.Model):
    """Define se partida foi vencida por ausência"""
    partida = models.OneToOneField('Partida', on_delete=models.CASCADE)
    
class JogadorTorneio(models.Model):
    """Vincula jogador a um torneio"""
    nome = models.CharField('Nome do jogador', max_length=30)
    time = models.ForeignKey('Time', on_delete=models.CASCADE, blank=True, null=True)
    jogador = models.ForeignKey('jogadores.Jogador', on_delete=models.CASCADE, blank=True, null=True)
    torneio = models.ForeignKey('Torneio', on_delete=models.CASCADE)
    posicao_final = models.SmallIntegerField('Resultado no torneio')
    valido = models.BooleanField('Jogador válido?', default=True)
    id_site = models.IntegerField('Código de identificação no site')
    seed = models.SmallIntegerField('Seed')
    
    class Meta:
        unique_together = (('nome', 'torneio', 'time'), ('jogador', 'torneio'), ('seed', 'torneio'), 
                           ('id_site', 'torneio'))
        
    def __str__(self):
        if self.time:
            return f'{self.time} | {self.nome}'
        return self.nome
        
class Time(models.Model):
    """Time a qual um jogador pertence em um torneio"""
    nome = models.CharField('Nome do time', max_length=20)
    
    class Meta:
        unique_together = ('nome',)
        
    def __str__(self):
        return self.nome
