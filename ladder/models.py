# -*- coding: utf-8 -*-
"""Modelos usados para ladder"""
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone


class Luta(models.Model):
    """Registro de uma luta"""
    ganhador = models.ForeignKey('jogadores.Jogador', on_delete=models.CASCADE, related_name='ganhador_luta')
    stage = models.ForeignKey('jogadores.Stage', on_delete=models.CASCADE, blank=True, null=True)
    data = models.DateField(u'Data da luta')
    adicionada_por = models.ForeignKey('jogadores.Jogador', on_delete=models.CASCADE, related_name='criador_luta')
    
    @property
    def ladder(self):
        if hasattr(self, 'lutaladder'):
            return self.lutaladder.ladder
        return None

class JogadorLuta(models.Model):
    """Jogadores participantes de uma luta"""
    jogador = models.ForeignKey('jogadores.Jogador', on_delete=models.CASCADE)
    personagem = models.ForeignKey('jogadores.Personagem', on_delete=models.CASCADE, blank=True, null=True)
    luta = models.ForeignKey('Luta', on_delete=models.CASCADE)
    
    class Meta():
        unique_together = ('jogador', 'luta')
    
class RegistroLadder(models.Model):
    """Registro para ladder"""
    LIMITE_POSICOES_DESAFIO = 2 # Diferença máxima de posições para haver desafio
    PERIODO_ESPERA_MESMOS_JOGADORES = 4 # Quantidade de dias a esperar para refazer um desafio
    PERIODO_ESPERA_DESAFIO_CORINGA = 90 # Quantidade de dias a esperar para utilizar um coringa
    
    MELHOR_DE = 5 # Quantidade máxima de lutas que um registro pode ter
    SCORE_VITORIA = 3 # Score para vitória
    
    MENSAGEM_ERRO_DESAFIANTE_MUITO_ABAIXO_DESAFIADO = f'Desafiante está mais de {LIMITE_POSICOES_DESAFIO} posições abaixo do desafiado'
    MENSAGEM_ERRO_DESAFIANTE_ACIMA_DESAFIADO = 'Desafiante está à frente do desafiado'
    MENSAGEM_ERRO_DESAFIANTE_FERIAS = 'Desafiante está de férias'
    MENSAGEM_ERRO_DESAFIADO_FERIAS = 'Desafiado está de férias'
    MENSAGEM_ERRO_MESMO_JOGADOR = 'Desafiante e desafiado não podem ser o mesmo jogador'
    MENSAGEM_ERRO_PERIODO_ESPERA_MESMOS_JOGADORES = f'Desafio não respeita período mínimo de ' \
        f'{PERIODO_ESPERA_MESMOS_JOGADORES} dias entre mesmos jogadores'
    MENSAGEM_ERRO_PERIODO_ESPERA_CORINGA = f'Ainda não acabou o tempo de {PERIODO_ESPERA_DESAFIO_CORINGA} dias '\
        f'para desafiante reutilizar coringa'
    
    desafiante = models.ForeignKey('jogadores.Jogador', on_delete=models.CASCADE, related_name='desafiante')
    desafiado = models.ForeignKey('jogadores.Jogador', on_delete=models.CASCADE, related_name='desafiado')
    desafio_coringa = models.BooleanField(u'É desafio coringa?')
    score_desafiante = models.SmallIntegerField(u'Vitórias do desafiante', validators=[MinValueValidator(0), MaxValueValidator(3)])
    score_desafiado = models.SmallIntegerField(u'Vitórias do desafiado', validators=[MinValueValidator(0), MaxValueValidator(3)])
    admin_validador = models.ForeignKey('jogadores.Jogador', on_delete=models.CASCADE, blank=True, null=True, related_name='admin_validador')
    data_hora = models.DateTimeField(u'Data e hora do resultado')
    adicionado_por = models.ForeignKey('jogadores.Jogador', on_delete=models.CASCADE, related_name='criador_registro')
    
    class Meta():
        unique_together = ('desafiante', 'desafiado', 'data_hora')
    
    @property
    def lutas(self):
        """Lista de lutas que compõe o registro"""
        return [luta_ladder.luta for luta_ladder in self.lutaladder_set.all()]
    
    def is_cancelado(self):
        """Define se é um registro cancelado"""
        return hasattr(self, 'cancelamentoregistroladder')
    
    def is_historico(self):
        """Define se é histórico"""
        horario_atual = timezone.now()
        return self.data_hora.month != horario_atual.month or self.data_hora.year != horario_atual.year
        
    def is_validado(self):
        return self.admin_validador != None
    
    @property
    def mes_ano_ladder(self):
        """Retorna mes e ano de ladder da qual registro faz parte"""
        if self.is_historico():
            return (self.data_hora.month, self.data_hora.year)
        return None
    
    @property
    def ladder(self):
        if self.is_historico():
            mes, ano = self.mes_ano_ladder
            return HistoricoLadder.objects.filter(ano=ano, mes=mes)
        return PosicaoLadder.objects
    
    def desafiante_venceu(self):
        """Retorna se desafiante foi o ganhador"""
        return self.score_desafiante > self.score_desafiado
    
class LutaLadder(models.Model):
    """Lutas para um registro de ladder"""
    registro_ladder = models.ForeignKey('RegistroLadder', on_delete=models.CASCADE)
    luta = models.OneToOneField('Luta', on_delete=models.CASCADE)
    indice_registro_ladder = models.SmallIntegerField(u'Índice da luta')
    
    class Meta():
        unique_together = (('registro_ladder', 'luta'), ('registro_ladder', 'indice_registro_ladder'))
        ordering = ('indice_registro_ladder',)

class InicioLadder(models.Model):
    """Posição inicial na ladder"""
    posicao = models.SmallIntegerField(u'Posição inicial')
    jogador = models.ForeignKey('jogadores.Jogador', on_delete=models.CASCADE)
    
    class Meta():
        unique_together = ('posicao', 'jogador')
        
    def __str__(self):
        return f'{self.posicao}: {self.jogador}'

class PosicaoLadder(models.Model):
    """Posição atual na ladder"""
    posicao = models.SmallIntegerField(u'Posição atual')
    jogador = models.ForeignKey('jogadores.Jogador', on_delete=models.CASCADE)
    
    class Meta():
        unique_together = ('posicao', 'jogador')
        
    def __str__(self):
        return f'{self.posicao}: {self.jogador}'

class HistoricoLadder(models.Model):
    """Histórico para ladder"""
    MENSAGEM_LADDER_MES_ANO_INEXISTENTE = 'Não há ladder para a data informada'
    
    mes = models.SmallIntegerField(u'Mês')
    ano = models.SmallIntegerField(u'Ano')
    posicao = models.SmallIntegerField(u'Posição no mês')
    jogador = models.ForeignKey('jogadores.Jogador', on_delete=models.CASCADE)
    
    class Meta():
        unique_together = (('jogador', 'mes', 'ano'), ('posicao', 'mes', 'ano'))
    
class CancelamentoRegistroLadder(models.Model):
    """Cancelamento (exclusão lógica) de registros de ladder"""
    registro_ladder = models.OneToOneField('RegistroLadder', on_delete=models.CASCADE)
    data_hora = models.DateTimeField(u'Data/hora da exclusão', auto_now_add=True)
    jogador = models.ForeignKey('jogadores.Jogador', on_delete=models.CASCADE)
    