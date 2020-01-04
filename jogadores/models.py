# -*- coding: utf-8 -*-
"""Modelos usados para guardar jogadores"""
import datetime

from django.contrib.auth.models import User, Group
from django.db import models
from django.db.models.aggregates import Sum
from django.db.models.expressions import Case, When, F
from django.db.models.query_utils import Q
from django.db.models.signals import post_save
from django.utils import timezone

from ladder.models import DesafioLadder, InicioLadder, ResultadoDesafioLadder, \
    HistoricoLadder, RemocaoJogador, ResultadoDecaimentoJogador, \
    ResultadoRemocaoJogador, PermissaoAumentoRange, Season
from smashLadder.utils import DateTimeFieldTz, mes_ano_ant


class Jogador(models.Model):
    """Informações do jogador"""
    nick = models.CharField(u'Tag', max_length=30)
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
    
    def pode_usar_coringa_na_data(self, data):
        return self.ultimo_uso_coringa == None or \
            (data - self.ultimo_uso_coringa).days >= DesafioLadder.PERIODO_ESPERA_DESAFIO_CORINGA
            
    def posicao_em(self, data_hora):
        """Retora a posição do jogador na ladder na data/hora especificada"""
        # Verificar Season para data/hora
        season = Season.objects.filter(data_inicio__lte=data_hora.date()).order_by('-data_inicio')[0]
        
        # Buscar última remoção da ladder, posição será definida a partir de sua data
        if RemocaoJogador.objects.filter(jogador=self, data__lt=data_hora, data__gte=season.data_hora_inicio).exists():
            data_inicial = RemocaoJogador.objects.filter(jogador=self).order_by('-data')[0].data
            desafios_validados_considerando_remocao = DesafioLadder.validados.na_season(season).filter(data_hora__gt=data_inicial)
        else:
            data_inicial = None
            desafios_validados_considerando_remocao = DesafioLadder.validados.na_season(season)
        
        # Buscar último desafio participado
        desafio_mais_recente = None
        
        if desafios_validados_considerando_remocao.filter(data_hora__lt=data_hora).filter(Q(desafiante=self) | Q(desafiado=self)).exists():
            desafio_mais_recente = desafios_validados_considerando_remocao.filter(data_hora__lt=data_hora) \
                .filter(Q(desafiante=self) | Q(desafiado=self)).annotate(
                    posicao=Case(When(Q(desafiante=self) & Q(score_desafiante__gt=F('score_desafiado')), then=F('posicao_desafiado')),
                                 When(Q(desafiante=self) & Q(score_desafiante__lt=F('score_desafiado')), then=F('posicao_desafiante')),
                                 When(Q(desafiado=self) & Q(score_desafiante__gt=F('score_desafiado')), then=F('posicao_desafiado') + 1),
                                 When(Q(desafiado=self) & Q(score_desafiante__lt=F('score_desafiado')), then=F('posicao_desafiado')))) \
                                 .order_by('-data_hora')[0]
                
        if desafio_mais_recente:
#             print(f'Desafio mais recente de {self}: {desafio_mais_recente.id} com {desafio_mais_recente.desafiante} VS {desafio_mais_recente.desafiado}')
            posicao = desafio_mais_recente.posicao

            # Buscar alterações feitas por remoções de outros jogadores
            posicao += (ResultadoRemocaoJogador.objects.filter(remocao__data__range=[desafio_mais_recente.data_hora, data_hora], jogador=self) \
                .exclude(remocao__data=data_hora).aggregate(alteracao_total=Sum('alteracao_posicao'))['alteracao_total'] or 0)
            
#             print(self, ResultadoDesafioLadder.objects.filter(jogador=self, desafio_ladder__data_hora__range=[desafio_mais_recente.data_hora, data_hora]) \
#                 .exclude(desafio_ladder=desafio_mais_recente).exclude(desafio_ladder__data_hora=data_hora) \
#                 .aggregate(alteracao_total=Sum('alteracao_posicao'))['alteracao_total'] or 0)
            
            # Buscar alterações feitas por desafios de outros jogadores
            posicao += (ResultadoDesafioLadder.objects.filter(jogador=self, desafio_ladder__data_hora__range=[desafio_mais_recente.data_hora, data_hora]) \
                .filter(desafio_ladder__admin_validador__isnull=False, desafio_ladder__cancelamentodesafioladder__isnull=True) \
                .exclude(desafio_ladder=desafio_mais_recente).exclude(desafio_ladder__data_hora=data_hora) \
                .aggregate(alteracao_total=Sum('alteracao_posicao'))['alteracao_total'] or 0)
            
            # Buscar alterações feitas por decaimentos de outros jogadores
            posicao += (ResultadoDecaimentoJogador.objects.filter(jogador=self, decaimento__data__range=[desafio_mais_recente.data_hora, data_hora]) \
                .exclude(decaimento__data=data_hora) \
                .aggregate(alteracao_total=Sum('alteracao_posicao'))['alteracao_total'] or 0)
            
            return posicao
        
        # Se não houver desafios cadastrados, verificar última ladder
        # Definir ultima ladder
        mes, ano = mes_ano_ant(data_hora.month, data_hora.year)
        
        if HistoricoLadder.objects.filter(ano=ano, mes=mes).exists():
            # Se houver remoção e ela ocorrer no mês atual, ignorar busca e retornar como novo entrante
            if data_inicial and data_inicial.month == data_hora.month and data_inicial.year == data_hora.year:
                return 0
            ultima_ladder = HistoricoLadder.objects.filter(ano=ano, mes=mes)
        else:
            # Se houver remoção, ignorar busca por ladder inicial
            if data_inicial:
                return 0
            ultima_ladder = InicioLadder.objects.all()  
            
        if ultima_ladder.filter(jogador=self).exists():
            posicao = ultima_ladder.get(jogador=self).posicao
            
#             print(self, ResultadoDesafioLadder.objects.filter(jogador=self, desafio_ladder__data_hora__lt=data_hora) \
#                 .aggregate(alteracao_total=Sum('alteracao_posicao'))['alteracao_total'] or 0)
            
            # Buscar alterações feitas por alterações de outros jogadores
            if HistoricoLadder.objects.filter(ano=ano, mes=mes).exists():
                # Remoções
                posicao += (ResultadoRemocaoJogador.objects.filter(remocao__data__lt=data_hora, jogador=self) \
                            .filter(remocao__data__month=data_hora.month, remocao__data__year=data_hora.year)
                            .aggregate(alteracao_total=Sum('alteracao_posicao'))['alteracao_total'] or 0)
#                 posicao -= RemocaoJogador.objects.filter(data__lt=data_hora, posicao_jogador__lt=posicao) \
#                     .filter(data__month=data_hora.month, data__year=data_hora.year).count()
                
                # Desafios
                posicao += (ResultadoDesafioLadder.objects.filter(jogador=self, desafio_ladder__data_hora__lt=data_hora) \
                    .filter(desafio_ladder__data_hora__month=data_hora.month, desafio_ladder__data_hora__year=data_hora.year,
                            desafio_ladder__admin_validador__isnull=False, desafio_ladder__cancelamentodesafioladder__isnull=True) \
                    .aggregate(alteracao_total=Sum('alteracao_posicao'))['alteracao_total'] or 0)
                
                # Decaimentos
                posicao += (ResultadoDecaimentoJogador.objects.filter(jogador=self, decaimento__data__lt=data_hora) \
                    .filter(decaimento__data__month=data_hora.month, decaimento__data__year=data_hora.year)
                    .aggregate(alteracao_total=Sum('alteracao_posicao'))['alteracao_total'] or 0)
            else:
                # Remoções
#                 posicao -= RemocaoJogador.objects.filter(data__lt=data_hora, posicao_jogador__lt=posicao).count()
                posicao += (ResultadoRemocaoJogador.objects.filter(remocao__data__lt=data_hora, remocao__data__gt=season.data_hora_inicio,
                                                                   jogador=self).aggregate(alteracao_total= \
                                                                                           Sum('alteracao_posicao'))['alteracao_total'] or 0)
                    
                # Desafios
                posicao += (ResultadoDesafioLadder.objects.filter(jogador=self, desafio_ladder__data_hora__lt=data_hora,
                            desafio_ladder__data_hora__gt=season.data_hora_inicio, desafio_ladder__admin_validador__isnull=False, 
                            desafio_ladder__cancelamentodesafioladder__isnull=True) \
                    .aggregate(alteracao_total=Sum('alteracao_posicao'))['alteracao_total'] or 0)
                
                # Decaimentos
                posicao += (ResultadoDecaimentoJogador.objects.filter(jogador=self, decaimento__data__lt=data_hora,
                                                                      decaimento__data__gt=season.data_hora_inicio) \
                    .aggregate(alteracao_total=Sum('alteracao_posicao'))['alteracao_total'] or 0)
                
            return posicao
        
        # Novos entrantes começam na posição 0
        return 0
    
    def possui_permissao_aumento_range(self, data_hora=None):
        """Verifica se jogador possui permissão de aumento de range válida na data/hora"""
        if not data_hora:
            data_hora = timezone.localtime()
        # Buscar última permissão antes da data/hora e verificar se é válida
        data_hora_inicial = data_hora - datetime.timedelta(hours=PermissaoAumentoRange.PERIODO_VALIDADE)
        if PermissaoAumentoRange.objects.filter(jogador=self, data_hora__gte=data_hora_inicial, 
                                                data_hora__lt=data_hora).exists():
            ultima_permissao = PermissaoAumentoRange.objects.filter(jogador=self, data_hora__gte=data_hora_inicial, 
                                                                    data_hora__lt=data_hora).order_by('-data_hora')[0]
        
            return ultima_permissao.is_valida(data_hora)
        return False

def adicionar_grupo_admins(sender, instance, created, **kwargs):
    """Sinal post-save para adicionar jogador admin ao grupo Admins"""
    if instance.admin:
        instance.user.groups.add(Group.objects.get(name='Admins'))
        instance.user.is_staff = True
        instance.user.save()
    else:
        if instance.user.groups.filter(name='Admins').exists():
            instance.user.groups.remove(Group.objects.get(name='Admins'))
            instance.user.is_staff = False
            instance.user.save()

post_save.connect(adicionar_grupo_admins, sender=Jogador)

class Personagem(models.Model):
    """Personagens disponíveis no jogo"""
    nome = models.CharField(u'Nome', max_length=30)
    icone = models.CharField(u'Ícone', max_length=50)
    imagem = models.CharField(u'Imagem', max_length=50)
    
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
    # Indica se pode ser escolhida apenas depois da primeira luta
    retorno = models.BooleanField('Stage para retorno', default=False)
        
class Feedback(models.Model):
    avaliador = models.ForeignKey('Jogador', on_delete=models.CASCADE, related_name='avaliador')
    avaliado = models.ForeignKey('Jogador', on_delete=models.CASCADE, related_name='avaliado')
    texto = models.CharField('Texto do feedback', max_length=250)
    data_hora = DateTimeFieldTz(u'Data e hora do feedback')
        