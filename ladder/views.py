# -*- coding: utf-8 -*-
"""Views para ladder"""

import datetime

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.db.models.aggregates import Count
from django.db.models.expressions import Case, When, F, Value
from django.db.models.fields import IntegerField
from django.db.models.query_utils import Q
from django.forms.formsets import formset_factory
from django.http.response import Http404, JsonResponse
from django.shortcuts import get_object_or_404, render, redirect
from django.urls.base import reverse
from django.utils import timezone

from jogadores.models import Jogador
from ladder.forms import DesafioLadderForm, DesafioLadderLutaForm, \
    RemocaoJogadorForm, PermissaoAumentoRangeForm
from ladder.models import PosicaoLadder, HistoricoLadder, Luta, JogadorLuta, \
    DesafioLadder, CancelamentoDesafioLadder, InicioLadder, DecaimentoJogador, \
    PermissaoAumentoRange, RemocaoJogador, SeasonPosicaoFinal, Season, \
    SeasonPosicaoInicial
from ladder.utils import recalcular_ladder, validar_e_salvar_lutas_ladder, \
    remover_jogador
import pandas as pd
from smashLadder.management.commands.analise import analisar_resultado_acumulado_entre_jogadores, \
    analisar_resultado_acumulado_para_um_jogador, \
    analisar_vitorias_contra_personagens_para_um_jogador, \
    analisar_resultados_por_posicao, analisar_resultados_por_dif_de_posicao, \
    analisar_vitorias_por_personagem, analisar_resultados_stages_para_um_jogador, \
    analisar_vitorias_desafio_para_um_jogador
from smashLadder.utils import mes_ano_ant, mes_ano_prox


MENSAGEM_ERRO_EDITAR_DESAFIO_CANCELADO = 'Não é possível editar desafio cancelado'
MENSAGEM_ERRO_EDITAR_DESAFIO_SEASON_ANTERIOR = 'Não é possível editar desafio de Season anterior'

MENSAGEM_SUCESSO_ADD_DESAFIO_LADDER = 'Desafio inserido com sucesso! Peça a um administrador para validar'
MENSAGEM_SUCESSO_CANCELAR_DESAFIO_LADDER = 'Desafio cancelado com sucesso'
MENSAGEM_SUCESSO_CANCELAR_MULTIPLOS_DESAFIOS_LADDER = 'Desafios de ladder cancelados com sucesso'
MENSAGEM_SUCESSO_EDITAR_DESAFIO_LADDER = 'Desafio editado com sucesso!'
MENSAGEM_SUCESSO_VALIDAR_DESAFIO_LADDER = 'Desafio validado com sucesso!'

MENSAGEM_SUCESSO_CANCELAR_REMOCAO_JOGADOR_LADDER = 'Remoção cancelada com sucesso'
MENSAGEM_ERRO_CANCELAR_REMOCAO_INATIVIDADE= 'Não é possível cancelar remoções por inatividade'

@login_required
def add_desafio_ladder(request):
    """Adiciona desafio para ladder"""
    # Preparar formset
    DesafioLadderLutaFormSet = formset_factory(DesafioLadderLutaForm, extra=DesafioLadder.MELHOR_DE)
    formset_lutas = DesafioLadderLutaFormSet(request.POST or None, prefix='desafio_ladder_luta')
    for form_luta in formset_lutas:
        form_luta.fields['ganhador'].required = False
    
    if request.POST:
        form_desafio_ladder = DesafioLadderForm(request.POST, initial={'adicionado_por': request.user.jogador.id}, admin=request.user.jogador.admin)
        form_desafio_ladder.fields['adicionado_por'].disabled = True
        
        if form_desafio_ladder.is_valid():
            
            # Descobrir quantas lutas devem ser cadastradas a partir do resultado
            dados_form_desafio_ladder = form_desafio_ladder.cleaned_data
            lutas_total = dados_form_desafio_ladder['score_desafiante'] + dados_form_desafio_ladder['score_desafiado']
            
            # Validar formset com dados do form de desafio de ladder
            DesafioLadderLutaFormSet = formset_factory(DesafioLadderLutaForm, extra=DesafioLadder.MELHOR_DE, min_num=lutas_total, 
                                                        max_num=lutas_total)
            formset_lutas = DesafioLadderLutaFormSet(request.POST, prefix='desafio_ladder_luta')
            for form_luta in formset_lutas:
                form_luta.fields['ganhador'].required = False
            
            if formset_lutas.is_valid():
                try:
                    with transaction.atomic():
                        desafio_ladder = form_desafio_ladder.save(commit=False)
                        
                        # Adicionar posições
                        desafio_ladder.posicao_desafiante = desafio_ladder.desafiante.posicao_em(desafio_ladder.data_hora)
                        desafio_ladder.posicao_desafiado = desafio_ladder.desafiado.posicao_em(desafio_ladder.data_hora)
                        
                        desafio_ladder.save()
                        
                        # Validar lutas
                        validar_e_salvar_lutas_ladder(desafio_ladder, formset_lutas)
                        
                        messages.success(request, MENSAGEM_SUCESSO_ADD_DESAFIO_LADDER)
                        
                        # Se jogador que adicionou foi participante, perguntar feedback
                        if request.user.jogador.id == desafio_ladder.desafiante.id:
                            url_feedback = reverse('jogadores:avaliar_jogador', kwargs={'username': desafio_ladder.desafiado.user.username})
                            mensagem_feedback = f"""Aproveite para adicionar um <a href="{url_feedback}">feedback</a> para seu adversário!"""
                            messages.info(request, mensagem_feedback, 'safe')
                        
                        if request.user.jogador.id == desafio_ladder.desafiado.id:
                            url_feedback = reverse('jogadores:avaliar_jogador', kwargs={'username': desafio_ladder.desafiante.user.username})
                            mensagem_feedback = f"""Aproveite para adicionar um <a href="{url_feedback}">feedback</a> para seu adversário!"""
                            messages.info(request, mensagem_feedback, 'safe')
                            
                        return redirect(reverse('ladder:detalhar_desafio_ladder', kwargs={'desafio_id': desafio_ladder.id}))
                    
                except Exception as e:
                    messages.error(request, e)
            else:
                for erro in formset_lutas.non_form_errors():
                    # Sobrescrever erro de quantidade de forms
                    if erro.startswith(f'Por favor envie {lutas_total} ou '):
                        messages.error(request, f'Preencha apenas as lutas 1 a {lutas_total}')
                    else:
                        messages.error(request, erro)
        
        else:
            for erro in form_desafio_ladder.non_field_errors():
                messages.error(request, erro)
                
    else:
        form_desafio_ladder = DesafioLadderForm(initial={'adicionado_por': request.user.jogador.id, 'data_hora': timezone.localtime()}, 
                                                admin=request.user.jogador.admin)
        form_desafio_ladder.fields['adicionado_por'].disabled = True
        
    return render(request, 'ladder/adicionar_desafio_ladder.html', {'form_desafio_ladder': form_desafio_ladder, 
                                                                       'formset_lutas': formset_lutas})
    
def detalhar_ladder_atual(request):
    """Detalhar posição da ladder atual"""
    ladder = list(PosicaoLadder.objects.all().order_by('posicao').select_related('jogador__user'))
    
    data_atual = timezone.localtime()
    data_mes_anterior = data_atual.replace(day=1) - datetime.timedelta(days=1)
    
    qtd_desafios = DesafioLadder.objects.filter(data_hora__month=data_atual.month, data_hora__year=data_atual.year).count()
    
    # Comparar com ladder anterior
    if HistoricoLadder.objects.filter(mes=data_mes_anterior.month, ano=data_mes_anterior.year).exists():
        ladder_anterior = HistoricoLadder.objects.filter(mes=data_mes_anterior.month, ano=data_mes_anterior.year).select_related('jogador')
    else:
        ladder_anterior = InicioLadder.objects.all().select_related('jogador')
    ladder_anterior = list(ladder_anterior)
    
    # Considerar última posição de ladder atual caso jogador não esteja na anterior
    for posicao_ladder in ladder:
        preencheu_alteracao = False
        # Procurar jogador na ladder anterior
        for posicao_ladder_anterior in ladder_anterior:
            if posicao_ladder_anterior.jogador == posicao_ladder.jogador:
                posicao_ladder.alteracao = posicao_ladder_anterior.posicao - posicao_ladder.posicao

                preencheu_alteracao = True
                break
            
        if not preencheu_alteracao:
            # Se jogador não estava na ladder anterior, buscar posição em seu primeiro desafio da ladder atual
            primeiro_desafio = DesafioLadder.validados.filter((Q(desafiante=posicao_ladder.jogador) | Q(desafiado=posicao_ladder.jogador)), 
                                                              data_hora__month=data_atual.month, data_hora__year=data_atual.year).annotate(
                                                                  posicao=Case(When(desafiante=posicao_ladder.jogador, then=F('posicao_desafiante')),
                                                                               When(desafiado=posicao_ladder.jogador, then=F('posicao_desafiado')))) \
                                                                               .order_by('data_hora')[0]
                
            posicao_ladder.alteracao = primeiro_desafio.posicao - posicao_ladder.posicao

    # Guardar destaques da ladder
    destaques = {}
    
    if DesafioLadder.validados.exists():
        
        # Verificar qual jogador possui mais desafios na ladder
        # Qtd de desafios feitos
        desafios_feitos = dict(Jogador.objects.all().annotate(qtd_desafios=(Count(Case(
            When(desafiante__cancelamentodesafioladder__isnull=True, desafiante__admin_validador__isnull=False, 
                 desafiante__data_hora__month=data_atual.month, desafiante__data_hora__year=data_atual.year, then=True),
            output_field=IntegerField(),
        )))).values_list('nick', 'qtd_desafios'))
        
        # Qtd de desafios recebidos
        desafios_recebidos = dict(Jogador.objects.all().annotate(qtd_desafios=(Count(Case(
            When(desafiado__cancelamentodesafioladder__isnull=True, desafiado__admin_validador__isnull=False, 
                 desafiado__data_hora__month=data_atual.month, desafiado__data_hora__year=data_atual.year, then=True),
            output_field=IntegerField(),
        )))).values_list('nick', 'qtd_desafios'))
    
        # Somar
        desafios = { k: desafios_feitos.get(k, 0) + desafios_recebidos.get(k, 0) for k in set(desafios_feitos) | set(desafios_recebidos) }
        
        valor_maximo = desafios[(max(desafios, key=lambda key: desafios[key]))]
        if valor_maximo > 0:
            destaques['jogadores_mais_desafios'] = [key for key, value in desafios.items() if value == valor_maximo]
        
        # Sequencia de vitórias superior a 5
        # Buscar todos os desafios
        desafios = DesafioLadder.validados.order_by('data_hora').select_related('desafiante', 'desafiado')
        
        # Buscar participantes da ladder
        jogadores = {posicao.jogador.nick: 0 for posicao in ladder}
        
        # Iterar por desafios, cada ganhador adiciona 1 na streak, cada perdedor reseta
        for desafio in desafios:
            if desafio.score_desafiante > desafio.score_desafiado:
                if desafio.desafiante.nick in jogadores:
                    jogadores[desafio.desafiante.nick] += 1
                if desafio.desafiado.nick in jogadores:
                    jogadores[desafio.desafiado.nick] = 0
            else:
                if desafio.desafiado.nick in jogadores:
                    jogadores[desafio.desafiado.nick] += 1
                if desafio.desafiante.nick in jogadores:
                    jogadores[desafio.desafiante.nick] = 0
        
        # Destacar quem tiver mais de 5 vitórias consecutivas
        destaques['jogadores_streak_vitorias'] = [key for key, value in jogadores.items() if value >= 5]
        for posicao_ladder in ladder:
            if posicao_ladder.jogador.nick in destaques['jogadores_streak_vitorias']:
                posicao_ladder.jogador.streak = jogadores[posicao_ladder.jogador.nick]
                
        # Verificar jogadores que fizeram 5 defesas com sucesso
        defesas_sucesso_5 = dict(DesafioLadder.validados.filter(data_hora__month=data_atual.month, data_hora__year=data_atual.year, 
                                                                score_desafiado__gt=F('score_desafiante')).values('desafiado').order_by('desafiado') \
             .annotate(qtd_vitorias=Count('desafiado')).filter(qtd_vitorias__gte=5).values_list('desafiado__nick', 'qtd_vitorias'))
        
        # Destacar jogadores que fizeram 5 defesas com sucesso
        destaques['jogadores_5_defesas'] = [key for key, value in defesas_sucesso_5.items()]
        for posicao_ladder in ladder:
            if posicao_ladder.jogador.nick in destaques['jogadores_5_defesas']:
                posicao_ladder.jogador.qtd_defesas = defesas_sucesso_5[posicao_ladder.jogador.nick]
                
        # Destaque para uso de coringa com sucesso subindo mais de 10 posições
        vitorias_coringa = DesafioLadder.validados.filter(data_hora__month=data_atual.month, data_hora__year=data_atual.year) \
            .filter(desafio_coringa=True, score_desafiante__gt=F('score_desafiado'), 
                    posicao_desafiante__gte=(F('posicao_desafiado') + 10)).select_related('desafiante')
        destaques['vitoria_coringa_10_posicoes'] = [vitoria.desafiante.nick for vitoria in vitorias_coringa]
                
        # Marcar todos os jogadores com destaques
        for posicao_ladder in ladder:
            for destaque in destaques:
                if posicao_ladder.jogador.nick in destaques[destaque]:
                    posicao_ladder.jogador.tem_destaque = True
                    break
        
    return render(request, 'ladder/ladder_atual.html', {'ladder': ladder, 'destaques': destaques, 'qtd_desafios': qtd_desafios})
    
def detalhar_ladder_historico(request, ano, mes):
    """Detalhar histórico da ladder em mês/ano específico"""
    # TODO adicionar destaques
    
    # Testa se existe histórico para mês/ano apontados
    if not HistoricoLadder.objects.filter(ano=ano, mes=mes).exists():
        raise Http404('Não há ladder para o mês/ano inseridos')
    ladder = HistoricoLadder.objects.filter(ano=ano, mes=mes).order_by('posicao') \
        .select_related('jogador__user')
    
    # Pegar mês/ano anterior
    mes_anterior, ano_anterior = mes_ano_ant(mes, ano)
    
    qtd_desafios = DesafioLadder.objects.filter(data_hora__month=mes, data_hora__year=ano).count()
    
    # Comparar com ladder anterior
    if HistoricoLadder.objects.filter(mes=mes_anterior, ano=ano_anterior).exists():
        ladder_anterior = HistoricoLadder.objects.filter(mes=mes_anterior, ano=ano_anterior)
    else:
        ladder_anterior = InicioLadder.objects.all()
    ladder_anterior = list(ladder_anterior)
    
    # Considerar última posição de ladder atual caso jogador não esteja na anterior
    for posicao_ladder in ladder:
        preencheu_alteracao = False
        # Procurar jogador na ladder anterior
        for posicao_ladder_anterior in ladder_anterior:
            if posicao_ladder_anterior.jogador_id == posicao_ladder.jogador_id:
                posicao_ladder.alteracao = posicao_ladder_anterior.posicao - posicao_ladder.posicao

                preencheu_alteracao = True
                break
            
        if not preencheu_alteracao:
            # Se jogador não estava na ladder anterior, buscar posição em seu primeiro desafio da ladder atual
            primeiro_desafio = DesafioLadder.validados.filter((Q(desafiante=posicao_ladder.jogador) | Q(desafiado=posicao_ladder.jogador)), 
                                                              data_hora__month=mes, data_hora__year=ano).annotate(
                                                                  posicao=Case(When(desafiante=posicao_ladder.jogador, then=F('posicao_desafiante')),
                                                                               When(desafiado=posicao_ladder.jogador, then=F('posicao_desafiado')))) \
                                                                               .order_by('data_hora')[0]
                 
            posicao_ladder.alteracao = primeiro_desafio.posicao - posicao_ladder.posicao
            
    # Guardar destaques da ladder
    destaques = {}
    
    desafios_mes = DesafioLadder.validados.filter(data_hora__month=mes, data_hora__year=ano)
    if desafios_mes.exists():
        # Procurar destaques
        
        # Verificar jogadores que fizeram 5 defesas com sucesso
        defesas_sucesso_5 = dict(desafios_mes.filter(score_desafiado__gt=F('score_desafiante')).values('desafiado').order_by('desafiado') \
             .annotate(qtd_vitorias=Count('desafiado')).filter(qtd_vitorias__gte=5).values_list('desafiado__nick', 'qtd_vitorias'))
        
        # Destacar jogadores que fizeram 5 defesas com sucesso
        destaques['jogadores_5_defesas'] = [key for key, _ in defesas_sucesso_5.items()]
        for posicao_ladder in ladder:
            if posicao_ladder.jogador.nick in destaques['jogadores_5_defesas']:
                posicao_ladder.jogador.qtd_defesas = defesas_sucesso_5[posicao_ladder.jogador.nick]
        
        # Destaque para uso de coringa com sucesso subindo mais de 10 posições
        vitorias_coringa = desafios_mes.filter(desafio_coringa=True, score_desafiante__gt=F('score_desafiado'),
                                                          posicao_desafiante__gte=(F('posicao_desafiado') + 10)).select_related('desafiante')
        destaques['vitoria_coringa_10_posicoes'] = [vitoria.desafiante.nick for vitoria in vitorias_coringa]

        # Marcar todos os jogadores com destaques
        for posicao_ladder in ladder:
            for destaque in destaques:
                if posicao_ladder.jogador.nick in destaques[destaque]:
                    posicao_ladder.jogador.tem_destaque = True
                    break
    
    return render(request, 'ladder/ladder_historico.html', {'ladder': ladder, 'ano': ano, 'mes': mes, 'destaques': destaques,
                                                            'qtd_desafios': qtd_desafios})


def detalhar_hall_fama(request, ano, indice):
    """Detalhar Season no Hall da Fama"""
    # TODO adicionar destaques
    
    # Testa se existe histórico para mês/ano apontados
    if not SeasonPosicaoFinal.objects.filter(season__ano=ano, season__indice=indice).exists():
        raise Http404('Não há registro no Hall da Fama para o índice/ano inseridos')
    ladder = SeasonPosicaoFinal.objects.filter(season__ano=ano, season__indice=indice).order_by('posicao') \
        .select_related('jogador__user')
    
    # Buscar season
    season = Season.objects.get(ano=ano, indice=indice)
    
    qtd_desafios = DesafioLadder.objects.filter(data_hora__range=[season.data_inicio, season.data_fim]).count()
    
    # Comparar com início da season
    ladder_anterior = list(SeasonPosicaoInicial.objects.filter(season__ano=ano, season__indice=indice).order_by('posicao'))
    
    # Considerar última posição de ladder atual caso jogador não esteja na anterior
    for posicao_ladder in ladder:
        preencheu_alteracao = False
        # Procurar jogador na ladder anterior
        for posicao_ladder_anterior in ladder_anterior:
            if posicao_ladder_anterior.jogador_id == posicao_ladder.jogador_id:
                posicao_ladder.alteracao = posicao_ladder_anterior.posicao - posicao_ladder.posicao

                preencheu_alteracao = True
                break
            
        if not preencheu_alteracao:
            # Se jogador não estava na ladder anterior, buscar posição em seu primeiro desafio da ladder atual
            primeiro_desafio = DesafioLadder.validados.filter((Q(desafiante=posicao_ladder.jogador) | Q(desafiado=posicao_ladder.jogador)), 
                                                              data_hora__range=[season.data_inicio, season.data_fim]).annotate(
                                                                  posicao=Case(When(desafiante=posicao_ladder.jogador, then=F('posicao_desafiante')),
                                                                               When(desafiado=posicao_ladder.jogador, then=F('posicao_desafiado')))) \
                                                                               .order_by('data_hora')[0]
                 
            posicao_ladder.alteracao = primeiro_desafio.posicao - posicao_ladder.posicao
            
    # Guardar destaques da ladder
    destaques = {}
    
    desafios_season = DesafioLadder.validados.filter(data_hora__range=[season.data_inicio, season.data_fim])
    if desafios_season.exists():
        # Procurar destaques
        
        # Verificar jogadores que fizeram 5 defesas com sucesso
        defesas_sucesso_5 = dict(desafios_season.filter(score_desafiado__gt=F('score_desafiante')).values('desafiado').order_by('desafiado') \
             .annotate(qtd_vitorias=Count('desafiado')).filter(qtd_vitorias__gte=5).values_list('desafiado__nick', 'qtd_vitorias'))
        
        # Destacar jogadores que fizeram 5 defesas com sucesso
        destaques['jogadores_5_defesas'] = [key for key, _ in defesas_sucesso_5.items()]
        for posicao_ladder in ladder:
            if posicao_ladder.jogador.nick in destaques['jogadores_5_defesas']:
                posicao_ladder.jogador.qtd_defesas = defesas_sucesso_5[posicao_ladder.jogador.nick]
        
        # Destaque para uso de coringa com sucesso subindo mais de 10 posições
        vitorias_coringa = desafios_season.filter(desafio_coringa=True, score_desafiante__gt=F('score_desafiado'),
                                                          posicao_desafiante__gte=(F('posicao_desafiado') + 10)).select_related('desafiante')
        destaques['vitoria_coringa_10_posicoes'] = [vitoria.desafiante.nick for vitoria in vitorias_coringa]

        # Marcar todos os jogadores com destaques
        for posicao_ladder in ladder:
            for destaque in destaques:
                if posicao_ladder.jogador.nick in destaques[destaque]:
                    posicao_ladder.jogador.tem_destaque = True
                    break
    
    return render(request, 'ladder/hall_fama.html', {'ladder': ladder, 'ano': ano, 'indice': indice, 'destaques': destaques,
                                                            'qtd_desafios': qtd_desafios})

def listar_ladder_historico(request):
    """Listar históricos de ladder por ano/mês"""
    # Buscar anos e meses para listagem
    lista_ladders = HistoricoLadder.objects.all().order_by('-ano', '-mes') \
                         .values('mes', 'ano').distinct()
    
    return render(request, 'ladder/listar_ladder_historico.html', {'lista_ladders': lista_ladders})

def listar_hall_fama(request):
    """Listar Hall da Fama de Seasons"""
    # Buscar anos e meses para listagem
    lista_ladders = Season.objects.filter(data_fim__lte=timezone.localdate()).order_by('-ano', '-indice') \
                         .values('indice', 'ano').distinct()
    
    return render(request, 'ladder/listar_hall_fama.html', {'lista_ladders': lista_ladders})

@login_required
def add_permissao_aumento_range(request):
    """Adicionar permissão de aumento de range"""
    # Verificar se usuário é admin
    if not request.user.jogador.admin:
        raise PermissionDenied
        
    if request.POST:
        form_permissao_aumento_range = PermissaoAumentoRangeForm(request.POST, initial={'admin_permissor': request.user.jogador.id,
                                                                                        'data_hora': timezone.localtime()})
        form_permissao_aumento_range.fields['admin_permissor'].disabled = True
        form_permissao_aumento_range.fields['data_hora'].disabled = True
        
        if form_permissao_aumento_range.is_valid():
            try:
                with transaction.atomic():
                    permissao = form_permissao_aumento_range.save(commit=False)
                    permissao.save()
                    
                    messages.success(request, PermissaoAumentoRange.MENSAGEM_SUCESSO_PERMISSAO_AUMENTO_RANGE)
                    return redirect(reverse('jogadores:detalhar_jogador', kwargs={'username': permissao.jogador.user.username}))
                    
            except Exception as e:
                messages.error(request, e)
        
        else:
            for erro in form_permissao_aumento_range.non_field_errors():
                messages.error(request, erro)
    else:
        form_permissao_aumento_range = PermissaoAumentoRangeForm(initial={'admin_permissor': request.user.jogador.id})
        form_permissao_aumento_range.fields['admin_permissor'].disabled = True
        form_permissao_aumento_range.fields['data_hora'].disabled = True
        
    return render(request, 'ladder/adicionar_permissao_aumento_range.html', {'form_permissao_aumento_range': form_permissao_aumento_range})

@login_required
def remover_permissao_aumento_range(request, permissao_id=None):
    """Remover permissão de aumento de range"""
    # Verificar se usuário é admin
    if not request.user.jogador.admin:
        raise PermissionDenied
    
    # Se for enviada uma permissão, mostrar tela para decidir remover
    if permissao_id:
        # Carregar permissão
        permissao = get_object_or_404(PermissaoAumentoRange.objects.select_related('jogador', 'admin_permissor'), pk=permissao_id)
        
        if request.POST:
            try:
                with transaction.atomic():
                    if permissao.is_valida():
                        permissao.delete()
                        messages.success(request, PermissaoAumentoRange.MENSAGEM_SUCESSO_REMOCAO_PERMISSAO)
                    else:
                        raise ValueError(PermissaoAumentoRange.MENSAGEM_ERRO_DESAFIO_UTILIZANDO_PERMISSAO)
                    
            except Exception as e:
                messages.error(request, e)
            
    permissoes = PermissaoAumentoRange.objects.filter(data_hora__gte=timezone.localtime() \
                                                      - datetime.timedelta(hours=PermissaoAumentoRange.PERIODO_VALIDADE)) \
                                                      .select_related('admin_permissor', 'jogador')
    permissoes = [permissao for permissao in permissoes if permissao.is_valida()]
    return render(request, 'ladder/remover_permissao_aumento_range.html', {'permissoes': permissoes})

def detalhar_luta(request, luta_id):
    """Detalhar uma luta"""
    luta = get_object_or_404(Luta.objects.select_related('lutaladder__desafio_ladder', 'ganhador'), id=luta_id)
    participantes = JogadorLuta.objects.filter(luta=luta).select_related('jogador__user', 'personagem')
    
    return render(request, 'ladder/luta.html', {'luta': luta, 'participantes': participantes})

@login_required
def cancelar_desafio_ladder(request, desafio_id):
    """Cancelar um desafio de ladder"""
    desafio_ladder = get_object_or_404(DesafioLadder, id=desafio_id)
    
    # Se já for cancelado, retornar para detalhamento
    if desafio_ladder.is_cancelado():
        messages.error(request, f'Cancelamento já foi feito por {desafio_ladder.cancelamentodesafioladder.jogador.nick}')
        return redirect(reverse('ladder:detalhar_desafio_ladder', kwargs={'desafio_id': desafio_id}))
    if desafio_ladder.fora_da_season():
        messages.error(request, 'Não é possível cancelar desafio de Season anterior')
        return redirect(reverse('ladder:detalhar_desafio_ladder', kwargs={'desafio_id': desafio_id}))
    
    # Verificar se usuário logado pode cancelar desafio
    # Admins podem ver tudo
    if request.user.jogador.admin:
        pass
    # Jogadores comuns podem ver apenas os desafios que criaram e não foram validados
    elif desafio_ladder.is_validado():
        raise PermissionDenied
    elif request.user.jogador != desafio_ladder.adicionado_por:
        raise PermissionDenied
    
    if request.POST:
        confirmacao = request.POST.get('salvar')
        if confirmacao != None:
            # Cancelar desafio
            try:
                with transaction.atomic():
                    # Gerar cancelamento para desafio
                    cancelamento = CancelamentoDesafioLadder(desafio_ladder=desafio_ladder, jogador=request.user.jogador)
                    cancelamento.save()
                    
                    # Se validado, verificar alterações decorrentes da operação
                    if desafio_ladder.is_validado():
                        # Recalcula ladder para verificar se cancelamento é válido
                        recalcular_ladder(desafio_ladder)
                        
                        # Se desafio tinha desafio coringa, verificar último uso do jogador
                        if desafio_ladder.desafio_coringa:
                            desafiante = desafio_ladder.desafiante
                            # Se esse foi o último uso, voltar para penúltimo ou deixar nulo
                            if desafio_ladder.data_hora.date() == desafiante.ultimo_uso_coringa:
                                # Verifica se existe uso anterior
                                if DesafioLadder.objects.filter(data_hora__lt=desafio_ladder.data_hora, 
                                                                 cancelamentodesafioladder__isnull=True,
                                                                 admin_validador__isnull=False, desafiante=desafiante, 
                                                                 desafio_coringa=True).exists():
                                    data_penultimo_uso = DesafioLadder.objects.filter(data_hora__lt=desafio_ladder.data_hora, 
                                                                                  cancelamentodesafioladder__isnull=True,
                                                                                  admin_validador__isnull=False, desafiante=desafiante, 
                                                                                  desafio_coringa=True).order_by('-data_hora')[0].data_hora
                                    desafiante.ultimo_uso_coringa = data_penultimo_uso
                                else:
                                    desafiante.ultimo_uso_coringa = None
                                desafiante.save()
                        
                    messages.success(request, MENSAGEM_SUCESSO_CANCELAR_DESAFIO_LADDER)
                    return redirect(reverse('ladder:detalhar_desafio_ladder', kwargs={'desafio_id': desafio_id}))
            
            except Exception as e:
                messages.error(request, str(e))
    
    return render(request, 'ladder/cancelar_desafio_ladder.html', {'desafio_ladder': desafio_ladder})

def detalhar_desafio_ladder(request, desafio_id):
    """Detalhar um desafio de ladder"""
    desafio_ladder = get_object_or_404(DesafioLadder.objects.select_related('admin_validador', 'adicionado_por', 
                                                                            'desafiante__user', 'desafiado__user'), id=desafio_id)
    
    # Buscar alterações após desafio
    desafio_ladder.alteracoes_ladder = desafio_ladder.resultadodesafioladder_set.all().annotate(alteracao=F('alteracao_posicao')*-1) \
        .order_by('-alteracao', '-id').select_related('jogador')
    
    # Verificar se usuário pode alterar desafio
    if request.user.is_authenticated:
        desafio_ladder.is_cancelavel = desafio_ladder.cancelavel_por_jogador(request.user.jogador)
        desafio_ladder.is_editavel = desafio_ladder.editavel_por_jogador(request.user.jogador)
    else:
        desafio_ladder.is_cancelavel = False
        desafio_ladder.is_editavel = False
    return render(request, 'ladder/detalhar_desafio_ladder.html', {'desafio_ladder': desafio_ladder})

@login_required
def editar_desafio_ladder(request, desafio_id):
    """Editar um desafio de ladder, apenas se não estiver validado"""
    # TODO implementar edição de desafio validado
    desafio_ladder = get_object_or_404(DesafioLadder, id=desafio_id)
    
    # Verificar se cancelado
    if desafio_ladder.is_cancelado():
        messages.error(request, MENSAGEM_ERRO_EDITAR_DESAFIO_CANCELADO)
        return redirect(reverse('ladder:detalhar_desafio_ladder', kwargs={'desafio_id': desafio_ladder.id}))
    if desafio_ladder.fora_da_season():
        messages.error(request, MENSAGEM_ERRO_EDITAR_DESAFIO_SEASON_ANTERIOR)
        return redirect(reverse('ladder:detalhar_desafio_ladder', kwargs={'desafio_id': desafio_ladder.id}))
    
    # Verificar se usuário logado pode editar desafio
    if desafio_ladder.is_validado():
        raise PermissionDenied
    # Admins e criadores podem editar
    elif request.user.jogador.admin or request.user.jogador == desafio_ladder.adicionado_por:
        pass
    else:
        raise PermissionDenied
    
    # Preparar lutas do desafio
    queryset_desafio_ladder = Luta.objects.filter(lutaladder__desafio_ladder=desafio_ladder).select_related('lutaladder') \
        .prefetch_related('jogadorluta_set')
    
    lutas_desafio_ladder = list()
    for _ in range(DesafioLadder.MELHOR_DE):
        lutas_desafio_ladder.append({})
    
    for luta in queryset_desafio_ladder:
        lutas_desafio_ladder[luta.lutaladder.indice_desafio_ladder-1] = {'id': luta.id,'ganhador': luta.ganhador, 'stage': luta.stage, 
                                   'personagem_desafiante': luta.jogadorluta_set.get(jogador=desafio_ladder.desafiante).personagem, 
                                   'personagem_desafiado': luta.jogadorluta_set.get(jogador=desafio_ladder.desafiado).personagem}
        
    # Preparar formset
    DesafioLadderLutaFormSet = formset_factory(DesafioLadderLutaForm, extra=(DesafioLadder.MELHOR_DE - len(lutas_desafio_ladder)),
                                                can_delete=True)
    formset_lutas = DesafioLadderLutaFormSet(request.POST or None, prefix='desafio_ladder_luta', initial=lutas_desafio_ladder)
    for form_luta in formset_lutas:
        form_luta.fields['ganhador'].required = False
            
    if request.POST:
        form_desafio_ladder = DesafioLadderForm(request.POST, instance=desafio_ladder, admin=request.user.jogador.admin)
        form_desafio_ladder.fields['adicionado_por'].disabled = True
        
        if form_desafio_ladder.is_valid():
            
            # Descobrir quantas lutas devem ser cadastradas a partir do resultado
            dados_form_desafio_ladder = form_desafio_ladder.cleaned_data
            lutas_total = dados_form_desafio_ladder['score_desafiante'] + dados_form_desafio_ladder['score_desafiado']
            
            # Validar formset com dados do form de desafio de ladder
            DesafioLadderLutaFormSet = formset_factory(DesafioLadderLutaForm, extra=(DesafioLadder.MELHOR_DE - len(lutas_desafio_ladder)), 
                                                        max_num=lutas_total, can_delete=True)
            formset_lutas = DesafioLadderLutaFormSet(request.POST, prefix='desafio_ladder_luta', initial=lutas_desafio_ladder)
            for form_luta in formset_lutas:
                form_luta.fields['ganhador'].required = False
            
            if formset_lutas.is_valid():
                try:
                    with transaction.atomic():
                        desafio_ladder = form_desafio_ladder.save(commit=False)
                        
                        # Adicionar posições
                        desafio_ladder.posicao_desafiante = desafio_ladder.desafiante.posicao_em(desafio_ladder.data_hora)
                        desafio_ladder.posicao_desafiado = desafio_ladder.desafiado.posicao_em(desafio_ladder.data_hora)
                        
                        desafio_ladder.save()
                        
                        # Validar lutas
                        validar_e_salvar_lutas_ladder(desafio_ladder, formset_lutas)
                        
                        messages.success(request, MENSAGEM_SUCESSO_EDITAR_DESAFIO_LADDER)
                        return redirect(reverse('ladder:detalhar_desafio_ladder', kwargs={'desafio_id': desafio_ladder.id}))
                    
                except Exception as e:
                    messages.error(request, e)
            else:
                for erro in formset_lutas.non_form_errors():
                    # Sobrescrever erro de quantidade de forms
                    if erro.startswith(f'Por favor envie {lutas_total} ou '):
                        messages.error(request, f'Preencha apenas as lutas 1 a {lutas_total}')
                    else:
                        messages.error(request, erro)
        else:
            for erro in form_desafio_ladder.non_field_errors():
                messages.error(request, erro)
    else:
        form_desafio_ladder = DesafioLadderForm(instance=desafio_ladder, admin=request.user.jogador.admin)
        form_desafio_ladder.fields['adicionado_por'].disabled = True
        
    return render(request, 'ladder/editar_desafio_ladder.html', {'form_desafio_ladder': form_desafio_ladder,
                                                                  'formset_lutas': formset_lutas})

def detalhar_regras(request):
    """Detalhar regras da ladder"""
    admins = Jogador.objects.filter(admin=True).select_related('user')
    for admin in admins:
        if admin.user.first_name or admin.user.last_name:
            admin.nome_tag = f'{admin.user.first_name} "{admin.nick}" {admin.user.last_name}'.strip()
        else:
            admin.nome_tag = admin.nick
    
    return render(request, 'ladder/regras.html', {'LIMITE_POSICOES_DESAFIO': DesafioLadder.LIMITE_POSICOES_DESAFIO, 
                                                  'MELHOR_DE': DesafioLadder.MELHOR_DE, 
                                                  'PERIODO_ESPERA_MESMOS_JOGADORES': DesafioLadder.PERIODO_ESPERA_MESMOS_JOGADORES,
                                                  'PERIODO_ESPERA_DESAFIO_CORINGA': DesafioLadder.PERIODO_ESPERA_DESAFIO_CORINGA,
                                                  'QTD_POSICOES_DECAIMENTO': DecaimentoJogador.QTD_POSICOES_DECAIMENTO,
                                                  'PERIODO_INATIVIDADE': DecaimentoJogador.PERIODO_INATIVIDADE,
                                                  'admins': admins})

def listar_desafios_ladder(request, ano=None, mes=None):
    """Listar desafios de ladder específica"""
    # Ano/mês devem estar ambos preenchidos ou ambos nulos
    # Ambos nulos significa ladder atual
    if ano == None and mes == None:
        data_atual = timezone.localdate()
        ano = data_atual.year
        mes = data_atual.month
    elif (ano == None and mes != None) or (ano != None and mes == None):
        raise Http404('Ano e mês devem ser preenchidos')
    elif mes not in [_ for _ in range(1, 13)]:
        raise Http404('Mês inválido')
    elif ano * 12 + mes > timezone.localtime().year * 12 + timezone.localtime().month:
        raise Http404('Data futura é inválida para histórico')
    
    
    # Buscar desafios para ladder especificada
    desafios_ladder = DesafioLadder.objects.filter(data_hora__month=mes, data_hora__year=ano).order_by('data_hora') \
        .select_related('desafiante__user', 'desafiado__user', 'cancelamentodesafioladder', 'admin_validador')
    
    # Verificar quais desafios usuário pode cancelar
    for desafio_ladder in desafios_ladder:
        if request.user.is_authenticated:
            desafio_ladder.is_cancelavel = desafio_ladder.cancelavel_por_jogador(request.user.jogador)
        else:
            desafio_ladder.is_cancelavel = False
    
    return render(request, 'ladder/listar_desafios_ladder.html', {'desafios_ladder': desafios_ladder, 'ano': ano, 'mes': mes})

def listar_desafios_season(request, ano, indice):
    """Listar desafios de ladder específica"""
    if Season.objects.filter(ano=ano, indice=indice).exists():
        season = Season.objects.get(ano=ano, indice=indice)
    else:
        raise Http404('Não existe Season para ano/índice')
    
    # Buscar desafios para ladder especificada
    desafios_ladder = DesafioLadder.objects.filter(data_hora__range=[season.data_inicio, season.data_fim]).order_by('data_hora') \
        .select_related('desafiante__user', 'desafiado__user', 'cancelamentodesafioladder', 'admin_validador')
    
    # Verificar quais desafios usuário pode cancelar
    for desafio_ladder in desafios_ladder:
        if request.user.is_authenticated:
            desafio_ladder.is_cancelavel = desafio_ladder.cancelavel_por_jogador(request.user.jogador)
        else:
            desafio_ladder.is_cancelavel = False
    
    return render(request, 'ladder/listar_desafios_hall_fama.html', {'desafios_ladder': desafios_ladder, 'ano': ano, 'indice': indice})

def listar_desafios_ladder_pendentes_validacao(request):
    """Listar desafios de ladder pendentes de validação"""
    # Buscar desafios pendentes
    desafios_pendentes = DesafioLadder.objects.filter(admin_validador__isnull=True, cancelamentodesafioladder__isnull=True).order_by('data_hora') \
        .select_related('desafiante__user', 'desafiado__user', 'cancelamentodesafioladder', 'admin_validador')
    
    # Verificar quais desafios usuário pode cancelar
    for desafio_ladder in desafios_pendentes:
        if request.user.is_authenticated:
            desafio_ladder.is_cancelavel = desafio_ladder.cancelavel_por_jogador(request.user.jogador)
        else:
            desafio_ladder.is_cancelavel = False
    
    return render(request, 'ladder/listar_desafios_pendente_validacao.html', {'desafios_pendentes': desafios_pendentes})

@login_required
def cancelar_remocao_jogador_ladder(request, remocao_id):
    """Cancela uma remoção que não seja por inatividade"""
    # Usuário deve ser admin
    if not request.user.jogador.admin:
        raise PermissionDenied
    
    remocao = get_object_or_404(RemocaoJogador, id=remocao_id)
    if remocao.remocao_por_inatividade:
        messages.error(request, MENSAGEM_ERRO_CANCELAR_REMOCAO_INATIVIDADE)
        return redirect(reverse('ladder:listar_remocoes_jogador_ladder')) 
    
    if request.POST:
        confirmacao = request.POST.get('salvar')
        if confirmacao != None:
            # Cancelar remoção
            try:
                with transaction.atomic():
                    # Buscar ano/mês da remoção
                    mes, ano = remocao.mes_ano_ladder
                    
                    # Apagar remoção
                    remocao.delete()
                    
                    # Recalcula ladder para verificar se cancelamento é válido
                    recalcular_ladder(mes=mes, ano=ano)
                        
                    messages.success(request, MENSAGEM_SUCESSO_CANCELAR_REMOCAO_JOGADOR_LADDER)
                    return redirect(reverse('ladder:listar_remocoes_jogador_ladder'))
            
            except Exception as e:
                # Atualizar objeto de remoção
                remocao = RemocaoJogador.objects.get(id=remocao_id)
                messages.error(request, str(e))
    
    return render(request, 'ladder/cancelar_remocao_jogador_ladder.html', {'remocao': remocao})

def listar_remocoes_jogador_ladder(request):
    """Lista remoções de jogadores da ladder"""
    remocoes = RemocaoJogador.objects.all().order_by('-data')
    
    return render(request, 'ladder/listar_remocoes_jogador_ladder.html', {'remocoes': remocoes})

@login_required
def remover_jogador_ladder(request):
    """Remove um jogador da ladder em data especificada"""
    # Usuário deve ser admin
    if not request.user.jogador.admin:
        raise PermissionDenied
    
    if request.POST:
        form_remover_jogador = RemocaoJogadorForm(request.POST, initial={'admin_removedor': request.user.jogador.id})
        form_remover_jogador.fields['admin_removedor'].disabled = True
        if form_remover_jogador.is_valid():
            try:
                with transaction.atomic():
                    remocao = form_remover_jogador.save(commit=False)
                    remocao.save()
                    remover_jogador(remocao)
            
                    messages.success(request, f'{remocao.jogador} removido da ladder com sucesso')
                    return redirect(reverse('ladder:detalhar_ladder_atual')) 
            
            except Exception as e:
                messages.error(request, str(e))
                
    else:
        form_remover_jogador = RemocaoJogadorForm(initial={'admin_removedor': request.user.jogador.id})
        form_remover_jogador.fields['admin_removedor'].disabled = True
        
    return render(request, 'ladder/remover_jogador_ladder.html', {'form_remover_jogador': form_remover_jogador})

@login_required
def validar_desafio_ladder(request, desafio_id):
    """Validar um desafio de ladder"""
    # Usuário deve ser admin
    if not request.user.jogador.admin:
        raise PermissionDenied
    
    desafio_ladder = get_object_or_404(DesafioLadder, id=desafio_id)
    
    if desafio_ladder.is_validado():
        messages.error(request, f'Validação já foi feita por {desafio_ladder.admin_validador.nick}')
        return redirect(reverse('ladder:detalhar_desafio_ladder', kwargs={'desafio_id': desafio_id}))
    if desafio_ladder.fora_da_season():
        messages.error(request, 'Não é possível validar desafio de Season anterior')
        return redirect(reverse('ladder:detalhar_desafio_ladder', kwargs={'desafio_id': desafio_id}))
    
    if request.POST:
        confirmacao = request.POST.get('salvar')

        if confirmacao != None:
            try:
                with transaction.atomic():
                    # Validação
                    
                    # Gravar validador
                    desafio_ladder.admin_validador = request.user.jogador
                    desafio_ladder.save()
                    
                    # Alterar ladder referência
                    recalcular_ladder(desafio_ladder)
                    
                    if desafio_ladder.desafio_coringa:
                        desafiante = desafio_ladder.desafiante
                        # Verificar se desafiante pode utilizar desafio coringa
                        if not desafiante.pode_usar_coringa_na_data(desafio_ladder.data_hora.date()):
                            raise ValueError(DesafioLadder.MENSAGEM_ERRO_PERIODO_ESPERA_CORINGA)
                        
                        # Guardar utilização de coringa
                        desafiante.ultimo_uso_coringa = desafio_ladder.data_hora.date()
                        desafiante.save()
                        
                    messages.success(request, MENSAGEM_SUCESSO_VALIDAR_DESAFIO_LADDER)
                    
                    # Se houver mais desafios a validar, voltar para tela de validação
                    if DesafioLadder.objects.filter(admin_validador__isnull=True, cancelamentodesafioladder__isnull=True).exists():
                        return redirect(reverse('ladder:listar_desafios_ladder_pendentes_validacao'))
                    else:
                        if desafio_ladder.is_historico():
                            mes, ano = desafio_ladder.mes_ano_ladder
                            return redirect(reverse('ladder:detalhar_ladder_historico', kwargs={'ano': ano, 'mes': mes}))
                        else:
                            return redirect(reverse('ladder:detalhar_ladder_atual'))
            
            except Exception as e:
                messages.error(request, str(e))
        
    return render(request, 'ladder/validar_desafio_ladder.html', {'desafio_ladder': desafio_ladder})

def analises(request):
    """Mostrar análises dos dados de desafios"""
    # Buscar primeiros registros de ladder
    if HistoricoLadder.objects.all().exists():
        primeiro_registro = HistoricoLadder.objects.all().order_by('ano', 'mes')[0]
        mes_inicial = primeiro_registro.mes
        ano_inicial = primeiro_registro.ano
    else:
        data_atual = timezone.localdate()
        mes_inicial = data_atual.month
        ano_inicial = data_atual.year
    
    return render(request, 'ladder/analises.html', {'mes_inicial': mes_inicial, 'ano_inicial': ano_inicial})

def analise_resultado_acumulado_jogadores(request):
    """Retorna dados sobre acumulado de resultados de desafios entre jogadores"""
    ano = int(request.GET.get('ano'))
    mes = int(request.GET.get('mes'))
    
    data_atual = timezone.localdate()
    if ano > data_atual.year or (ano == data_atual.year and mes > data_atual.month):
        ano = data_atual.year
        mes = data_atual.month
    
    # Definir mes/ano final para resultados de desafios
    (prox_mes, prox_ano) = mes_ano_prox(mes, ano)
    
    # Filtrar jogadores validos para mes/ano
    if (ano, mes) == (data_atual.year, data_atual.month):
        jogadores_validos = PosicaoLadder.objects.all().values_list('jogador')
    else:
        jogadores_validos = HistoricoLadder.objects.filter(mes=mes, ano=ano).values_list('jogador')
    
    desafios_df = pd.DataFrame(list(DesafioLadder.validados.filter(data_hora__lt=timezone.datetime(prox_ano, prox_mes, 1, 0, 0, tzinfo=timezone.get_current_timezone())) \
                                    .filter(desafiante__in=jogadores_validos, desafiado__in=jogadores_validos)
                                    .annotate(nick_desafiante=F('desafiante__nick')).annotate(nick_desafiado=F('desafiado__nick')).values(
                                        'data_hora', 'nick_desafiante', 'score_desafiante', 'nick_desafiado', 
                                                'score_desafiado').order_by('data_hora')))
    
    # Verifica se dataframe possui dados
    if desafios_df.empty:
        return JsonResponse({'resultado_desafios': [], 'jogador_enfrentado': [], 'jogador': []})
    
    desafios_df = analisar_resultado_acumulado_entre_jogadores(desafios_df, (mes, ano))
    
    # Trocar NaNs por None, para ser codificado em JSON
    desafios_df = desafios_df.where(pd.notnull(desafios_df), None)
    
    return JsonResponse({'resultado_desafios': desafios_df.values.tolist(), 'jogador_enfrentado': desafios_df.columns.tolist(), 
                         'jogador': desafios_df.index.tolist()})
        
    
def analise_resultado_por_posicao(request):
    """Retorna dados sobre resultados por posição"""
    desafios_df = pd.DataFrame(list(DesafioLadder.validados.all().annotate(nick_desafiante=F('desafiante__nick')) \
                                    .annotate(nick_desafiado=F('desafiado__nick')).values(
                                        'data_hora', 'nick_desafiante', 'score_desafiante', 'posicao_desafiante', 'nick_desafiado', 
                                        'score_desafiado', 'posicao_desafiado', 'desafio_coringa').order_by('data_hora')))

    # Verifica se dataframe possui dados
    if desafios_df.empty:
        return JsonResponse({'posicao_desafiante': [], 'posicao_desafiado': [], 'qtd_desafios': [], 'resultado': []})

    desafios_df = analisar_resultados_por_posicao(desafios_df)

    return JsonResponse({'posicao_desafiante': desafios_df['posicao_desafiante'].tolist(), 
                         'posicao_desafiado': desafios_df['posicao_desafiado'].tolist(),
                         'qtd_desafios': desafios_df['qtd_desafios'].tolist(),
                         'resultado': desafios_df['resultado'].tolist()})
        
def analise_resultado_por_diferenca_posicao(request):
    """Retorna dados sobre diferença de posição"""
    desafios_df = pd.DataFrame(list(DesafioLadder.validados.all() \
                                    .values('score_desafiante', 'posicao_desafiante', 'score_desafiado', 'posicao_desafiado')))

    # Verifica se dataframe possui dados
    if desafios_df.empty:
        return JsonResponse({'qtd_vitorias': [], 'perc_vitorias': [], 'qtd_derrotas': [], 'perc_derrotas': [], 'dif_posicao': []})

    desafios_df = analisar_resultados_por_dif_de_posicao(desafios_df)

    return JsonResponse({'qtd_vitorias': desafios_df['vitoria'].tolist(), 
                         'perc_vitorias': desafios_df['percentual_vitorias'].tolist(),
                         'qtd_derrotas': desafios_df['derrota'].tolist(),
                         'perc_derrotas': desafios_df['percentual_derrotas'].tolist(),
                         'dif_posicao': desafios_df.index.tolist()})
        
def analise_vitorias_por_personagem(request):
    """Retorna dados sobre vitórias por personagem"""
    desafios_personagens_df = pd.DataFrame(list(JogadorLuta.objects.filter(personagem__isnull=False, 
                                                                           luta__lutaladder__desafio_ladder__cancelamentodesafioladder__isnull=True, 
                                                                           luta__lutaladder__desafio_ladder__admin_validador__isnull=False) \
                                                .annotate(nome_personagem=F('personagem__nome')) \
                                                .annotate(vitoria=Case(When(luta__ganhador=F('jogador'), then=Value(1)), default=0,
                                                                       output_field=IntegerField())) \
                                                .values('nome_personagem', 'vitoria')))

    # Verifica se dataframe possui dados
    if desafios_personagens_df.empty:
        return JsonResponse({'qtd_lutas': [], 'perc_vitorias': [], 'personagem': []})

    desafios_personagens_df = analisar_vitorias_por_personagem(desafios_personagens_df)

    return JsonResponse({'qtd_lutas': desafios_personagens_df['qtd_lutas'].tolist(), 
                         'perc_vitorias': desafios_personagens_df['perc_vitorias'].tolist(),
                         'personagem': desafios_personagens_df.index.tolist()})  
        
def analises_por_jogador(request):
    """Mostrar análises dos dados de desafios por jogador"""
    # Buscar primeiros registros de ladder
    if HistoricoLadder.objects.all().exists():
        primeiro_registro = HistoricoLadder.objects.all().order_by('ano', 'mes')[0]
        mes_inicial = primeiro_registro.mes
        ano_inicial = primeiro_registro.ano
    else:
        data_atual = timezone.localdate()
        mes_inicial = data_atual.month
        ano_inicial = data_atual.year
        
    jogadores = Jogador.objects.all()
    return render(request, 'ladder/analises_por_jogador.html', {'jogadores': jogadores, 'mes_inicial': mes_inicial, 
                                                                'ano_inicial': ano_inicial})
                             
def analise_resultado_acumulado_para_um_jogador(request):
    """Retorna dados sobre acumulado de resultados de desafios de um jogador"""
    ano = int(request.GET.get('ano'))
    mes = int(request.GET.get('mes'))
    jogador_id = int(request.GET.get('jogador_id'))
    
    # Verificar se jogador existe
    jogador = get_object_or_404(Jogador, id=jogador_id)
    
    data_atual = timezone.localdate()
    if ano > data_atual.year or (ano == data_atual.year and mes > data_atual.month):
        ano = data_atual.year
        mes = data_atual.month
    
    # Definir mes/ano final para resultados de desafios
    (prox_mes, prox_ano) = mes_ano_prox(mes, ano)
    
    # Filtrar jogadores validos para mes/ano
    if (ano, mes) == (data_atual.year, data_atual.month):
        jogadores_validos = PosicaoLadder.objects.all().values_list('jogador')
    else:
        jogadores_validos = HistoricoLadder.objects.filter(mes=mes, ano=ano).values_list('jogador')
    
    desafios_df = pd.DataFrame(list(DesafioLadder.validados.filter(data_hora__lt=timezone.datetime(prox_ano, prox_mes, 1, 0, 0, tzinfo=timezone.get_current_timezone())) \
                                    .filter(desafiante__in=jogadores_validos, desafiado__in=jogadores_validos)
                                    .filter(Q(desafiante=jogador) | Q(desafiado=jogador))
                                    .annotate(nick_desafiante=F('desafiante__nick')).annotate(nick_desafiado=F('desafiado__nick')).values(
                                        'data_hora', 'nick_desafiante', 'score_desafiante', 'nick_desafiado', 
                                                'score_desafiado').order_by('data_hora')))
    
    # Verifica se dataframe possui dados
    if desafios_df.empty:
        return JsonResponse({'resultado_desafios': [], 'jogador_enfrentado': []})
    
    desafios_df = analisar_resultado_acumulado_para_um_jogador(desafios_df, jogador.nick, (mes, ano))
    
    return JsonResponse({'resultado_desafios': desafios_df['resultado'].tolist(), 'jogador_enfrentado': desafios_df['nick_desafiado'].tolist()})


def analise_resultado_acumulado_contra_personagens_para_um_jogador(request):
    """Retorna dados sobre acumulado de resultados de lutas de um jogador contra personagens"""
    ano = int(request.GET.get('ano'))
    mes = int(request.GET.get('mes'))
    jogador_id = int(request.GET.get('jogador_id'))
    
    # Verificar se jogador existe
    jogador = get_object_or_404(Jogador, id=jogador_id)
    
    data_atual = timezone.localdate()
    if ano > data_atual.year or (ano == data_atual.year and mes > data_atual.month):
        ano = data_atual.year
        mes = data_atual.month
    
    # Definir mes/ano final para resultados de desafios
    (prox_mes, prox_ano) = mes_ano_prox(mes, ano)
    
    # Filtrar jogadores validos para mes/ano
    if (ano, mes) == (data_atual.year, data_atual.month):
        jogadores_validos = PosicaoLadder.objects.all().values_list('jogador')
    else:
        jogadores_validos = HistoricoLadder.objects.filter(mes=mes, ano=ano).values_list('jogador')
    
    desafios_validados = DesafioLadder.validados.filter(data_hora__lt=timezone.datetime(prox_ano, prox_mes, 1, 0, 0, tzinfo=timezone.get_current_timezone()))
    
    desafios_df = pd.DataFrame(list(JogadorLuta.objects.filter(personagem__isnull=False, luta__lutaladder__desafio_ladder__in=desafios_validados) \
                                    .filter(luta__lutaladder__desafio_ladder__desafiante__in=jogadores_validos, 
                                            luta__lutaladder__desafio_ladder__desafiado__in=jogadores_validos)
                                    .filter(Q(luta__lutaladder__desafio_ladder__desafiante=jogador) | Q(luta__lutaladder__desafio_ladder__desafiado=jogador))
                                    .annotate(vitoria=Case(When(luta__ganhador=F('jogador'), then=Value(1)), default=0, 
                                                           output_field=IntegerField())) \
                                    .values('jogador__nick', 'personagem__nome', 'vitoria', 'luta')))
    
    # Verifica se dataframe possui dados
    if desafios_df.empty:
        return JsonResponse({'quantidade_lutas': [], 'percentual_vitorias': [], 'personagem': []})
    
    desafios_df = analisar_vitorias_contra_personagens_para_um_jogador(desafios_df, jogador.nick, (mes, ano))
    
    return JsonResponse({'quantidade_lutas': desafios_df['quantidade_lutas'].tolist(), 
                         'percentual_vitorias': desafios_df['percentual_vitorias'].tolist(),
                         'personagem': desafios_df.index.tolist()})
        
def analise_resultado_stages_para_um_jogador(request):
    """Retorna dados sobre resultados em stages para um jogador"""
    jogador_id = int(request.GET.get('jogador_id'))

    # Verificar se jogador existe
    jogador = get_object_or_404(Jogador, id=jogador_id)

    desafios_validados = DesafioLadder.validados.filter(Q(desafiante=jogador) | 
                                                        Q(desafiado=jogador))

    desafios_df = pd.DataFrame(list(JogadorLuta.objects.filter(luta__lutaladder__desafio_ladder__in=desafios_validados, 
                                                               luta__stage__isnull=False, jogador=jogador)
                                    .annotate(vitoria=Case(When(luta__ganhador=F('jogador'), then=Value(1)), default=0, 
                                                           output_field=IntegerField())) \
                                    .values('luta__stage__nome', 'luta__stage__modelo', 'vitoria')))

    # Verifica se dataframe possui dados
    if desafios_df.empty:
        return JsonResponse({'quantidade_lutas': [], 'percentual_vitorias': [], 'personagem': []})

    desafios_df = analisar_resultados_stages_para_um_jogador(desafios_df, jogador.nick)

    return JsonResponse({'quantidade_lutas': desafios_df['qtd_lutas'].tolist(), 
                         'percentual_vitorias': desafios_df['percentual_vitorias'].tolist(),
                         'quantidade_vitorias': desafios_df['vitoria'].tolist(),
                         'stage': desafios_df.index.tolist()})
        
def analise_vitorias_desafio_para_um_jogador(request):
    """Retorna dados sobre vitórias em desafios para um jogador"""
    jogador_id = int(request.GET.get('jogador_id'))

    # Verificar se jogador existe
    jogador = get_object_or_404(Jogador, id=jogador_id)

    desafios_df = pd.DataFrame(list(DesafioLadder.validados.filter(Q(desafiante=jogador, score_desafiante__gt=F('score_desafiado')) | 
                                                                   Q(desafiado=jogador, score_desafiado__gt=F('score_desafiante'))) \
                                    .annotate(diferenca=F('score_desafiante')-F('score_desafiado'))
                                    .values('diferenca')))

    # Verifica se dataframe possui dados
    if desafios_df.empty:
        return JsonResponse({'quantidade_vitorias': [], 'diferenca': []})

    desafios_df = analisar_vitorias_desafio_para_um_jogador(desafios_df, jogador.nick)

    return JsonResponse({'quantidade_vitorias': desafios_df['qtd_desafios'].tolist(), 
                         'diferenca': desafios_df.index.tolist()})
        