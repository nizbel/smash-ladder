# -*- coding: utf-8 -*-
"""Modelos para jogadores mostrados na administração do site"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User

from jogadores.models import Jogador, Personagem, Stage


# Define an inline admin descriptor for Employee model
# which acts a bit like a singleton
class UserJogadorInLine(admin.StackedInline):
    model = Jogador
    can_delete = False
  
# Define a new User admin
class UserAdmin(BaseUserAdmin):
    inlines = (UserJogadorInLine, )
  
# Re-register UserAdmin
admin.site.unregister(User)
admin.site.register(User, UserAdmin)


class PersonagemAdmin(admin.ModelAdmin):
    list_display = ('nome',)
    search_fields = ['nome']
    
admin.site.register(Personagem, PersonagemAdmin)

class StageAdmin(admin.ModelAdmin):
    list_display = ('nome', 'descricao_modelo')
    search_fields = ['nome']
    
admin.site.register(Stage, StageAdmin)