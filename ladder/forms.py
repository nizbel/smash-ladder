# -*- coding: utf-8 -*-
"""Formulários para classes de ladder"""
import datetime

from django import forms
from django.db.models.query_utils import Q
from django.forms import ValidationError
from django.forms.models import ModelForm, ModelChoiceField
from django.utils import timezone

from jogadores.models import Personagem, Stage, Jogador
from ladder.models import DesafioLadder, PosicaoLadder, HistoricoLadder, Luta, \
    RemocaoJogador
from ladder.utils import verificar_posicoes_desafiante_desafiado
from smashLadder.utils import preparar_classes_form


class DesafioLadderForm(ModelForm):
    """Formulário para desafio da ladder"""
    class Meta:
        model = DesafioLadder
        fields = ('desafiante', 'desafiado', 'score_desafiante', 'score_desafiado', 'desafio_coringa', 
                  'data_hora', 'adicionado_por')
        
    def __init__(self,*args,**kwargs):
        if 'admin' in kwargs:
            self.admin = kwargs.pop('admin')
        else:
            self.admin = False
            
        super(DesafioLadderForm,self).__init__(*args,**kwargs)
        
        preparar_classes_form(self)
    
    def clean_data_hora(self):
        data_hora = self.cleaned_data['data_hora']
        
        if data_hora > timezone.now():
            raise ValidationError('Horário da partida não pode ocorrer no futuro')
        
        return data_hora
        
    def clean(self):
        cleaned_data = super().clean()
        
        desafiante = cleaned_data.get('desafiante')
        desafiado = cleaned_data.get('desafiado')
        desafio_coringa = cleaned_data.get('desafio_coringa')
        criador_desafio = cleaned_data.get('adicionado_por')
        score_desafiante = cleaned_data.get('score_desafiante')
        score_desafiado = cleaned_data.get('score_desafiado')
        data_hora = cleaned_data.get('data_hora')
        if not data_hora:
            return cleaned_data
        
        # Converter data/hora para fuso local
        data_hora = timezone.localtime(data_hora)
        
        # Testar se desafio se refere a histórico ou a ladder atual
        hora_atual = timezone.localtime()
        if data_hora.month == hora_atual.month and data_hora.year == hora_atual.year:
            ladder = PosicaoLadder.objects
        else:
            ladder = HistoricoLadder.objects.filter(mes=data_hora.month, ano=data_hora.year)
            # Verifica se existe ladder de histórica para data do desafio
            if not ladder.exists():
                raise ValidationError(HistoricoLadder.MENSAGEM_LADDER_MES_ANO_INEXISTENTE)
        
        # Verificar se desafiante pode realizar desafio
        try:
#             verificar_posicoes_desafiante_desafiado(ladder, desafiante, desafiado, data_hora, desafio_coringa)
            novo_desafio = DesafioLadder(desafiante=desafiante, desafiado=desafiado, data_hora=data_hora, 
                                         desafio_coringa=desafio_coringa)
            verificar_posicoes_desafiante_desafiado(novo_desafio)
        except ValueError as e:
            raise ValidationError(e)
        
        # Se desafio coringa
        if desafio_coringa:
            # Verificar se desafiante pode utilizar desafio coringa
            if not desafiante.pode_usar_coringa_na_data(data_hora.date()):
                raise ValidationError(DesafioLadder.MENSAGEM_ERRO_PERIODO_ESPERA_CORINGA)
        
        # Verificar se criador do desafio pode criá-lo
        if criador_desafio not in [desafiante, desafiado] and not self.admin:
            raise ValidationError('Jogador não pode criar desafios para ladder para terceiros')
        
        # Verificar scores, partidas são melhor de 5
        if (score_desafiante < DesafioLadder.SCORE_VITORIA and score_desafiado < DesafioLadder.SCORE_VITORIA) \
                or (score_desafiante + score_desafiado) > DesafioLadder.MELHOR_DE:
            raise ValidationError(f'Resultado impossível para melhor de {DesafioLadder.MELHOR_DE}')
        
        # Verificar se período de espera para desafio foi respeitado
        lutas_mesmos_jogadores_em_data_proxima = DesafioLadder.objects \
                .filter(desafiante=desafiante, desafiado=desafiado, cancelamentodesafioladder__isnull=True,
                        data_hora__range=[data_hora - datetime.timedelta(days=DesafioLadder.PERIODO_ESPERA_MESMOS_JOGADORES),
                                          data_hora + datetime.timedelta(days=DesafioLadder.PERIODO_ESPERA_MESMOS_JOGADORES)])
        # Evitar verificar mesma instância
        if self.instance.id != None:
            lutas_mesmos_jogadores_em_data_proxima = lutas_mesmos_jogadores_em_data_proxima.exclude(id=self.instance.id)
           
        if (lutas_mesmos_jogadores_em_data_proxima.exists()):
            raise ValidationError(DesafioLadder.MENSAGEM_ERRO_PERIODO_ESPERA_MESMOS_JOGADORES)
        
        # Verificar se jogadores envolvidos não estão presentes em outros desafios exatamente no mesmo horário
        if DesafioLadder.objects.filter(Q(data_hora=data_hora, desafiante__in=[desafiante, desafiado]) |
                                        Q(data_hora=data_hora, desafiado__in=[desafiante, desafiado])) \
                                        .exclude(id=self.instance.id).exists():
            raise ValidationError('Jogadores participantes do desafio já estão em outro desafio exatamente na mesma data/hora')
        
        # Modelo anterior
#         if (DesafioLadder.objects.filter(desafiante=desafiante, desafiado=desafiado, 
#                                           data_hora__range=[data_hora - datetime.timedelta(days=DesafioLadder.PERIODO_ESPERA_MESMOS_JOGADORES),
#                                                             data_hora])):
#             raise ValidationError(DesafioLadder.MENSAGEM_ERRO_PERIODO_ESPERA_MESMOS_JOGADORES)

        # Verificar que não há remoção de jogador participante na mesma data
        if RemocaoJogador.objects.filter(data__date=data_hora.date(), jogador__in=[desafiante, desafiado]).exists():
            remocao = RemocaoJogador.objects.filter(data__date=data_hora.date(), jogador__in=[desafiante, desafiado])[0]
            raise ValidationError(f'{remocao.jogador} é removido da ladder na data especificada')
        
        return cleaned_data

class DesafioLadderLutaForm(ModelForm):
    """Formulário para uma luta de desafio de ladder"""
    personagem_desafiante = ModelChoiceField(queryset=Personagem.objects.all(), required=False)
    personagem_desafiado = ModelChoiceField(queryset=Personagem.objects.all(), required=False)
    
    class Meta:
        model = Luta
        fields = ('ganhador', 'stage')
        
    def __init__(self,*args,**kwargs):
        super(DesafioLadderLutaForm,self).__init__(*args,**kwargs)
        
        preparar_classes_form(self)
        
        if 'id' in self.initial and self.instance.id == None:
            self.instance = Luta.objects.get(id=self.initial['id'])
            
        self.fields['stage'].queryset = Stage.objects.filter(stagevalidaladder__isnull=False)
            
class RemocaoJogadorForm(ModelForm):
    """Formulário para remoção de jogador da ladder"""
    
    class Meta:
        model = RemocaoJogador
        fields = ('jogador', 'data', 'admin_removedor', 'posicao_jogador')
        widgets = {'posicao_jogador': forms.HiddenInput()}
        
    def __init__(self,*args,**kwargs):
        super(RemocaoJogadorForm,self).__init__(*args,**kwargs)
        
        preparar_classes_form(self)
        # Campo de posição não é obrigatório, pois será preenchido automaticamente
        self.fields['posicao_jogador'].required = False
        
    def clean(self):
        cleaned_data = super().clean()
        admin_removedor = cleaned_data.get('admin_removedor')
        data = cleaned_data.get('data')
        jogador = cleaned_data.get('jogador')
        
        if DesafioLadder.objects.filter(cancelamentodesafioladder__isnull=True, data_hora__date=data.date()).exists():
            raise ValidationError('Jogador possui desafio na data apontada para remoção')
            
        if not admin_removedor.admin:
            raise ValidationError('Responsável pela remoção deve ser admin')
        
        posicao_jogador = jogador.posicao_em(data)
        if posicao_jogador == 0:
            raise ValidationError('Jogador não estava presente na ladder na data especificada')
        
        cleaned_data['posicao_jogador'] = posicao_jogador
        
        return cleaned_data
