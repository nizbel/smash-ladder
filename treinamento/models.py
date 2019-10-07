# -*- coding: utf-8 -*-
from django.db import models

from smashLadder.utils import DateTimeFieldTz


class RegistroTreinamento(models.Model):
    inicio = DateTimeFieldTz('Data/hora de início')
    fim = DateTimeFieldTz('Data/hora de fim')
    jogador = models.ForeignKey('jogadores.Jogador', on_delete=models.CASCADE)
    
class Anotacao(models.Model):
    texto = models.CharField('Texto da anotação', max_length=250)
    jogador = models.ForeignKey('jogadores.Jogador', on_delete=models.CASCADE)
    data_hora = DateTimeFieldTz('Data/hora da anotação', auto_now_add=True)
    
class Metrica(models.Model):
    nome = models.CharField('Nome da métrica', max_length=50)
    jogador = models.ForeignKey('jogadores.Jogador', on_delete=models.CASCADE)
    descricao = models.CharField('Descrição da métrica', max_length=250, blank=True, null=True)
    
    def __str__(self):
        return self.nome
    
class ResultadoTreinamento(models.Model):
    metrica = models.ForeignKey('Metrica', on_delete=models.CASCADE)
    quantidade = models.IntegerField('Quantidade')
    registro_treinamento = models.ForeignKey('RegistroTreinamento', on_delete=models.CASCADE)
    
class LinkUtil(models.Model):
    nome = models.CharField('Nome', max_length=30)
    url = models.URLField('URL')
    jogador = models.ForeignKey('jogadores.Jogador', on_delete=models.CASCADE)
    descricao = models.CharField('Descrição do link', max_length=250, blank=True, null=True)