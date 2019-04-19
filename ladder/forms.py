# -*- coding: utf-8 -*-
"""Formulários para classes de ladder"""
import datetime

from django.forms import ValidationError
from django.forms.fields import BooleanField
from django.forms.models import ModelForm, ModelChoiceField
from django.forms.widgets import HiddenInput
from django.utils import timezone

from jogadores.models import Personagem
from ladder.models import RegistroLadder, PosicaoLadder, HistoricoLadder, Luta
from ladder.utils import verificar_posicoes_desafiante_desafiado
from smashLadder.utils import preparar_classes_form


class RegistroLadderForm(ModelForm):
    """Formulário para registro da ladder"""
    class Meta:
        model = RegistroLadder
        fields = ('desafiante', 'desafiado', 'score_desafiante', 'score_desafiado', 'desafio_coringa', 
                  'data_hora', 'adicionado_por')
        
    def __init__(self,*args,**kwargs):
        if 'admin' in kwargs:
            self.admin = kwargs.pop('admin')
        else:
            self.admin = False
            
        super(RegistroLadderForm,self).__init__(*args,**kwargs)
        
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
        criador_registro = cleaned_data.get('adicionado_por')
        score_desafiante = cleaned_data.get('score_desafiante')
        score_desafiado = cleaned_data.get('score_desafiado')
        data_hora = cleaned_data.get('data_hora')
        if not data_hora:
            return cleaned_data
        
        # Testar se registro se refere a histórico ou a ladder atual
        hora_atual = timezone.now()
        if data_hora.month == hora_atual.month and data_hora.year == hora_atual.year:
            ladder = PosicaoLadder.objects
        else:
            ladder = HistoricoLadder.objects.filter(mes=data_hora.month, ano=data_hora.year)
            # Verifica se existe ladder de histórica para data do registro
            if not ladder.exists():
                raise ValidationError(HistoricoLadder.MENSAGEM_LADDER_MES_ANO_INEXISTENTE)
        
        # Verificar se desafiante pode realizar desafio
        try:
            verificar_posicoes_desafiante_desafiado(ladder, desafiante, desafiado, data_hora, desafio_coringa)
        except ValueError as e:
            raise ValidationError(e)
        
        # Se desafio coringa
        if desafio_coringa:
            # Verificar se desafiante pode utilizar desafio coringa
            if not desafiante.pode_usar_coringa_na_data(timezone.make_naive(data_hora).date()):
                raise ValidationError(RegistroLadder.MENSAGEM_ERRO_PERIODO_ESPERA_CORINGA)
        
        # Verificar se criador do registro pode criá-lo
        if criador_registro not in [desafiante, desafiado] and not self.admin:
            raise ValidationError('Jogador não pode criar registros para ladder para terceiros')
        
        # Verificar scores, partidas são melhor de 5
        if (score_desafiante < RegistroLadder.SCORE_VITORIA and score_desafiado < RegistroLadder.SCORE_VITORIA) \
                or (score_desafiante + score_desafiado) > RegistroLadder.MELHOR_DE:
            raise ValidationError(f'Resultado impossível para melhor de {RegistroLadder.MELHOR_DE}')
        
        # Verificar se período de espera para desafio foi respeitado
        lutas_mesmos_jogadores_em_data_proxima = RegistroLadder.objects \
                .filter(desafiante=desafiante, desafiado=desafiado, 
                        data_hora__range=[data_hora - datetime.timedelta(days=RegistroLadder.PERIODO_ESPERA_MESMOS_JOGADORES),
                                          data_hora + datetime.timedelta(days=RegistroLadder.PERIODO_ESPERA_MESMOS_JOGADORES)])
        # Evitar verificar mesma instância
        if self.instance.id != None:
            lutas_mesmos_jogadores_em_data_proxima = lutas_mesmos_jogadores_em_data_proxima.exclude(id=self.instance.id)
           
        if (lutas_mesmos_jogadores_em_data_proxima.exists()):
            raise ValidationError(RegistroLadder.MENSAGEM_ERRO_PERIODO_ESPERA_MESMOS_JOGADORES)
        
        # Modelo anterior
#         if (RegistroLadder.objects.filter(desafiante=desafiante, desafiado=desafiado, 
#                                           data_hora__range=[data_hora - datetime.timedelta(days=RegistroLadder.PERIODO_ESPERA_MESMOS_JOGADORES),
#                                                             data_hora])):
#             raise ValidationError(RegistroLadder.MENSAGEM_ERRO_PERIODO_ESPERA_MESMOS_JOGADORES)
        
        return cleaned_data
    
class RegistroLadderLutaForm(ModelForm):
    """Formulário para uma luta de registro de ladder"""
    personagem_desafiante = ModelChoiceField(queryset=Personagem.objects.all(), required=False)
    personagem_desafiado = ModelChoiceField(queryset=Personagem.objects.all(), required=False)
    
    class Meta:
        model = Luta
        fields = ('ganhador', 'stage')
        
    def __init__(self,*args,**kwargs):
        super(RegistroLadderLutaForm,self).__init__(*args,**kwargs)
        
        preparar_classes_form(self)
        
        if 'id' in self.initial and self.instance.id == None:
            self.instance = Luta.objects.get(id=self.initial['id'])
