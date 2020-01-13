# -*- coding: utf-8 -*-
from django.contrib.auth.models import User
from django.db import models

from smashLadder.utils import DateTimeFieldTz


class PerformanceRequisicao(models.Model):
    data_hora_requisicao = DateTimeFieldTz('Data/hora da requisição')
    data_hora_resposta = DateTimeFieldTz('Data/hora da resposta')
    url = models.CharField('URL', max_length=255)
    user = models.ForeignKey(User, blank=True, null=True, on_delete=models.SET_NULL)