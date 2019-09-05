# -*- coding: utf-8 -*-
from django.db import models

from smashLadder.utils import DateTimeFieldTz


class PerformanceRequisicao(models.Model):
    data_hora_requisicao = DateTimeFieldTz('Data/hora da requisição')
    data_hora_resposta = DateTimeFieldTz('Data/hora da resposta')
    jogador = models.ForeignKey('jogadores.Jogador', blank=True, null=True, on_delete=models.CASCADE)
    url = models.CharField('URL', max_length=255)