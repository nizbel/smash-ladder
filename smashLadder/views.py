# -*- coding: utf-8 -*-
"""Views gerais"""
from django.shortcuts import render

from ladder.models import PosicaoLadder, DesafioLadder

def home(request):
    """Detalhar regras da ladder"""
    
    top_10_ladder = PosicaoLadder.objects.filter(posicao__lte=10).order_by('posicao').select_related('jogador__user', 'jogador__main')
    
    ultimos_desafios_ladder = DesafioLadder.objects.all().order_by('-data_hora').select_related('desafiante', 'desafiado', 'cancelamentodesafioladder')[:4]
    
    if request.user.is_authenticated:
        for desafio in ultimos_desafios_ladder:
            desafio.is_cancelavel = desafio.cancelavel_por_jogador(request.user.jogador)
    
    return render(request, 'home.html', {'ultimos_desafios_ladder': ultimos_desafios_ladder,
                                                  'top_10_ladder': top_10_ladder})


