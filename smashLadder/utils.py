# -*- coding: utf-8 -*-
"""Funções para uso geral"""
from django.forms.fields import BooleanField, DateTimeField


def preparar_classes_form(form):
    """Adiciona classes de bootstrap para formatar campos dos forms"""
    for field in form.fields.values():
        if isinstance(field, BooleanField):
            field.widget.attrs.update({
                    'class': 'form-control-checkbox'
            })
        elif isinstance(field, DateTimeField):
            field.widget.attrs.update({
                    'class': 'form-control data-hora'
            })
        else:
            field.widget.attrs.update({
                    'class': 'form-control'
            })