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
    try:
        LIMITE_POSICOES_DESAFIO = ConfiguracaoLadder.buscar_configuracao([ConfiguracaoLadder.CONFIGURACAO_LIMITE_POSICOES_DESAFIO,]) \
            [ConfiguracaoLadder.CONFIGURACAO_LIMITE_POSICOES_DESAFIO] # Diferença máxima de posições para haver desafio
    except:
        LIMITE_POSICOES_DESAFIO = 3
    
    # É permitido usar coringa na Ladder?
    try:
        USO_CORINGA = ConfiguracaoLadder.buscar_configuracao([ConfiguracaoLadder.CONFIGURACAO_USO_CORINGA,]) \
            [ConfiguracaoLadder.CONFIGURACAO_USO_CORINGA] # Diferença máxima de posições para haver desafio
    except:
        USO_CORINGA = True
    PERIODO_ESPERA_MESMOS_JOGADORES = 3 # Quantidade de dias a esperar para refazer um desafio
    PERIODO_ESPERA_DESAFIO_CORINGA = 60 # Quantidade de dias a esperar para utilizar um coringa
    
    try:
        MELHOR_DE = ConfiguracaoLadder.buscar_configuracao([ConfiguracaoLadder.CONFIGURACAO_MELHOR_DE,]) \
            [ConfiguracaoLadder.CONFIGURACAO_MELHOR_DE] # Quantidade máxima de lutas que um desafio pode ter
    except:
        MELHOR_DE = 3
    SCORE_VITORIA = ((MELHOR_DE // 2) + 1) # Score para vitória
    
    MENSAGEM_ERRO_DESAFIANTE_MUITO_ABAIXO_DESAFIADO = f'Desafiante está mais de {LIMITE_POSICOES_DESAFIO} posições abaixo do desafiado'
    MENSAGEM_ERRO_DESAFIANTE_ACIMA_DESAFIADO = 'Desafiante está à frente do desafiado'
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
        ordering = ('data_hora',)
        
    def __str__(self):
        return f'{self.id}: {self.data_hora}'
    
    @staticmethod
    def alterar_limite_posicoes_desafio():
        DesafioLadder.LIMITE_POSICOES_DESAFIO = ConfiguracaoLadder.buscar_configuracao([ConfiguracaoLadder.CONFIGURACAO_LIMITE_POSICOES_DESAFIO,]) \
            [ConfiguracaoLadder.CONFIGURACAO_LIMITE_POSICOES_DESAFIO]
        
        # Atualizar mensagem
        DesafioLadder.MENSAGEM_ERRO_DESAFIANTE_MUITO_ABAIXO_DESAFIADO = f'Desafiante está mais de {DesafioLadder.LIMITE_POSICOES_DESAFIO} ' \
            'posições abaixo do desafiado'
            
    @staticmethod
    def alterar_melhor_de():
        DesafioLadder.MELHOR_DE = ConfiguracaoLadder.buscar_configuracao([ConfiguracaoLadder.CONFIGURACAO_MELHOR_DE,]) \
            [ConfiguracaoLadder.CONFIGURACAO_MELHOR_DE]
        
        DesafioLadder.SCORE_VITORIA = ((DesafioLadder.MELHOR_DE // 2) + 1)
        
    @staticmethod
    def alterar_uso_coringa():
        DesafioLadder.USO_CORINGA = ConfiguracaoLadder.buscar_configuracao([ConfiguracaoLadder.CONFIGURACAO_USO_CORINGA,]) \
            [ConfiguracaoLadder.CONFIGURACAO_USO_CORINGA]
        
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
    
    def fora_da_season(self):
        """Retorna se desafio é de Season anterior"""
        season_atual = Season.objects.order_by('-data_inicio')[0]
        return self.data_hora < season_atual.data_hora_inicio
    
    class DesafioLadderManager(models.Manager):
        """Override do manager padrão"""
        def na_season(self, season):
            data_hora_inicio = datetime.datetime(season.data_inicio.year, season.data_inicio.month, season.data_inicio.day)
            
            # Se possui data de fim
            if season.data_fim:
                data_hora_fim = datetime.datetime(season.data_fim.year, season.data_fim.month, season.data_fim.day) \
                    + datetime.timedelta(days=1)
                return self.get_queryset().filter(data_hora__range=[timezone.make_aware(data_hora_inicio), 
                                                                timezone.make_aware(data_hora_fim, 
                                                                                    timezone.get_current_timezone())])
            else:
                # Se não, buscar apenas a partir da data inicial
                return self.get_queryset().filter(data_hora__gte=timezone.make_aware(data_hora_inicio))
    # Managers
    class DesafiosValidadosManager(models.Manager):
        """Manager para trazer desafios validados e não cancelados"""
        def get_queryset(self):
            return super().get_queryset().filter(cancelamentodesafioladder__isnull=True, admin_validador__isnull=False)
        
        def na_season(self, season):
            # Se possui data de fim
            if season.data_fim:
                data_hora_fim = datetime.datetime(season.data_fim.year, season.data_fim.month, season.data_fim.day) \
                    + datetime.timedelta(days=1)
                return self.get_queryset().filter(data_hora__range=[season.data_hora_inicio, 
                                                                timezone.make_aware(data_hora_fim)])
            else:
                # Se não, buscar apenas a partir da data inicial
                return self.get_queryset().filter(data_hora__gte=season.data_hora_inicio)
        
#     objects = models.Manager()
    objects = DesafioLadderManager()
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
    # Quantidade de dias inativo para decair
    try:
        PERIODO_INATIVIDADE = ConfiguracaoLadder.buscar_configuracao([ConfiguracaoLadder.CONFIGURACAO_PERIODO_INATIVIDADE,]) \
            [ConfiguracaoLadder.CONFIGURACAO_PERIODO_INATIVIDADE]
    except:
        PERIODO_INATIVIDADE = 30
        
    QTD_POSICOES_DECAIMENTO = 3 # Quantidade de posições a decair por vez
    
    # Permitir que primeiro decaimento seja perdoado?
    try:
        ABONAR_PRIMEIRO_DECAIMENTO = ConfiguracaoLadder.buscar_configuracao([ConfiguracaoLadder.CONFIGURACAO_ABONAR_PRIMEIRO_DECAIMENTO,]) \
            [ConfiguracaoLadder.CONFIGURACAO_ABONAR_PRIMEIRO_DECAIMENTO]
    except:
        ABONAR_PRIMEIRO_DECAIMENTO = False
    
    jogador = models.ForeignKey('jogadores.Jogador', on_delete=models.CASCADE)
    # Adicionado como datetime para facilitar comparações na hora de calcular ladder
    data = DateTimeFieldTz('Data do decaimento')
    posicao_inicial = models.SmallIntegerField('Posição da qual jogador caiu')
    qtd_periodos_inatividade = models.SmallIntegerField('Quantidade de períodos inativo', validators=[MinValueValidator(1), MaxValueValidator(2)])
    
    class Meta():
        unique_together = ('jogador', 'data')
        
    def __str__(self):
        return f'{self.jogador} cai de {self.posicao_inicial} em {self.data.strftime("%d/%m/%Y")}'
    
    @staticmethod
    def alterar_periodo_inatividade():
        DecaimentoJogador.PERIODO_INATIVIDADE = ConfiguracaoLadder.buscar_configuracao([ConfiguracaoLadder.CONFIGURACAO_PERIODO_INATIVIDADE,]) \
            [ConfiguracaoLadder.CONFIGURACAO_PERIODO_INATIVIDADE]
            
    @staticmethod
    def alterar_abonar_primeiro_decaimento():
        DecaimentoJogador.ABONAR_PRIMEIRO_DECAIMENTO = ConfiguracaoLadder \
            .buscar_configuracao([ConfiguracaoLadder.CONFIGURACAO_ABONAR_PRIMEIRO_DECAIMENTO,]) \
            [ConfiguracaoLadder.CONFIGURACAO_ABONAR_PRIMEIRO_DECAIMENTO]
    
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
    
class Season(models.Model):
    """Registro de Season"""
    # Guarda mês/dia para começar novas seasons
    try:
        PERIODO_SEASON = ConfiguracaoLadder.buscar_configuracao([ConfiguracaoLadder.CONFIGURACAO_PERIODO_SEASON,]) \
            [ConfiguracaoLadder.CONFIGURACAO_PERIODO_SEASON]
    except:
        PERIODO_SEASON = ConfiguracaoLadder.VALOR_SEASON_INDETERMINADO
        
    ano = models.SmallIntegerField('Ano')
    indice = models.SmallIntegerField('Índice da Season')
    data_inicio = models.DateField('Data de início')
    data_fim = models.DateField('Data de fim', blank=True, null=True)
    
    class Meta():
        unique_together = (('ano', 'indice'), ('data_inicio',), ('data_fim',))
    
    def __str__(self):
        return f'Season {self.indice}/{self.ano}'
    
    @property
    def data_hora_inicio(self):
        data_hora_inicio = datetime.datetime(self.data_inicio.year, self.data_inicio.month, self.data_inicio.day)
        return timezone.make_aware(data_hora_inicio)
    
    @staticmethod
    def alterar_periodo_season():
        Season.PERIODO_SEASON = ConfiguracaoLadder.buscar_configuracao([ConfiguracaoLadder.CONFIGURACAO_PERIODO_SEASON,]) \
            [ConfiguracaoLadder.CONFIGURACAO_PERIODO_SEASON]
        
class SeasonPosicaoInicial(models.Model):
    """Posições da Ladder ao iniciar a Season"""
    season = models.ForeignKey('Season', on_delete=models.CASCADE, related_name='season_posicao_inicial')
    jogador = models.ForeignKey('jogadores.Jogador', on_delete=models.CASCADE)
    posicao = models.SmallIntegerField('Posição inicial')
    
    class Meta():
        unique_together = (('posicao', 'season'), ('jogador', 'season'))
        
    def __str__(self):
        return f'{self.season}, {self.posicao}: {self.jogador}'
    
class SeasonPosicaoFinal(models.Model):
    """Posições da Ladder ao finalizar a Season"""
    season = models.ForeignKey('Season', null=True, blank=True, on_delete=models.CASCADE, related_name='season_posicao_final')
    jogador = models.ForeignKey('jogadores.Jogador', on_delete=models.CASCADE)
    posicao = models.SmallIntegerField('Posição final')
    
    class Meta():
        unique_together = (('posicao', 'season'), ('jogador', 'season'))
        
    def __str__(self):
        return f'{self.season}, {self.posicao}: {self.jogador}'
    
class Lockdown(models.Model):
    """Registro de trava para site enquanto nova season é gerada"""
    valido = models.BooleanField('Lockdown válido?', default=False)
    
    @staticmethod
    def sistema_em_lockdown():
        lockdown, _ = Lockdown.objects.get_or_create(id=1)
        return lockdown.valido
    
    @staticmethod
    def buscar():
        return Lockdown.objects.get_or_create(id=1)[0]
        