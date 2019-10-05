# -*- coding: utf-8 -*-
"""Utils para treinamento"""

def converter_segundos_duracao(segundos):
    """Converter número de segundos para horas e minutos"""
    horas = segundos // 3600
    minutos = segundos % 3600 // 60
    
    return (horas, minutos)