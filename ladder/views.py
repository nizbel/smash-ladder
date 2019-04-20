# -*- coding: utf-8 -*-
"""Views para ladder"""

import datetime

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.forms.formsets import formset_factory
from django.http.response import Http404
from django.shortcuts import get_object_or_404, render, redirect
from django.urls.base import reverse
from django.utils import timezone

from ladder.forms import DesafioLadderForm, DesafioLadderLutaForm
from ladder.models import PosicaoLadder, HistoricoLadder, Luta, JogadorLuta, \
    DesafioLadder, CancelamentoDesafioLadder, InicioLadder
from ladder.utils import verificar_posicoes_desafiante_desafiado, alterar_ladder, \
    recalcular_ladder, validar_e_salvar_lutas_ladder


MENSAGEM_ERRO_EDITAR_DESAFIO_CANCELADO = 'Não é possível editar desafio cancelado'

MENSAGEM_SUCESSO_ADD_DESAFIO_LADDER = 'Desafio inserido com sucesso! Peça a um administrador para validar'
MENSAGEM_SUCESSO_CANCELAR_DESAFIO_LADDER = 'Desafio cancelado com sucesso'
MENSAGEM_SUCESSO_CANCELAR_MULTIPLOS_DESAFIOS_LADDER = 'Desafios de ladder cancelados com sucesso'
MENSAGEM_SUCESSO_EDITAR_DESAFIO_LADDER = 'Desafio editado com sucesso!'
MENSAGEM_SUCESSO_VALIDAR_DESAFIO_LADDER = 'Desafio validado com sucesso!'

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
                        desafio_ladder.save()
                        
                        # Validar lutas
                        validar_e_salvar_lutas_ladder(desafio_ladder, formset_lutas)
                        
                        messages.success(request, MENSAGEM_SUCESSO_ADD_DESAFIO_LADDER)
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
        form_desafio_ladder = DesafioLadderForm(initial={'adicionado_por': request.user.jogador.id}, admin=request.user.jogador.admin)
        form_desafio_ladder.fields['adicionado_por'].disabled = True
        
    return render(request, 'ladder/adicionar_desafio_ladder.html', {'form_desafio_ladder': form_desafio_ladder, 
                                                                       'formset_lutas': formset_lutas})
    
def detalhar_ladder_atual(request):
    """Detalhar posição da ladder atual"""
    ladder = list(PosicaoLadder.objects.all().order_by('posicao').select_related('jogador'))
    
    data_mes_anterior = timezone.now().replace(day=1) - datetime.timedelta(days=1)
    
    # Comparar com ladder anterior
    if HistoricoLadder.objects.filter(mes=data_mes_anterior.month, ano=data_mes_anterior.year).exists():
        ladder_anterior = HistoricoLadder.objects.filter(mes=data_mes_anterior.month, ano=data_mes_anterior.year)
    else:
        ladder_anterior = InicioLadder.objects.all()
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
            posicao_ladder.alteracao = len(ladder) - posicao_ladder.posicao
    
    return render(request, 'ladder/ladder_atual.html', {'ladder': ladder})
    
def detalhar_ladder_historico(request, ano, mes):
    """Detalhar histórico da ladder em mês/ano específico"""
    # Testa se existe histórico para mês/ano apontados
    if not HistoricoLadder.objects.filter(ano=ano, mes=mes).exists():
        raise Http404('Não há ladder para o mês/ano inseridos')
    ladder = HistoricoLadder.objects.filter(ano=ano, mes=mes).order_by('posicao') \
        .select_related('jogador')
    
    # Pegar mês/ano anterior
    mes_anterior = mes - 1
    ano_anterior = ano
    if mes_anterior == 0:
        ano_anterior -= 1
        mes_anterior = 12
    
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
            if posicao_ladder_anterior.jogador == posicao_ladder.jogador:
                posicao_ladder.alteracao = posicao_ladder_anterior.posicao - posicao_ladder.posicao

                preencheu_alteracao = True
                break
            
        if not preencheu_alteracao:
            posicao_ladder.alteracao = len(ladder) - posicao_ladder.posicao
    
    return render(request, 'ladder/ladder_historico.html', {'ladder': ladder, 'ano': ano, 'mes': mes})

def listar_ladder_historico(request):
    """Listar históricos de ladder por ano/mês"""
    # Buscar anos e meses para listagem
    
    lista_ladders = HistoricoLadder.objects.all().order_by('-ano', '-mes') \
                         .values('mes', 'ano').distinct()
    
    return render(request, 'ladder/listar_ladder_historico.html', {'lista_ladders': lista_ladders})

def detalhar_luta(request, luta_id):
    """Detalhar uma luta"""
    luta = get_object_or_404(Luta, id=luta_id)
    participantes = JogadorLuta.objects.filter(luta=luta).select_related('jogador', 'personagem')
    
    return render(request, 'ladder/luta.html', {'luta': luta, 'participantes': participantes})

@login_required
def cancelar_desafio_ladder(request, desafio_id):
    """Cancelar um desafio de ladder"""
    desafio_ladder = get_object_or_404(DesafioLadder, id=desafio_id)
    
    # Se já for cancelado, retornar para detalhamento
    if desafio_ladder.is_cancelado():
        messages.error(request, f'Cancelamento já foi feito por {desafio_ladder.cancelamentodesafioladder.jogador.nick}')
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
        if confirmacao == '1':
            # Cancelar desafio
            try:
                with transaction.atomic():
                    # Se validado, verificar alterações decorrentes da operação
                    if desafio_ladder.is_validado():
                        # Verificar se desafio é de histórico
                        if desafio_ladder.is_historico():
                            mes, ano = desafio_ladder.mes_ano_ladder
                        else:
                            mes, ano = None, None
                        
                        # Gerar cancelamento para desafio e tentar recalcular ladder
                        cancelamento = CancelamentoDesafioLadder(desafio_ladder=desafio_ladder, jogador=request.user.jogador)
                        cancelamento.save()
                        
                        # Recalcula ladder para verificar se cancelamento é válido
                        recalcular_ladder(mes, ano)
                        
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
                        
                    # Se não validado, cancelar
                    else:
                        cancelamento = CancelamentoDesafioLadder(desafio_ladder=desafio_ladder, jogador=request.user.jogador)
                        cancelamento.save()
                    
                    messages.success(request, MENSAGEM_SUCESSO_CANCELAR_DESAFIO_LADDER)
                    return redirect(reverse('ladder:detalhar_desafio_ladder', kwargs={'desafio_id': desafio_id}))
            
            except Exception as e:
                messages.error(request, str(e))
    
    return render(request, 'ladder/cancelar_desafio_ladder.html', {'desafio_ladder': desafio_ladder})

def detalhar_desafio_ladder(request, desafio_id):
    """Detalhar um desafio de ladder"""
    desafio_ladder = get_object_or_404(DesafioLadder, id=desafio_id)
    
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
    
    return render(request, 'ladder/regras.html', {})

def listar_desafios_ladder(request, ano=None, mes=None):
    """Listar desafios de ladder específica"""
    # Ano/mês devem estar ambos preenchidos ou ambos nulos
    # Ambos nulos significa ladder atual
    if ano == None and mes == None:
        data_atual = timezone.now().date()
        ano = data_atual.year
        mes = data_atual.month
    elif (ano == None and mes != None) or (ano != None and mes == None):
        raise Http404('Ano e mês devem ser preenchidos')
    elif mes not in [_ for _ in range(1, 13)]:
        raise Http404('Mês inválido')
    elif ano * 12 + mes > timezone.now().year * 12 + timezone.now().month:
        raise Http404('Data futura é inválida para histórico')
    
    
    # Buscar desafios para ladder especificada
    desafios_ladder = DesafioLadder.objects.filter(data_hora__month=mes, data_hora__year=ano).order_by('data_hora')
    
    return render(request, 'ladder/listar_desafios_ladder.html', {'desafios_ladder': desafios_ladder, 'ano': ano, 'mes': mes})

def listar_desafios_ladder_pendentes_validacao(request):
    """Listar desafios de ladder pendentes de validação"""
    # Buscar desafios pendentes
    desafios_pendentes = DesafioLadder.objects.filter(admin_validador__isnull=True, cancelamentodesafioladder__isnull=True).order_by('data_hora')
    
    return render(request, 'ladder/listar_desafios_pendente_validacao.html', {'desafios_pendentes': desafios_pendentes})

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
    
    if request.POST:
        confirmacao = request.POST.get('salvar')

        if confirmacao != None:
            try:
                with transaction.atomic():
                    # Validação
                    # Verificar posições
                    verificar_posicoes_desafiante_desafiado(desafio_ladder.ladder, desafio_ladder.desafiante,
                                                             desafio_ladder.desafiado, desafio_ladder.data_hora,
                                                             desafio_ladder.desafio_coringa)
                    
                    # Alterar ladder referência
                    alterar_ladder(desafio_ladder)
                    
                    # Gravar validador
                    desafio_ladder.admin_validador = request.user.jogador
                    desafio_ladder.save()
                    
                    if desafio_ladder.desafio_coringa:
                        desafiante = desafio_ladder.desafiante
                        # Verificar se desafiante pode utilizar desafio coringa
                        if not desafiante.pode_usar_coringa_na_data(desafio_ladder.data_hora.date()):
                            raise ValueError(DesafioLadder.MENSAGEM_ERRO_PERIODO_ESPERA_CORINGA)
                        
                        # Guardar utilização de coringa
                        desafiante.ultimo_uso_coringa = desafio_ladder.data_hora.date()
                        desafiante.save()
                        
                    messages.success(request, MENSAGEM_SUCESSO_VALIDAR_DESAFIO_LADDER)
                    if desafio_ladder.is_historico():
                        mes, ano = desafio_ladder.mes_ano_ladder
                        return redirect(reverse('ladder:detalhar_ladder_historico', kwargs={'ano': ano, 'mes': mes}))
                    else:
                        return redirect(reverse('ladder:detalhar_ladder_atual'))
            
            except Exception as e:
                messages.error(request, str(e))
        
    return render(request, 'ladder/validar_desafio_ladder.html', {'desafio_ladder': desafio_ladder})
