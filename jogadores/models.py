# -*- coding: utf-8 -*-
"""Modelos usados para guardar jogadores"""
from django.contrib.auth.models import User
from django.db import models
from django.db.models.aggregates import Sum, Max
from django.utils import timezone

from ladder.models import DesafioLadder, InicioLadder, ResultadoDesafioLadder,\
    HistoricoLadder


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
        
    def is_de_ferias(self):
        """Verifica se jogador está de férias"""
        return self.de_ferias_na_data(timezone.now().date())
        
    def de_ferias_na_data(self, data):
        """Verifica se jogador está de férias na data apontada"""
        return RegistroFerias.objects.filter(jogador=self, data_inicio__lte=data, data_fim__gte=data).exists()
    
    def pode_usar_coringa_na_data(self, data):
        return self.ultimo_uso_coringa == None or \
            (data - self.ultimo_uso_coringa).days >= DesafioLadder.PERIODO_ESPERA_DESAFIO_CORINGA
            
    def posicao_em(self, data_hora):
        """Retora a posição do jogador na ladder na data/hora especificada"""
        # Buscar último desafio participado
        desafio_mais_recente = None
        
        if DesafioLadder.validados.filter(desafiante=self, data_hora__lt=data_hora).exists():
            ultimo_desafiante = DesafioLadder.validados.filter(desafiante=self, data_hora__lt=data_hora).order_by('-data_hora')[0]
            desafio_mais_recente = ultimo_desafiante
            # Se ganhou, pega posição do desafiado
            if desafio_mais_recente.score_desafiante > desafio_mais_recente.score_desafiado:
                desafio_mais_recente.posicao = desafio_mais_recente.posicao_desafiado
            else:
                desafio_mais_recente.posicao = desafio_mais_recente.posicao_desafiante
                
        if DesafioLadder.validados.filter(desafiado=self, data_hora__lt=data_hora).exists():
            ultimo_desafiado = DesafioLadder.validados.filter(desafiado=self, data_hora__lt=data_hora).order_by('-data_hora')[0]
            if desafio_mais_recente == None or desafio_mais_recente.data_hora < ultimo_desafiado.data_hora:
                desafio_mais_recente = ultimo_desafiado
                
                # Se ganhou, mantém posição
                if desafio_mais_recente.score_desafiado > desafio_mais_recente.score_desafiante:
                    desafio_mais_recente.posicao = desafio_mais_recente.posicao_desafiado
                else:
                    desafio_mais_recente.posicao = desafio_mais_recente.posicao_desafiado + 1
        
        if desafio_mais_recente:
#             print(f'Desafio mais recente de {self}: {desafio_mais_recente.id} com {desafio_mais_recente.desafiante} VS {desafio_mais_recente.desafiado}')
            posicao = desafio_mais_recente.posicao
            
#             print(self, ResultadoDesafioLadder.objects.filter(jogador=self, desafio_ladder__data_hora__range=[desafio_mais_recente.data_hora, data_hora]) \
#                 .exclude(desafio_ladder=desafio_mais_recente).exclude(desafio_ladder__data_hora=data_hora) \
#                 .aggregate(alteracao_total=Sum('alteracao_posicao'))['alteracao_total'] or 0)
            
            # Buscar alterações feitas por desafios de outros jogadores
            posicao += (ResultadoDesafioLadder.objects.filter(jogador=self, desafio_ladder__data_hora__range=[desafio_mais_recente.data_hora, data_hora]) \
                .exclude(desafio_ladder=desafio_mais_recente).exclude(desafio_ladder__data_hora=data_hora) \
                .aggregate(alteracao_total=Sum('alteracao_posicao'))['alteracao_total'] or 0)
            
            return posicao
        
        # Se não houver desafios cadastrados, verificar última ladder
        # Definir ultima ladder
        mes = data_hora.month
        ano = data_hora.year
        mes -= 1
        if mes == 0:
            mes = 12
            ano -= 1
            
        if HistoricoLadder.objects.filter(ano=ano, mes=mes).exists():
            ultima_ladder = HistoricoLadder.objects.filter(ano=ano, mes=mes)
        else:
            ultima_ladder = InicioLadder.objects.all()  
            
        if ultima_ladder.filter(jogador=self).exists():
            posicao = ultima_ladder.get(jogador=self).posicao
#             print('ULTIMA LADDER:', posicao)
            
#             print(self, ResultadoDesafioLadder.objects.filter(jogador=self, desafio_ladder__data_hora__lt=data_hora) \
#                 .aggregate(alteracao_total=Sum('alteracao_posicao'))['alteracao_total'] or 0)
            
            # Buscar alterações feitas por desafios de outros jogadores
            if HistoricoLadder.objects.filter(ano=ano, mes=mes).exists():
                posicao += (ResultadoDesafioLadder.objects.filter(jogador=self, desafio_ladder__data_hora__lt=data_hora) \
                    .filter(desafio_ladder__data_hora__month=data_hora.month, desafio_ladder__data_hora__year=data_hora.year) \
                    .aggregate(alteracao_total=Sum('alteracao_posicao'))['alteracao_total'] or 0)
            else:
                posicao += (ResultadoDesafioLadder.objects.filter(jogador=self, desafio_ladder__data_hora__lt=data_hora) \
                    .aggregate(alteracao_total=Sum('alteracao_posicao'))['alteracao_total'] or 0)
                
            return posicao
        
        # TODO Decidir qual posição retornar caso seja novo entrante
#         # Definir ultima ladder
#         mes = data_hora.month
#         ano = data_hora.year
#         mes -= 1
#         if mes == 0:
#             mes = 12
#             ano -= 1
#         if HistoricoLadder.objects.filter(ano=ano, mes=mes).exists():
#             ultima_ladder = HistoricoLadder.objects.filter(ano=ano, mes=mes)
#         else:
#             ultima_ladder = InicioLadder.objects.all()    
        
        return 0
        
#         print('ULTIMA POSICAO', DesafioLadder.validados.filter(data_hora__lt=data_hora).exclude(desafiante=self) \
#             .aggregate(ultima_posicao=Max('posicao_desafiante'))['ultima_posicao'], 
#             ultima_ladder.aggregate(ultima_posicao=Max('posicao'))['ultima_posicao'])
#         return max(DesafioLadder.validados.filter(data_hora__lt=data_hora).exclude(desafiante=self) \
#             .aggregate(ultima_posicao=Max('posicao_desafiante'))['ultima_posicao'], 
#             ultima_ladder.aggregate(ultima_posicao=Max('posicao'))['ultima_posicao']) + 1

class Personagem(models.Model):
    """Personagens disponíveis no jogo"""
    nome = models.CharField(u'Nome', max_length=30)
    icone = models.CharField(u'Ícone', max_length=50)
    
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
    
    TIPO_NORMAL_DESCRICAO = 'Padrão'
    TIPO_BATTLEFIELD_DESCRICAO = 'BF'
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
    
    @property
    def valida_para_ladder(self):
        return hasattr(self, 'stagevalidaladder')
    
class StageValidaLadder(models.Model):
    """Estágios válidos para desafios de ladder"""
    stage = models.OneToOneField('Stage', on_delete=models.CASCADE)

class RegistroFerias(models.Model):
    """Registro de férias de jogador"""
    PERIODO_MAX_FERIAS = 30
    
    jogador = models.ForeignKey('Jogador', on_delete=models.CASCADE)
    data_inicio = models.DateField(u'Início das férias')
    data_fim = models.DateField(u'Fim das férias')
     
    class Meta():
        verbose_name_plural = 'registros de férias'
        unique_together = (('jogador', 'data_inicio'), ('jogador', 'data_fim'))
        