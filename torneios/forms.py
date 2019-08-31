# -*- coding: utf-8 -*-
"""Formulários para classes de torneio"""
from django import forms
from django.core.exceptions import ValidationError

from smashLadder.utils import preparar_classes_form
from torneios.models import Torneio, JogadorTorneio, Round, Time


class CriarTorneioForm(forms.Form):
    """Formulário para criação de torneio"""
    identificador_torneio = forms.CharField(label='Identificador ou URL', max_length=50)
    site = forms.TypedChoiceField(label='Site', choices=Torneio.OPCOES_SITE, coerce=int)
    delimitador_time = forms.CharField(label='Delimitador de time', max_length=5, initial='|')

    def __init__(self,*args,**kwargs):
        super(CriarTorneioForm,self).__init__(*args,**kwargs)
        
        preparar_classes_form(self)
    
    def clean(self):
        cleaned_data = super().clean()
        
        identificador_torneio = cleaned_data['identificador_torneio']
        site = cleaned_data['site']
        
        # Definir site do torneio
        if site == Torneio.SITE_CHALLONGE_ID:
            url_site = Torneio.SITE_CHALLONGE_URL
        else:
            raise ValidationError(Torneio.MENSAGEM_ERRO_SITE_INVALIDO)
        
        # Verificar se identificador do torneio é URL
        is_url = (url_site in identificador_torneio)
        
        if is_url:
            url = identificador_torneio
        else:
            url = url_site + identificador_torneio
            
        # Verificar se já existe torneio com a URL inserida
        if Torneio.objects.filter(url=url).exists():
            raise ValidationError(Torneio.MENSAGEM_ERRO_URL_TORNEIO_JA_EXISTENTE)
        
class JogadorTorneioForm(forms.ModelForm):
    """Formulário para jogador de um torneio"""
    class Meta:
        model = JogadorTorneio
        fields = ('nome', 'time', 'valido', 'jogador')
        labels = {'jogador': 'Jogador da Ladder'}
        
    def __init__(self,*args,**kwargs):
        super(JogadorTorneioForm,self).__init__(*args,**kwargs)
        
        preparar_classes_form(self)
        
    def clean(self):
        cleaned_data = super().clean()
        
        jogador = cleaned_data['jogador']
        time = cleaned_data['time']
        valido = cleaned_data['valido']
        
        # Verifica se outro jogador no mesmo torneio já não está vinculado ao mesmo jogador da ladder
        if jogador and JogadorTorneio.objects.filter(torneio=self.instance.torneio, jogador=jogador).exclude(id=self.instance.id).exists():
            jogador_torneio = JogadorTorneio.objects.get(torneio=self.instance.torneio, jogador=jogador)
            raise ValidationError(f'Jogador da Ladder já está vinculado a {jogador_torneio.seed} - {jogador_torneio.nome}')
        
        # Jogador inválido não pode ter time
        if not valido and time:
            raise ValidationError('Jogador inválido não pode estar ligado a time')
    
class RoundForm(forms.ModelForm):
    """Formulário para round de um torneio"""
    class Meta:
        model = Round
        fields = ('nome',)
        
    def __init__(self,*args,**kwargs):
        super(RoundForm,self).__init__(*args,**kwargs)
        
        preparar_classes_form(self)
        
class TimeForm(forms.ModelForm):
    """Formulário para time"""
    class Meta:
        model = Time
        fields = ('nome',)
    
    def __init__(self,*args,**kwargs):
        super(TimeForm,self).__init__(*args,**kwargs)
        
        preparar_classes_form(self)
        