# -*- coding: utf-8 -*-
"""Modelos usados para guardar jogadores"""
from django.contrib.auth.models import User
from django.db import models
from ladder.models import DesafioLadder


class Jogador(models.Model):
    """Informações do jogador"""
    nick = models.CharField(u'Nickname', max_length=30)
    main = models.ForeignKey('Personagem', on_delete=models.CASCADE, blank=True, null=True)
    admin = models.BooleanField(u'É da administração?', default=False)
    ultimo_uso_coringa = models.DateField(u'Último uso de coringa', default=None, blank=True, null=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    
    def __str__(self):
        return self.nick
    
    class Meta:
        verbose_name_plural = 'jogadores'
        unique_together = ('nick',)
        ordering = ('nick',)
        
    def de_ferias_na_data(self, data):
        """Verifica se jogador está de férias na data apontada"""
        return RegistroFerias.objects.filter(jogador=self, data_inicio__lte=data, data_fim__gte=data).exists()
    
    def pode_usar_coringa_na_data(self, data):
        return self.ultimo_uso_coringa == None or \
            (data - self.ultimo_uso_coringa).days >= DesafioLadder.PERIODO_ESPERA_DESAFIO_CORINGA

class Personagem(models.Model):
    """Personagens disponíveis no jogo"""
    nome = models.CharField(u'Nome', max_length=30)
    
    def __str__(self):
        return self.nome
    
    class Meta:
        verbose_name_plural = 'personagens'
        unique_together = ('nome',)
        ordering = ('nome',)

class Stage(models.Model):
    """Estágios disponíveis no jogo"""
    TIPO_NORMAL = 1
    TIPO_BATTLEFIELD = 2
    TIPO_OMEGA = 3
    
    TIPO_NORMAL_DESCRICAO = 'Normal'
    TIPO_BATTLEFIELD_DESCRICAO = 'Battlefield'
    TIPO_OMEGA_DESCRICAO = 'Omega'
    
    ESCOLHAS_MODELO = [(TIPO_NORMAL,TIPO_NORMAL_DESCRICAO), 
                       (TIPO_BATTLEFIELD, TIPO_BATTLEFIELD_DESCRICAO), 
                       (TIPO_OMEGA, TIPO_OMEGA_DESCRICAO)]
    
    nome = models.CharField(u'Nome do estágio', max_length=30)
    modelo = models.SmallIntegerField(u'Modelo do estágio', choices=ESCOLHAS_MODELO)

    def __str__(self):
        return f'{self.nome} ({self.descricao_modelo})'
    
    class Meta:
        unique_together = ('nome', 'modelo')
        ordering = ('nome', 'modelo')
    
    @property
    def descricao_modelo(self):
        for opcao in self.ESCOLHAS_MODELO:
            if self.modelo == opcao[0]:
                return opcao[1]
        
        raise ValueError(f'{self.nome} tem modelo indefinido')

class RegistroFerias(models.Model):
    """Registro de férias de jogador"""
    jogador = models.ForeignKey('Jogador', on_delete=models.CASCADE)
    data_inicio = models.DateField(u'Início das férias')
    data_fim = models.DateField(u'Fim das férias')
     
    class Meta():
        unique_together = (('jogador', 'data_inicio'), ('jogador', 'data_fim'))
        