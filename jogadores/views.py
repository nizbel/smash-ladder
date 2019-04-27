# -*- coding: utf-8 -*-
"""Views para jogadores"""

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, render, redirect
from django.urls.base import reverse
from django.utils import timezone

from jogadores.forms import JogadorForm
from jogadores.models import Jogador
from ladder.models import DesafioLadder


def detalhar_jogador(request, username):
    """Detalhar um jogador específico pelo nick"""
    jogador = get_object_or_404(Jogador, user__username=username)
    
    jogador.is_de_ferias = jogador.de_ferias_na_data(timezone.now().date())
    
    # Detalhar resultados de desafios do jogador
    desafios = {}
    desafios_feitos = list(DesafioLadder.objects.filter(desafiante=jogador, admin_validador__isnull=False))
    desafios_recebidos = list(DesafioLadder.objects.filter(desafiado=jogador, admin_validador__isnull=False))
    
    desafios['feitos'] = len(desafios_feitos)
    desafios['recebidos'] = len(desafios_recebidos)
    desafios['vitorias'] = len([vitoria for vitoria in desafios_feitos if vitoria.score_desafiante > vitoria.score_desafiado]) \
        + len([vitoria for vitoria in desafios_recebidos if vitoria.score_desafiante < vitoria.score_desafiado])
    desafios['derrotas'] = len([derrota for derrota in desafios_feitos if derrota.score_desafiante < derrota.score_desafiado]) \
        + len([derrota for derrota in desafios_recebidos if derrota.score_desafiante > derrota.score_desafiado]) \
    
    
    return render(request, 'jogadores/detalhar_jogador.html', {'jogador': jogador, 'desafios': desafios})

def listar_jogadores(request):
    """Lista todos os jogadores"""
    jogadores = Jogador.objects.all().select_related('user')
    
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
