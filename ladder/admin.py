# -*- coding: utf-8 -*-
"""Modelos para ladder mostrados na administração do site"""
from django.contrib import admin

from ladder.models import PosicaoLadder, HistoricoLadder, DesafioLadder, \
    Luta, LutaLadder, InicioLadder, RemocaoJogador, DecaimentoJogador, \
    PermissaoAumentoRange, JogadorLuta, CancelamentoDesafioLadder, \
    SeasonPosicaoInicial, SeasonPosicaoFinal, Season


class HistoricoLadderAdmin(admin.ModelAdmin):
    list_display = ('posicao', 'jogador', 'mes', 'ano')
    search_fields = ['jogador__nick']
    
    def has_add_permission(self, request, obj=None):
        return request.user.is_superuser
    
    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser
    
    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser
    
admin.site.register(HistoricoLadder, HistoricoLadderAdmin)

class LutaAdmin(admin.ModelAdmin):
    list_display = ('ganhador', 'stage', 'data')
    search_fields = ['ganhador__nick', 'stage__nome', 'data']
    
admin.site.register(Luta, LutaAdmin)

class LutaLadderAdmin(admin.ModelAdmin):
    list_display = ('desafio_ladder', 'indice_desafio_ladder')
    search_fields = ['luta__data']
    
    def has_add_permission(self, request, obj=None):
        return request.user.is_superuser
    
    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser
    
    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser
    
admin.site.register(LutaLadder, LutaLadderAdmin)


class InicioLadderAdmin(admin.ModelAdmin):
    list_display = ('posicao', 'jogador')
    search_fields = ['jogador__nick']
    
admin.site.register(InicioLadder, InicioLadderAdmin)

class PosicaoLadderAdmin(admin.ModelAdmin):
    list_display = ('posicao', 'jogador')
    search_fields = ['jogador__nick']
    
    def has_add_permission(self, request, obj=None):
        return request.user.is_superuser
    
    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser
    
    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser
    
admin.site.register(PosicaoLadder, PosicaoLadderAdmin)

class DesafioLadderAdmin(admin.ModelAdmin):
    list_display = ('data_hora', 'desafiante', 'desafiado', 'desafio_coringa', 'admin_validador', 'adicionado_por')
    search_fields = ['desafiante__nick', 'desafiado__nick']
    
    def has_add_permission(self, request, obj=None):
        return request.user.is_superuser
    
    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser
    
    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser
    
admin.site.register(DesafioLadder, DesafioLadderAdmin)

class CancelamentoDesafioLadderAdmin(admin.ModelAdmin):
    list_display = ('data_hora', 'jogador')
    search_fields = ['jogador__nick',]
    
    def has_add_permission(self, request, obj=None):
        return request.user.is_superuser
    
    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser
    
    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser
    
admin.site.register(CancelamentoDesafioLadder, CancelamentoDesafioLadderAdmin)


class RemocaoJogadorAdmin(admin.ModelAdmin):
    list_display = ('posicao_jogador', 'jogador', 'admin_removedor', 'data')
    search_fields = ['jogador__nick']
    
    def has_add_permission(self, request, obj=None):
        return request.user.is_superuser
    
    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser
    
    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser
    
admin.site.register(RemocaoJogador, RemocaoJogadorAdmin)


class DecaimentoJogadorAdmin(admin.ModelAdmin):
    list_display = ('data', 'jogador', 'posicao_inicial', 'qtd_periodos_inatividade')
    search_fields = ['jogador__nick']
    
    def has_add_permission(self, request, obj=None):
        return request.user.is_superuser
    
    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser
    
    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser
    
admin.site.register(DecaimentoJogador, DecaimentoJogadorAdmin)

class PermissaoAumentoRangeAdmin(admin.ModelAdmin):
    list_display = ('data_hora', 'jogador', 'admin_permissor')
    search_fields = ['jogador__nick']
    
    def has_add_permission(self, request, obj=None):
        return request.user.is_superuser
    
    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser
    
    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser
    
admin.site.register(PermissaoAumentoRange, PermissaoAumentoRangeAdmin)


class JogadorLutaAdmin(admin.ModelAdmin):
    list_display = ('jogador', 'personagem', 'luta')
    search_fields = ['jogador__nick', 'personagem__nome']
    
admin.site.register(JogadorLuta, JogadorLutaAdmin)

class SeasonAdmin(admin.ModelAdmin):
    list_display = ('ano', 'indice', 'data_inicio', 'data_fim')
    search_fields = ('ano', 'indice')
    
    def has_add_permission(self, request, obj=None):
        return request.user.is_superuser
    
    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser
    
    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser
    
admin.site.register(Season, SeasonAdmin)

class SeasonPosicaoInicialAdmin(admin.ModelAdmin):
    list_display = ('posicao', 'jogador')
    search_fields = ['jogador__nick']
    
    def has_add_permission(self, request, obj=None):
        return request.user.is_superuser
    
    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser
    
    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser
    
admin.site.register(SeasonPosicaoInicial, SeasonPosicaoInicialAdmin)

class SeasonPosicaoFinalAdmin(admin.ModelAdmin):
    list_display = ('posicao', 'jogador')
    search_fields = ['jogador__nick']
    
    def has_add_permission(self, request, obj=None):
        return request.user.is_superuser
    
    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser
    
    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser
    
admin.site.register(SeasonPosicaoFinal, SeasonPosicaoFinalAdmin)
