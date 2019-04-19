# -*- coding: utf-8 -*-
"""Views para jogadores"""

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, render, redirect
from django.urls.base import reverse

from jogadores.models import Jogador
from jogadores.forms import JogadorForm


def detalhar_jogador(request, username):
    """Detalhar um jogador específico pelo nick"""
    jogador = get_object_or_404(Jogador, user__username=username)
    
    return render(request, 'jogadores/detalhar_jogador.html', {'jogador': jogador})

def listar_jogadores(request):
    """Lista todos os jogadores"""
    jogadores = Jogador.objects.all()
    
    return render(request, 'jogadores/listar_jogadores.html', {'jogadores': list(jogadores)})

@login_required
def editar_jogador(request, username):
    """Editar um jogador específico pelo nick"""
    if request.user.username != username and not request.user.jogador.admin:
        raise PermissionDenied
    
    jogador = Jogador.objects.get(user__username=username)
    
    if request.POST:
        form_jogador = JogadorForm(request.POST, instance=jogador)
        # Definir campos desabilitados
        if not request.user.jogador.admin:
            # Apenas admin pode alterar campo admin
            form_jogador.fields['admin'].disabled = True
        if request.user.username != username:
            # Apenas próprio usuário pode alterar seu nick e main
            form_jogador.fields['main'].disabled = True
            form_jogador.fields['nick'].disabled = True
        
        
        if form_jogador.is_valid():
            jogador = form_jogador.save(commit=False)
            jogador.save()
            
            return redirect(reverse('jogadores:detalhar_jogador', kwargs={'username': jogador.user.username}))
        
        else:
            print(form_jogador.errors)
    else:
        # Preparar form
        form_jogador = JogadorForm(instance=jogador)
        # Definir campos desabilitados
        if not request.user.jogador.admin:
            # Apenas admin pode alterar campo admin
            form_jogador.fields['admin'].disabled = True
        if request.user.username != username:
            # Apenas próprio usuário pode alterar seu nick e main
            form_jogador.fields['main'].disabled = True
            form_jogador.fields['nick'].disabled = True
    
    
    return render(request, 'jogadores/editar_jogador.html', {'jogador': jogador, 'form_jogador': form_jogador})
