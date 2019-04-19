# -*- coding: utf-8 -*-
"""Funções para uso geral"""
from django.forms.fields import BooleanField


def preparar_classes_form(form):
    """Adiciona classes de bootstrap para formatar campos dos forms"""
    for field in form.fields.values():
        if isinstance(field, BooleanField):
            field.widget.attrs.update({
                    'class': 'form-control-checkbox'
            })
        else:
            field.widget.attrs.update({
                    'class': 'form-control'
            })