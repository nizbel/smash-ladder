# -*- coding: utf-8 -*-
"""Formulários para classes de jogador"""
from django import forms
from django.forms.forms import Form
from django.forms.models import ModelForm

from jogadores.models import Jogador, Stage
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

class StagesValidasForm(Form):
    stages_validas = forms.MultipleChoiceField()
    
    def __init__(self,*args,**kwargs):
        super(StagesValidasForm,self).__init__(*args,**kwargs)
#         print('Inicial', self.fields['stages_validas'].initial, self.initial)
        self.fields['stages_validas'].label = 'Stages válidas para Ladder'
        self.fields['stages_validas'].choices = [(stage.id, f'{stage.nome} ({stage.descricao_modelo})') for stage in Stage.objects.all()]
        
        self.fields['stages_validas'].widget.attrs.update({
            'class': 'form-control col-12'
        })

    def clean_stages_validas(self):
        stages_validas = self.cleaned_data['stages_validas']
        
        stages_validas = [int(stage_valida) for stage_valida in stages_validas] 
               
        return stages_validas