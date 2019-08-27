# -*- coding: utf-8 -*-
"""Formulários para classes de torneio"""
from django import forms

from smashLadder.utils import preparar_classes_form
from torneios.models import Torneio
from django.core.exceptions import ValidationError


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
        
            
        