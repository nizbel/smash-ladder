# -*- coding: utf-8 -*-
"""Funções para uso geral"""
from django.db import models
from django.forms.fields import BooleanField, DateTimeField
from django.utils import timezone


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
            
class DateTimeFieldTz(models.DateTimeField):
    """Campo utilizado para mostrar data/hora no fuso do sistema"""
    def from_db_value(self, value, expression, connection, context):
        if value is None:
            return None
        else:
            return timezone.localtime(value)