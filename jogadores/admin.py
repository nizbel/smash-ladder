# -*- coding: utf-8 -*-
"""Modelos para jogadores mostrados na administração do site"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User

from jogadores.models import Jogador, Personagem, Stage, Feedback


# Define an inline admin descriptor for Jogador model
# which acts a bit like a singleton
class UserJogadorInLine(admin.StackedInline):
    model = Jogador
    can_delete = False
    
    def get_formset(self, request, obj=None, **kwargs):
        formset = super().get_formset(request, obj, **kwargs)
        is_superuser = request.user.is_superuser
        
        if not is_superuser:
            if 'ultimo_uso_coringa' in formset.form.base_fields:
                formset.form.base_fields['ultimo_uso_coringa'].disabled = True
            
        return formset
    
# Define a new User admin
class UserAdmin(BaseUserAdmin):
    inlines = (UserJogadorInLine, )
    
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        is_superuser = request.user.is_superuser

        if not is_superuser:
            if 'is_active' in form.base_fields:
                form.base_fields['is_active'].disabled = True
            if 'is_staff' in form.base_fields:
                form.base_fields['is_staff'].disabled = True
            if 'is_superuser' in form.base_fields:
                form.base_fields['is_superuser'].disabled = True
            if 'user_permissions' in form.base_fields:
                form.base_fields['user_permissions'].disabled = True
            if 'groups' in form.base_fields:
                form.base_fields['groups'].disabled = True
            if 'last_login' in form.base_fields:
                form.base_fields['last_login'].disabled = True
            if 'date_joined' in form.base_fields:
                form.base_fields['date_joined'].disabled = True

        return form
    
    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser
    
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

class FeedbackAdmin(admin.ModelAdmin):
    list_display = ('avaliador', 'avaliado', 'data_hora')
    search_fields = ['avaliador__nick', 'avaliado__nick']
    
    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser
    
    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser
    
admin.site.register(Feedback, FeedbackAdmin)
