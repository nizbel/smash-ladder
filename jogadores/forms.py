# -*- coding: utf-8 -*-
"""Formulários para classes de jogador"""
from django.forms.models import ModelForm

from jogadores.models import Jogador


class JogadorForm(ModelForm):

    class Meta:
        model = Jogador
        fields = ('nick', 'main', 'admin')
        
#     def clean(self):
#         data = super(JogadorForm, self).clean()
#         if data.get('valor_objetivo') is None:
#             data['valor_objetivo'] = 0
# 
#         return data