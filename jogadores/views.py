# -*- coding: utf-8 -*-
"""Views para jogadores"""

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models.aggregates import Count, Max
from django.db.models.expressions import F
from django.db.models.query_utils import Q
from django.shortcuts import get_object_or_404, render, redirect
from django.urls.base import reverse
from django.utils import timezone

from jogadores.forms import JogadorForm, StagesValidasForm
from jogadores.models import Jogador, Stage, StageValidaLadder
from ladder.models import DesafioLadder, Luta


def detalhar_jogador(request, username):
    """Detalhar um jogador específico pelo nick"""
    jogador = get_object_or_404(Jogador, user__username=username)
    
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
    
    jogador.percentual_vitorias = desafios['vitorias'] * 100 / ((desafios['vitorias'] + desafios['derrotas']) or 1)
    
    # Preencher gráfico com percentual de vitórias
    jogador.grafico_percentual_vitorias = list()
    qtd_vitorias = 0
    qtd_desafios = 0
    for desafio in DesafioLadder.objects.filter(Q(desafiante=jogador) | Q(desafiado=jogador), cancelamentodesafioladder__isnull=True) \
            .order_by('data_hora'):
        if desafio.desafiante == jogador and desafio.score_desafiante > desafio.score_desafiado:
            qtd_vitorias += 1
        elif desafio.desafiado == jogador and desafio.score_desafiante < desafio.score_desafiado:
            qtd_vitorias += 1
        qtd_desafios += 1
        percentual_vitorias = qtd_vitorias * 100 / qtd_desafios 
        jogador.grafico_percentual_vitorias.append(round(percentual_vitorias, 2))
        
    
    return render(request, 'jogadores/detalhar_jogador.html', {'jogador': jogador, 'desafios': desafios})

def detalhar_stage_id(request, stage_id):
    """Detalha uma stage específica"""
    stage = get_object_or_404(Stage, id=stage_id)
    
    # Definir quantidade de lutas e maior ganhador
    stage.qtd_lutas = Luta.objects.filter(lutaladder__desafio_ladder__cancelamentodesafioladder__isnull=True, stage=stage).count()
    
    if stage.qtd_lutas > 0:
        # Guarda maior quantidade de vitórias para garantir que apenas um possua essa quantidade
        maior_qtd_vitorias = Luta.objects.filter(lutaladder__desafio_ladder__cancelamentodesafioladder__isnull=True,
                                                   stage=stage, ganhador__isnull=False).order_by('ganhador').values('ganhador') \
            .annotate(qtd_vitorias=Count('ganhador')).aggregate(maior_qtd_vitorias=Max('qtd_vitorias'))['maior_qtd_vitorias'] or 0
        
        if maior_qtd_vitorias > 0:
            jogadores_com_mais_vitorias = Luta.objects.filter(lutaladder__desafio_ladder__cancelamentodesafioladder__isnull=True,
                                                       stage=stage, ganhador__isnull=False).order_by('ganhador').values('ganhador') \
                .annotate(qtd_vitorias=Count('ganhador')).filter(qtd_vitorias=maior_qtd_vitorias)
            if len(jogadores_com_mais_vitorias) == 1:
                stage.maior_ganhador = Jogador.objects.get(id=jogadores_com_mais_vitorias[0]['ganhador'])
    
    return render(request, 'stages/detalhar_stage.html', {'stage': stage})

def listar_jogadores(request):
    """Lista todos os jogadores"""
    jogadores = Jogador.objects.all().select_related('user')
    
    return render(request, 'jogadores/listar_jogadores.html', {'jogadores': list(jogadores)})

def listar_stages(request, apenas_validas_ladder=False):
    """Lista todos os stages"""
    if apenas_validas_ladder:
        stages = list(Stage.objects.filter(stagevalidaladder__isnull=False).order_by('nome', 'modelo').select_related('stagevalidaladder'))
    else:
        stages = list(Stage.objects.all().order_by('nome', 'modelo').select_related('stagevalidaladder'))
    
    return render(request, 'stages/listar_stages.html', {'stages': stages, 'apenas_validas_ladder': apenas_validas_ladder})

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

@login_required
def editar_stages_validas(request):
    if not request.user.jogador.admin:
        raise PermissionDenied
    
    if request.POST:
        form_stages_validas = StagesValidasForm(request.POST)
        
        if form_stages_validas.is_valid():
            print(form_stages_validas.cleaned_data)
            
            stages_validas_atualmente = list(Stage.objects.filter(stagevalidaladder__isnull=False).values_list('id', flat=True))
            print(stages_validas_atualmente)
            
            novas_stages_validas = Stage.objects.filter(id__in=form_stages_validas.cleaned_data['stages_validas'])
            for stage in novas_stages_validas:
                if stage.id not in stages_validas_atualmente:
                    nova_stage_valida = StageValidaLadder(stage=stage)
                    nova_stage_valida.save()
                    
                else:
                    stages_validas_atualmente.remove(stage.id)
                    
            # Invalidar stages que não tenham sido seleciondas (não foram removidas na etapa anterior)
            StageValidaLadder.objects.filter(stage__id__in=stages_validas_atualmente).delete()
                
            return redirect(reverse('stages:listar_stages_validas'))
    else:
        # Preparar form
        form_stages_validas = StagesValidasForm(initial={
            'stages_validas': [stage_id for stage_id in Stage.objects.filter(stagevalidaladder__isnull=False).values_list('id', flat=True)]})
    
    return render(request, 'stages/editar_stages_validas.html', {'form_stages_validas': form_stages_validas})
