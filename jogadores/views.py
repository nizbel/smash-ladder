# -*- coding: utf-8 -*-
"""Views para jogadores"""

import datetime

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.db.models.aggregates import Count, Max, Sum
from django.db.models.expressions import F, Value
from django.db.models.fields import IntegerField
from django.db.models.query_utils import Q
from django.http.response import JsonResponse
from django.shortcuts import get_object_or_404, render, redirect
from django.urls.base import reverse
from django.utils import timezone

from jogadores.forms import JogadorForm, StagesValidasForm, FeedbackForm
from jogadores.models import Jogador, Stage, StageValidaLadder, Personagem, \
    Feedback
from ladder.models import DesafioLadder, Luta, ResultadoDesafioLadder, \
    JogadorLuta, RemocaoJogador, ResultadoDecaimentoJogador
from ladder.utils import buscar_desafiaveis


def detalhar_jogador(request, username):
    """Detalhar um jogador específico pelo nick"""
    jogador = get_object_or_404(Jogador.objects.select_related('main'), user__username=username)
    
    # Detalhar resultados de desafios do jogador
    desafios = {}
    desafios_feitos = list(DesafioLadder.validados.filter(desafiante=jogador).select_related('desafiante', 'desafiado'))
    desafios_recebidos = list(DesafioLadder.validados.filter(desafiado=jogador).select_related('desafiante', 'desafiado'))
    
    desafios['feitos'] = len(desafios_feitos)
    desafios['recebidos'] = len(desafios_recebidos)
    desafios['vitorias'] = len([vitoria for vitoria in desafios_feitos if vitoria.score_desafiante > vitoria.score_desafiado]) \
        + len([vitoria for vitoria in desafios_recebidos if vitoria.score_desafiante < vitoria.score_desafiado])
    desafios['derrotas'] = len([derrota for derrota in desafios_feitos if derrota.score_desafiante < derrota.score_desafiado]) \
        + len([derrota for derrota in desafios_recebidos if derrota.score_desafiante > derrota.score_desafiado]) \
    
    jogador.percentual_vitorias = desafios['vitorias'] * 100 / ((desafios['vitorias'] + desafios['derrotas']) or 1)
    
    # Posição atual na ladder
    jogador.posicao_atual = jogador.posicao_em(timezone.localtime())
    
    # Buscar primeiro desafio
    todos_desafios = desafios_feitos
    todos_desafios.extend(desafios_recebidos)
    # Ordenar por data
    todos_desafios.sort(key = lambda x: x.data_hora)
    
    # Preencher gráfico com percentual de vitórias
    jogador.grafico_percentual_vitorias = list()
    qtd_vitorias = 0
    qtd_desafios = 0
    
    for desafio in todos_desafios:
        if desafio.desafiante_id == jogador.id and desafio.score_desafiante > desafio.score_desafiado:
            qtd_vitorias += 1
        elif desafio.desafiado_id == jogador.id and desafio.score_desafiante < desafio.score_desafiado:
            qtd_vitorias += 1
        qtd_desafios += 1
        percentual_vitorias = qtd_vitorias * 100 / qtd_desafios 
        jogador.grafico_percentual_vitorias.append(round(percentual_vitorias, 2))
        
    # Preencher gráfico de variação de posição utilizando resultados
    jogador.grafico_variacao_posicao = list()
    
    # Verificar se jogador possui desafios
    if todos_desafios:
        # Verificar se jogador possui remoções
        if RemocaoJogador.objects.filter(jogador=jogador).exists():
            # Buscar última remoção
            ultima_remocao = RemocaoJogador.objects.filter(jogador=jogador).order_by('-data')[0]
            
            for desafio in todos_desafios:
                if desafio.data_hora > ultima_remocao.data:
                    primeiro_desafio = desafio
                    break
            else:
                primeiro_desafio = None
        else:
            primeiro_desafio = todos_desafios[0]
        
        if primeiro_desafio:
            data_inicial = primeiro_desafio.data_hora
        
            if primeiro_desafio.desafiante_id == jogador.id:
                posicao_inicial = primeiro_desafio.posicao_desafiante
            else:
                posicao_inicial = primeiro_desafio.posicao_desafiado
        
            jogador.grafico_variacao_posicao.append({'x': data_inicial.strftime('%d/%m/%Y %H:%M'), 'y': posicao_inicial})
        
            # Preencher gráfico com variações a partir dessa data
            posicao_atual = posicao_inicial
            resultados_desafios = list(ResultadoDesafioLadder.objects.filter(jogador=jogador, desafio_ladder__data_hora__gte=data_inicial) \
                                       .annotate(data_hora=F('desafio_ladder__data_hora')) \
                                       .values('data_hora').annotate(alteracao_total=Sum('alteracao_posicao')) \
                                       .annotate(tipo=Value(1, output_field=IntegerField())) \
                                       .values('alteracao_total', 'data_hora', 'tipo').order_by('data_hora', 'desafio_ladder__posicao_desafiado'))
            resultados_decaimentos = list(ResultadoDecaimentoJogador.objects.filter(jogador=jogador, decaimento__data__gte=data_inicial) \
                                          .annotate(data_hora=F('decaimento__data')) \
                                          .values('data_hora').annotate(alteracao_total=Sum('alteracao_posicao')) \
                                          .annotate(tipo=Value(2, output_field=IntegerField())) \
                                          .values('alteracao_total', 'data_hora', 'tipo').order_by('data_hora', 'decaimento__posicao_inicial'))
            resultados_remocoes = list(RemocaoJogador.objects.filter(data__gte=data_inicial).annotate(data_hora=F('data'))
                                       .annotate(tipo=Value(3, output_field=IntegerField())) \
                                       .values('posicao_jogador', 'data_hora', 'tipo').order_by('data_hora', 'posicao_jogador'))
            
            resultados = resultados_desafios
            resultados.extend(resultados_decaimentos)
            resultados.extend(resultados_remocoes)
            
            resultados.sort(key=lambda x: x['data_hora'])
            
            for indice, resultado in enumerate(resultados):
                if resultado['tipo'] in [1, 2]:
                    posicao_atual += resultado['alteracao_total']
                elif resultado['tipo'] == 3:
                    if resultado['posicao_jogador'] < posicao_atual:
                        posicao_atual -= 1
                        
                if indice == len(resultados)-1 or (resultado['data_hora'] != resultados[indice+1]['data_hora']):
                    jogador.grafico_variacao_posicao.append({'x': resultado['data_hora'].strftime('%d/%m/%Y %H:%M'), 'y': posicao_atual})
                        
        # Adicionar últimos desafios
        jogador.ultimos_desafios = list(reversed(todos_desafios[-3:]))
            
#         jogador.qtd_lutas = JogadorLuta.objects.filter(jogador=jogador).count()
        jogador.qtd_lutas = DesafioLadder.objects.filter(Q(desafiante=jogador) | Q(desafiado=jogador)) \
            .aggregate(qtd_lutas=Sum(F('score_desafiante') + F('score_desafiado')))['qtd_lutas']
        
        # Adicionar top 5 personagens mais usados
        jogador.top_5_personagens = JogadorLuta.objects.filter(jogador=jogador, personagem__isnull=False).values('personagem') \
            .annotate(qtd_lutas=Count('personagem')).order_by('-qtd_lutas')[:5]

        # Buscar personagens para preencher nome
        personagens_top_5 = Personagem.objects.filter(id__in=[registro['personagem'] for registro in jogador.top_5_personagens])
        for registro in jogador.top_5_personagens:
            for personagem in personagens_top_5:
                if registro['personagem'] == personagem.id:
                    registro['personagem'] = personagem
                    break
                
    return render(request, 'jogadores/detalhar_jogador.html', {'jogador': jogador, 'desafios': desafios})

def detalhar_stage_id(request, stage_id):
    """Detalha uma stage específica"""
    stage = get_object_or_404(Stage, id=stage_id)
    
    # Definir quantidade de lutas e maior ganhador
    stage.qtd_lutas = Luta.objects.filter(lutaladder__desafio_ladder__cancelamentodesafioladder__isnull=True, stage=stage).count()
    
    if stage.qtd_lutas > 0:
        # Guarda maior quantidade de vitórias para garantir que apenas um possua essa quantidade
        stage.maior_qtd_vitorias = Luta.objects.filter(lutaladder__desafio_ladder__cancelamentodesafioladder__isnull=True,
                                                   stage=stage, ganhador__isnull=False).order_by('ganhador').values('ganhador') \
            .annotate(qtd_vitorias=Count('ganhador')).aggregate(maior_qtd_vitorias=Max('qtd_vitorias'))['maior_qtd_vitorias'] or 0
        
        if stage.maior_qtd_vitorias > 0:
            jogadores_com_mais_vitorias = Luta.objects.filter(lutaladder__desafio_ladder__cancelamentodesafioladder__isnull=True,
                                                       stage=stage, ganhador__isnull=False).order_by('ganhador').values('ganhador') \
                .annotate(qtd_vitorias=Count('ganhador')).filter(qtd_vitorias=stage.maior_qtd_vitorias)
            if len(jogadores_com_mais_vitorias) == 1:
                stage.maior_ganhador = Jogador.objects.get(id=jogadores_com_mais_vitorias[0]['ganhador'])
            
        # Preparar o top 5 de mais vitórias
        stage.top_5_ganhadores = Luta.objects.filter(lutaladder__desafio_ladder__cancelamentodesafioladder__isnull=True,
                                                   stage=stage, ganhador__isnull=False).order_by('ganhador').values('ganhador') \
            .annotate(qtd_vitorias=Count('ganhador')).order_by('-qtd_vitorias')[:5]
            
        # Buscar jogadores para preencher nome
        jogadores_top_5 = Jogador.objects.filter(id__in=[registro['ganhador'] for registro in stage.top_5_ganhadores])
        for registro in stage.top_5_ganhadores:
            for jogador in jogadores_top_5:
                if registro['ganhador'] == jogador.id:
                    registro['ganhador'] = jogador
                    break
    
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
        
#         else:
#             print(form_jogador.errors)
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
    
    # Carregar stages válidas
    stages_validas = [stage_id for stage_id in Stage.objects.filter(stagevalidaladder__isnull=False, 
                                                                             stagevalidaladder__retorno=False).values_list('id', flat=True)]
    stages_validas_retorno = [stage_id for stage_id in Stage.objects.filter(stagevalidaladder__isnull=False, 
                                                                             stagevalidaladder__retorno=True).values_list('id', flat=True)]
    
    if request.POST:
        form_stages_validas = StagesValidasForm(request.POST)
        
        if form_stages_validas.is_valid():
            try:
                with transaction.atomic():
#                     print(form_stages_validas.cleaned_data)
                    retorno = form_stages_validas.cleaned_data['retorno']
                    
                    stages_validas_atualmente = list(Stage.objects.filter(stagevalidaladder__isnull=False, 
                                                                          stagevalidaladder__retorno=retorno).values_list('id', flat=True))
#                     print(stages_validas_atualmente)
                    
                    novas_stages_validas = Stage.objects.filter(id__in=form_stages_validas.cleaned_data['stages_validas'])
                    for stage in novas_stages_validas:
                        if stage.id not in stages_validas_atualmente:
                            nova_stage_valida = StageValidaLadder(stage=stage, retorno=retorno)
                            nova_stage_valida.save()
                            
                        else:
                            stages_validas_atualmente.remove(stage.id)
                            
                    # Invalidar stages que não tenham sido seleciondas (não foram removidas na etapa anterior)
                    StageValidaLadder.objects.filter(stage__id__in=stages_validas_atualmente).delete()
                
                    return redirect(reverse('stages:listar_stages_validas'))
            except Exception as e:
                messages.error(request, str(e))
    else:
        # Preparar form
        form_stages_validas = StagesValidasForm()
    
    return render(request, 'stages/editar_stages_validas.html', {'form_stages_validas': form_stages_validas, 'stages_validas': stages_validas,
                                                                 'stages_validas_retorno': stages_validas_retorno})

def listar_desafios_jogador(request, username):
    """Listar desafios de um jogador pelo nick"""
    jogador = get_object_or_404(Jogador, user__username=username)
    
    # Buscar desafios participados
    desafios = DesafioLadder.objects.filter(Q(desafiante=jogador) | Q(desafiado=jogador)).order_by('data_hora').select_related('desafiante', 'desafiado')
    
    return render(request, 'jogadores/listar_desafios_jogador.html', {'jogador': jogador, 'desafios': desafios})

@login_required
def avaliar_jogador(request, username):
    """Deixar feedback para um jogador"""
    jogador = get_object_or_404(Jogador, user__username=username)
    
    if jogador == request.user.jogador:
        messages.error(request, 'Feedbacks devem ser feitos para outros jogadores')
        return redirect(reverse('jogadores:detalhar_jogador', kwargs={'username': username}))
    
    if request.POST:
        form_feedback = FeedbackForm(request.POST)
        
        if form_feedback.is_valid():
            try:
                with transaction.atomic():
                    feedback = form_feedback.save(commit=False)
                    
                    feedback.avaliador = request.user.jogador
                    feedback.data_hora = timezone.localtime()
                    feedback.avaliado = jogador
                    feedback.save()
                                    
                    return redirect(reverse('jogadores:detalhar_jogador', kwargs={'username': username}))
            except Exception as e:
                messages.error(request, str(e))
    else:
        # Preparar form
        form_feedback = FeedbackForm()
    
    return render(request, 'jogadores/avaliar_jogador.html', {'form_feedback': form_feedback, 'jogador': jogador})

@login_required
def listar_avaliacoes(request):
    """Listar feedbacks de um jogador"""
    jogador = request.user.jogador
    
    feedbacks = Feedback.objects.filter(avaliado=jogador)
    
    return render(request, 'jogadores/listar_avaliacoes.html', {'feedbacks': feedbacks})

def listar_desafiaveis(request):
    """Listar jogadores desafiáveis por um jogador usando ou não coringa em determinada data/hora"""
    data = {}
    if not request.POST:
        data['mensagem_erro'] = 'Requisição deve ser POST'
        return JsonResponse(data)
        
    jogador_id = request.POST.get('jogador_id')
    if Jogador.objects.filter(id=jogador_id).exists():
        jogador = Jogador.objects.get(id=jogador_id)
    else:
        data['mensagem_erro'] = 'Id de jogador informado inexistente'
        return JsonResponse(data)
    
    data_hora = request.POST.get('data_hora')
    try:
        data_hora = timezone.make_aware(datetime.datetime.strptime(data_hora, '%d/%m/%Y %H:%M'), timezone.get_current_timezone())
    except:
        data['mensagem_erro'] = 'Data/hora deve estar no formato DD/MM/AAAA hh:mm'
        return JsonResponse(data)
        
    coringa = int(request.POST.get('coringa', 0)) == 1
    
    try:
        desafiaveis = buscar_desafiaveis(jogador, data_hora, coringa, False)
    except ValueError as e:
        data['mensagem_erro'] = str(e)
        return JsonResponse(data)
    
    data['desafiaveis'] = [{'id':desafiavel.id, 'nick': desafiavel.nick} for desafiavel in desafiaveis]
    return JsonResponse(data)
