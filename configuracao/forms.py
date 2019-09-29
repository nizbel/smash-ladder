# -*- coding: utf-8 -*-
"""Formulários para classes de jogador"""
from django import forms
from django.core.exceptions import ValidationError

from configuracao.models import ConfiguracaoLadder


class ConfiguracaoLadderForm(forms.ModelForm):
    model = ConfiguracaoLadder
    
    def clean(self):
        if not self.instance.id and ConfiguracaoLadder.objects.all().exists():
            raise ValidationError('Não é possível adicionar outro objeto de configurações')