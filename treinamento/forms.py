# -*- coding: utf-8 -*-
"""Formulários para classes de treinamento"""
from django import forms

from smashLadder.utils import preparar_classes_form
from treinamento.models import RegistroTreinamento, Metrica, Anotacao, \
    ResultadoTreinamento


class AnotacaoForm(forms.ModelForm):
    """Formulário para anotação de treinamento"""
    class Meta:
        model = Anotacao
        fields = ('texto',)
        
    def __init__(self,*args,**kwargs):
        super(AnotacaoForm,self).__init__(*args,**kwargs)
        
        preparar_classes_form(self)
        

class MetricaForm(forms.ModelForm):
    """Formulário para registro de treinamento"""
    class Meta:
        model = Metrica
        fields = ('nome', 'descricao')
        
    def __init__(self,*args,**kwargs):
        super(MetricaForm,self).__init__(*args,**kwargs)
        
        preparar_classes_form(self)
        
class RegistroTreinamentoForm(forms.ModelForm):
    """Formulário para registro de treinamento"""
    class Meta:
        model = RegistroTreinamento
        fields = ('inicio', 'fim')
        
    def __init__(self,*args,**kwargs):
        super(RegistroTreinamentoForm,self).__init__(*args,**kwargs)
        
        preparar_classes_form(self)
        
class ResultadoTreinamentoForm(forms.ModelForm):
    """Formulário para resultado de treinamento"""
    class Meta:
        model = ResultadoTreinamento
        fields = ('metrica', 'quantidade')
        
    def __init__(self,*args,**kwargs):
        super(ResultadoTreinamentoForm,self).__init__(*args,**kwargs)
        
        preparar_classes_form(self)
        