# -*- coding: utf-8 -*-
"""Modelos para jogadores mostrados na administração do site"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User

from jogadores.models import Jogador, Personagem, Stage, RegistroFerias, \
    Feedback


# Define an inline admin descriptor for Employee model
# which acts a bit like a singleton
class UserJogadorInLine(admin.StackedInline):
    model = Jogador
    can_delete = False
    
# Define a new User admin
class UserAdmin(BaseUserAdmin):
    inlines = (UserJogadorInLine, )
    
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        is_superuser = request.user.is_superuser
        print(form.base_fields)
        if not is_superuser:
            form.base_fields['is_superuser'].disabled = True
            form.base_fields['user_permissions'].disabled = True
            form.base_fields['groups'].disabled = True

        return form
  
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


class RegistroFeriasAdmin(admin.ModelAdmin):
    list_display = ('jogador', 'data_inicio', 'data_fim')
    search_fields = ['jogador__nick']
    
admin.site.register(RegistroFerias, RegistroFeriasAdmin)


class FeedbackAdmin(admin.ModelAdmin):
    list_display = ('avaliador', 'avaliado', 'data_hora')
    search_fields = ['avaliador__nick', 'avaliado__nick']
    
admin.site.register(Feedback, FeedbackAdmin)
