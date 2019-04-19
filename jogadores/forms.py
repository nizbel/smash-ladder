# -*- coding: utf-8 -*-
"""Formulários para classes de jogador"""
from django.forms.models import ModelForm

from jogadores.models import Jogador
from smashLadder.utils import preparar_classes_form


class JogadorForm(ModelForm):

    class Meta:
        model = Jogador
        fields = ('nick', 'main', 'admin')
        
    
    def __init__(self,*args,**kwargs):
        if 'admin' in kwargs:
            self.admin = kwargs.pop('admin')
        else:
            self.admin = False
            
        super(JogadorForm,self).__init__(*args,**kwargs)
        
        preparar_classes_form(self)
