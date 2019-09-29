# -*- coding: utf-8 -*-
"""Modelos usados para ladder"""
import datetime

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone

from configuracao.models import ConfiguracaoLadder
from smashLadder.utils import DateTimeFieldTz


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
    
class DesafioLadder(models.Model):
    """Desafio para ladder"""
    LIMITE_POSICOES_DESAFIO = ConfiguracaoLadder.buscar_configuracao([ConfiguracaoLadder.CONFIGURACAO_LIMITE_POSICOES_DESAFIO,]) \
            [ConfiguracaoLadder.CONFIGURACAO_LIMITE_POSICOES_DESAFIO] # Diferença máxima de posições para haver desafio
    PERIODO_ESPERA_MESMOS_JOGADORES = 3 # Quantidade de dias a esperar para refazer um desafio
    PERIODO_ESPERA_DESAFIO_CORINGA = 60 # Quantidade de dias a esperar para utilizar um coringa
    
    MELHOR_DE = 5 # Quantidade máxima de lutas que um desafio pode ter
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
    score_desafiante = models.SmallIntegerField(u'Vitórias do desafiante', validators=[MinValueValidator(0), MaxValueValidator(SCORE_VITORIA)])
    score_desafiado = models.SmallIntegerField(u'Vitórias do desafiado', validators=[MinValueValidator(0), MaxValueValidator(SCORE_VITORIA)])
    admin_validador = models.ForeignKey('jogadores.Jogador', on_delete=models.CASCADE, blank=True, null=True, related_name='admin_validador')
    data_hora = DateTimeFieldTz(u'Data e hora do resultado')
    adicionado_por = models.ForeignKey('jogadores.Jogador', on_delete=models.CASCADE, related_name='criador_desafio')
    posicao_desafiante = models.SmallIntegerField(u'Posição do desafiante', default=0)
    posicao_desafiado = models.SmallIntegerField(u'Posição do desafiado', default=0)
    
    class Meta():
        unique_together = (('desafiante', 'data_hora'), ('desafiado', 'data_hora'))
    
    @staticmethod
    def alterar_limite_posicoes_desafio():
        DesafioLadder.LIMITE_POSICOES_DESAFIO = ConfiguracaoLadder.buscar_configuracao([ConfiguracaoLadder.CONFIGURACAO_LIMITE_POSICOES_DESAFIO,]) \
            [ConfiguracaoLadder.CONFIGURACAO_LIMITE_POSICOES_DESAFIO]
        
        # Atualizar mensagem
        DesafioLadder.MENSAGEM_ERRO_DESAFIANTE_MUITO_ABAIXO_DESAFIADO = f'Desafiante está mais de {DesafioLadder.LIMITE_POSICOES_DESAFIO} ' \
            'posições abaixo do desafiado'
            
    @property
    def lutas(self):
        """Lista de lutas que compõe o desafio"""
        return [luta_ladder.luta for luta_ladder in self.lutaladder_set.all().select_related('luta__ganhador')]
    
    def is_cancelado(self):
        """Define se é um desafio cancelado"""
        return hasattr(self, 'cancelamentodesafioladder')
    
    def is_historico(self):
        """Define se é histórico"""
        horario_atual = timezone.localtime()
        return self.data_hora.month != horario_atual.month or self.data_hora.year != horario_atual.year
        
    def is_validado(self):
        return self.admin_validador_id != None
    
    @property
    def mes_ano_ladder(self):
        """Retorna mes e ano de ladder da qual desafio faz parte"""
        if self.is_historico():
            return (self.data_hora.month, self.data_hora.year)
        return (None, None)
    
    @property
    def ladder(self):
        """Ladder a qual desafio se refere"""
        if self.is_historico():
            mes, ano = self.mes_ano_ladder
            return HistoricoLadder.objects.filter(ano=ano, mes=mes)
        return PosicaoLadder.objects
    
    def cancelavel_por_jogador(self, jogador):
        """Determina se jogador pode cancelar desafio"""
        if self.is_cancelado():
            return False
        # Admin sempre pode cancelar, criador apenas se não validado
        return jogador.admin or (not self.is_validado() and jogador == self.adicionado_por)
    
    def editavel_por_jogador(self, jogador):
        """Determinar se jogador pode editar desafio"""
        if self.is_cancelado():
            return False
        # Contanto que não esteja validado, jogador precisa ser admin ou criador
        return not self.is_validado() and (jogador.admin or jogador == self.adicionado_por)
    
    def desafiante_venceu(self):
        """Retorna se desafiante foi o ganhador"""
        return self.score_desafiante > self.score_desafiado
    
    # Managers
    class DesafiosValidadosManager(models.Manager):
        """Queryset para trazer desafios validados e não cancelados"""
        def get_queryset(self):
            return super().get_queryset().filter(cancelamentodesafioladder__isnull=True, admin_validador__isnull=False)
        
    objects = models.Manager()
    validados = DesafiosValidadosManager()
    
class LutaLadder(models.Model):
    """Lutas para um desafio de ladder"""
    desafio_ladder = models.ForeignKey('DesafioLadder', on_delete=models.CASCADE)
    luta = models.OneToOneField('Luta', on_delete=models.CASCADE)
    indice_desafio_ladder = models.SmallIntegerField(u'Índice da luta')
    
    class Meta():
        unique_together = (('desafio_ladder', 'luta'), ('desafio_ladder', 'indice_desafio_ladder'))
        ordering = ('indice_desafio_ladder',)

class InicioLadder(models.Model):
    """Posição inicial na ladder"""
    posicao = models.SmallIntegerField(u'Posição inicial')
    jogador = models.ForeignKey('jogadores.Jogador', on_delete=models.CASCADE)
    
    class Meta():
        unique_together = (('posicao',), ('jogador',))
        
    def __str__(self):
        return f'{self.posicao}: {self.jogador}'

class PosicaoLadder(models.Model):
    """Posição atual na ladder"""
    posicao = models.SmallIntegerField(u'Posição atual')
    jogador = models.ForeignKey('jogadores.Jogador', on_delete=models.CASCADE)
    
    class Meta():
        unique_together = (('posicao',), ('jogador',))
        
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
        
    def __str__(self):
        return f'{self.posicao}: {self.jogador}'
    
class CancelamentoDesafioLadder(models.Model):
    """Cancelamento (exclusão lógica) de desafios de ladder"""
    desafio_ladder = models.OneToOneField('DesafioLadder', on_delete=models.CASCADE)
    data_hora = models.DateTimeField(u'Data/hora da exclusão', auto_now_add=True)
    jogador = models.ForeignKey('jogadores.Jogador', on_delete=models.CASCADE)
    
class ResultadoDesafioLadder(models.Model):
    """Resultado de um desafio de ladder"""
    desafio_ladder = models.ForeignKey('DesafioLadder', on_delete=models.CASCADE)
    jogador = models.ForeignKey('jogadores.Jogador', on_delete=models.CASCADE)
    alteracao_posicao = models.SmallIntegerField(u'Alteração na posição após desafio')
    
    class Meta():
        unique_together = ('desafio_ladder', 'jogador')
        
class RemocaoJogador(models.Model):
    """Registro de remoção de jogador da ladder"""
    jogador = models.ForeignKey('jogadores.Jogador', on_delete=models.CASCADE)
    # Adicionado como datetime para facilitar comparações na hora de calcular ladder
    data = DateTimeFieldTz('Data da remoção')
    admin_removedor = models.ForeignKey('jogadores.Jogador', on_delete=models.CASCADE, related_name='admin_removedor')
    posicao_jogador = models.SmallIntegerField('Posição durante remoção')
    remocao_por_inatividade = models.BooleanField('Remoção devido a inatividade?', default=False)
    
    class Meta():
        unique_together = ('jogador', 'data')
        
    def __str__(self):
        return f'{self.jogador}: {self.data}'
    
    def is_historico(self):
        """Define se é histórico"""
        horario_atual = timezone.localtime()
        return self.data.month != horario_atual.month or self.data.year != horario_atual.year
    
    @property
    def mes_ano_ladder(self):
        """Retorna mes e ano de ladder da qual remoção faz parte"""
        if self.is_historico():
            return (self.data.month, self.data.year)
        return (None, None)
    
class ResultadoRemocaoJogador(models.Model):
    """Resultado de um desafio de ladder"""
    remocao = models.ForeignKey('RemocaoJogador', on_delete=models.CASCADE)
    jogador = models.ForeignKey('jogadores.Jogador', on_delete=models.CASCADE)
    alteracao_posicao = models.SmallIntegerField(u'Alteração na posição após remoção')
    
    class Meta():
        unique_together = ('remocao', 'jogador')
    
class DecaimentoJogador(models.Model):
    """Registro de decaimento de jogador na ladder"""
    PERIODO_INATIVIDADE = 30 # Quantidade de dias inativo para decair
    QTD_POSICOES_DECAIMENTO = 3 # Quantidade de posições a decair por vez
    
    jogador = models.ForeignKey('jogadores.Jogador', on_delete=models.CASCADE)
    # Adicionado como datetime para facilitar comparações na hora de calcular ladder
    data = DateTimeFieldTz('Data do decaimento')
    posicao_inicial = models.SmallIntegerField('Posição da qual jogador caiu')
    qtd_periodos_inatividade = models.SmallIntegerField('Quantidade de períodos inativo', validators=[MinValueValidator(1), MaxValueValidator(2)])
    
    class Meta():
        unique_together = ('jogador', 'data')
        
    def __str__(self):
        
        return f'{self.jogador} cai de {self.posicao_inicial} em {self.data.strftime("%d/%m/%Y")}'
    
    def is_historico(self):
        """Define se é histórico"""
        horario_atual = timezone.localtime()
        return self.data.month != horario_atual.month or self.data.year != horario_atual.year
    
    @property
    def mes_ano_ladder(self):
        """Retorna mes e ano de ladder da qual remoção faz parte"""
        if self.is_historico():
            return (self.data.month, self.data.year)
        return (None, None)
    
class ResultadoDecaimentoJogador(models.Model):
    """Resultado de um desafio de ladder"""
    decaimento = models.ForeignKey('DecaimentoJogador', on_delete=models.CASCADE)
    jogador = models.ForeignKey('jogadores.Jogador', on_delete=models.CASCADE)
    alteracao_posicao = models.SmallIntegerField(u'Alteração na posição após decaimento')
    
    class Meta():
        unique_together = ('decaimento', 'jogador')
    
class PermissaoAumentoRange(models.Model):
    """Registro de permissão para aumentar range de desafio caso os desafiáveis não estejam presentes"""
    # Período de validade da permissão, em horas
    PERIODO_VALIDADE = 2
    AUMENTO_RANGE = 3
    
    MENSAGEM_SUCESSO_PERMISSAO_AUMENTO_RANGE = 'Permissão de aumento de range concedida com sucesso'
    MENSAGEM_ERRO_JOGADOR_IGUAL_ADMIN = 'Usuário não pode conceder permissão a si mesmo'
    MENSAGEM_ERRO_JOGADOR_JA_POSSUI_PERMISSAO_VALIDA = 'Jogador já possui permissão válida'    
    MENSAGEM_ERRO_DESAFIANTE_MUITO_ABAIXO_DESAFIADO = f'Desafiante está mais de ' \
        f'{AUMENTO_RANGE + DesafioLadder.LIMITE_POSICOES_DESAFIO} posições abaixo do desafiado'
    MENSAGEM_SUCESSO_REMOCAO_PERMISSAO = 'Permissão de aumento de range removida com sucesso'
    MENSAGEM_ERRO_DESAFIO_UTILIZANDO_PERMISSAO = 'Já existe um desafio válido utilizando a permissão'
    
    jogador = models.ForeignKey('jogadores.Jogador', on_delete=models.CASCADE, related_name='permitido_aumento_range')
    admin_permissor = models.ForeignKey('jogadores.Jogador', on_delete=models.CASCADE, related_name='permissor_aumento_range')
    data_hora = DateTimeFieldTz(u'Data e hora da permissão')
    
    def is_valida(self, data_hora=None):
        """Define se permissão é válida na data/hora"""
        if not data_hora:
            data_hora = timezone.localtime()
        valida = (self.data_hora + datetime.timedelta(hours=self.PERIODO_VALIDADE) >= data_hora)
        if valida:
            valida = (not DesafioLadder.validados.filter(desafiante=self.jogador, data_hora__gte=self.data_hora, 
                                                                    data_hora__lt=data_hora).exists())
            
        return valida
        