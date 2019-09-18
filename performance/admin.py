# -*- coding: utf-8 -*-
"""Modelos para ladder mostrados na administração do site"""
from django.contrib import admin
from performance.models import PerformanceRequisicao


class PerformanceRequisicaoAdmin(admin.ModelAdmin):
    def duracao(self, obj):
        return obj.data_hora_resposta - obj.data_hora_requisicao
    
    list_display = ('data_hora_requisicao', 'data_hora_resposta', 'user', 'url', 'duracao')
    search_fields = ['user', 'url']
    
admin.site.register(PerformanceRequisicao, PerformanceRequisicaoAdmin)
