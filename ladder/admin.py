# -*- coding: utf-8 -*-
"""Modelos para ladder mostrados na administração do site"""
from django.contrib import admin

from ladder.models import PosicaoLadder, HistoricoLadder, RegistroLadder, \
    Luta, LutaLadder


class HistoricoLadderAdmin(admin.ModelAdmin):
    list_display = ('posicao', 'jogador', 'mes', 'ano')
    search_fields = ['jogador__nick']
    
admin.site.register(HistoricoLadder, HistoricoLadderAdmin)

class LutaAdmin(admin.ModelAdmin):
    list_display = ('ganhador', 'stage', 'data')
    search_fields = ['ganhador__nick', 'stage__nome', 'data']
    
admin.site.register(Luta, LutaAdmin)

class LutaLadderAdmin(admin.ModelAdmin):
    list_display = ('registro_ladder', 'indice_registro_ladder')
    search_fields = ['luta__data']
    
admin.site.register(LutaLadder, LutaLadderAdmin)

class PosicaoLadderAdmin(admin.ModelAdmin):
    list_display = ('posicao', 'jogador')
    search_fields = ['jogador__nick']
    
admin.site.register(PosicaoLadder, PosicaoLadderAdmin)

class RegistroLadderAdmin(admin.ModelAdmin):
    list_display = ('data_hora', 'desafiante', 'desafiado', 'desafio_coringa', 'admin_validador', 'adicionado_por')
    search_fields = ['desafiante__nick', 'desafiado__nick']
    
admin.site.register(RegistroLadder, RegistroLadderAdmin)