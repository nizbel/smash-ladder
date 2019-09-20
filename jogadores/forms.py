# -*- coding: utf-8 -*-
"""Formulários para classes de jogador"""
from django import forms
from django.core.exceptions import ValidationError
from django.forms.forms import Form
from django.forms.models import ModelForm
from django.forms.widgets import Textarea

from jogadores.models import Jogador, Stage, StageValidaLadder, Feedback
from smashLadder.utils import preparar_classes_form


class JogadorForm(ModelForm):
    email = forms.EmailField(required=False, help_text='Utilizado para troca de senha')
    
    class Meta:
        model = Jogador
        fields = ('nick', 'main', 'admin')
        
    
    def __init__(self,*args,**kwargs):
        if 'admin' in kwargs:
            self.admin = kwargs.pop('admin')
        else:
            self.admin = False
            
        super(JogadorForm,self).__init__(*args,**kwargs)
        
        if self.instance:
            self.fields['email'].initial = self.instance.user.email
        
        preparar_classes_form(self)

class StagesValidasForm(Form):
    retorno = forms.BooleanField(label='Alterar retorno', required=False)
    stages_validas = forms.MultipleChoiceField(label='Stages válidas para Ladder')
    
    def __init__(self,*args,**kwargs):
        super(StagesValidasForm,self).__init__(*args,**kwargs)
        
        preparar_classes_form(self)
        
        self.fields['stages_validas'].choices = [(stage.id, f'{stage.nome} ({stage.descricao_modelo})') for stage in Stage.objects.all()]
        
        self.fields['stages_validas'].widget.attrs.update({
            'class': 'form-control col-12'
        })

    def clean_stages_validas(self):
        stages_validas = self.cleaned_data['stages_validas']
        retorno = self.cleaned_data['retorno']
        
        stages_validas = [int(stage_valida) for stage_valida in stages_validas] 
        
        # Verificar se a outra opção de retorno já inclui alguma das fases
        if StageValidaLadder.objects.filter(retorno=(not retorno), stage__in=stages_validas).exists():
            if retorno:
                raise ValidationError('A seleção não pode incluir stages que já foram marcadas para serem iniciais')
            else:
                raise ValidationError('A seleção não pode incluir stages que já foram marcadas para serem de retorno')
               
        return stages_validas
    
class FeedbackForm(ModelForm):

    class Meta:
        model = Feedback
        fields = ('texto',)
        widgets = {
            'texto': Textarea(attrs={'rows': 10}),
        }
        help_texts = {
            'texto': 'Limite de 250 caracteres',
        }
        
    
    def __init__(self,*args,**kwargs):
        super(FeedbackForm,self).__init__(*args,**kwargs)
        
        preparar_classes_form(self)
