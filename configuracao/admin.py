# -*- coding: utf-8 -*-
"""Modelos para ladder mostrados na administração do site"""
from django.contrib import admin
from django.forms.models import model_to_dict

from configuracao.forms import ConfiguracaoLadderForm
from configuracao.models import ConfiguracaoLadder, HistoricoConfiguracaoLadder
from ladder.models import DesafioLadder, Season, DecaimentoJogador


class ConfiguracaoLadderAdmin(admin.ModelAdmin):
    form = ConfiguracaoLadderForm
    
    list_display = ('__str__', *[field.name for field in ConfiguracaoLadder._meta.fields if field.name != 'id'])

    def has_add_permission(self, request, obj=None):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False
    
    def save_model(self, request, obj, form, change):
        # Gerar histórico
        campos = model_to_dict(obj, exclude=['id',])

        historico = HistoricoConfiguracaoLadder(**campos, responsavel=request.user)
        historico.save()
        
        # Salvar
        super().save_model(request, obj, form, change)
        
        DesafioLadder.alterar_melhor_de()
        DesafioLadder.alterar_limite_posicoes_desafio()
        Season.alterar_periodo_season()
        DecaimentoJogador.alterar_abonar_primeiro_decaimento()
        DecaimentoJogador.alterar_periodo_inatividade()
        
    
admin.site.register(ConfiguracaoLadder, ConfiguracaoLadderAdmin)


class HistoricoConfiguracaoLadderAdmin(admin.ModelAdmin):
    list_display = ('data_hora', 'responsavel', *[field.name for field in HistoricoConfiguracaoLadder._meta.fields if field.name != 'id'])
    search_fields= ('limite_posicoes_desafio', 'data_hora', 'responsavel__username')
    
    def has_add_permission(self, request, obj=None):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False
    
admin.site.register(HistoricoConfiguracaoLadder, HistoricoConfiguracaoLadderAdmin)
