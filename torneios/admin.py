# -*- coding: utf-8 -*-
"""Modelos para jogadores mostrados na administração do site"""
from django.contrib import admin

from torneios.models import Torneio, Round, JogadorTorneio, Time, Partida


class TorneioAdmin(admin.ModelAdmin):
    list_display = ('nome', 'data', 'url', 'adicionado_por')
    search_fields = ['nome', 'data']
    
admin.site.register(Torneio, TorneioAdmin)

class RoundAdmin(admin.ModelAdmin):
    list_display = ('torneio', 'indice', 'nome')
    search_fields = ['nome', 'torneio__nome']
    
admin.site.register(Round, RoundAdmin)


class PartidaAdmin(admin.ModelAdmin):
    list_display = ('jogador_1', 'score_1', 'jogador_2', 'score_2', 'round', 'ganhador')
    search_fields = ['jogador_1__nome', 'jogador_2__nome']
    
admin.site.register(Partida, PartidaAdmin)


class JogadorTorneioAdmin(admin.ModelAdmin):
    list_display = ('nome', 'time', 'torneio', 'posicao_final')
    search_fields = ['nome', 'time__nome', 'torneio__nome', 'posicao_final']
    
admin.site.register(JogadorTorneio, JogadorTorneioAdmin)


class TimeAdmin(admin.ModelAdmin):
    list_display = ('nome',)
    search_fields = ['nome']
    
admin.site.register(Time, TimeAdmin)
