# -*- coding: utf-8 -*-
from django.contrib.auth.models import User
from django.db import models

from smashLadder.utils import DateTimeFieldTz


class ConfiguracaoLadder(models.Model):
    CONFIGURACAO_LIMITE_POSICOES_DESAFIO = 'limite_posicoes_desafio'
    
    # Altera DesafioLadder.LIMITE_POSICOES_DESAFIO
    limite_posicoes_desafio = models.SmallIntegerField('Limite de posições para desafiar')
    
    def __str__(self):
        return 'Configurações de Ladder'
    
    @staticmethod
    def buscar_configuracao(lista_configuracoes):
        try:
            return ConfiguracaoLadder.objects.all().values(*lista_configuracoes)[0]
        except IndexError:
            # Se não existir configurações, gerar padrão
            config = ConfiguracaoLadder(
                limite_posicoes_desafio=3
                )
            config.save()
            
            return ConfiguracaoLadder.objects.all().values(*lista_configuracoes)[0]

class HistoricoConfiguracaoLadder(models.Model):
    limite_posicoes_desafio = models.SmallIntegerField('Limite de posições para desafiar', blank=True, null=True)
    # Guardar responsável pela alteração
    responsavel = models.ForeignKey(User, blank=True, null=True, on_delete=models.CASCADE, related_name='responsavel_alteracao')
    data_hora = DateTimeFieldTz(u'Data e hora do resultado', auto_now_add=True)
    