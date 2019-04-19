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

from ladder.forms import RegistroLadderForm, RegistroLadderLutaForm
from ladder.models import PosicaoLadder, HistoricoLadder, Luta, JogadorLuta, \
    RegistroLadder, CancelamentoRegistroLadder, InicioLadder
from ladder.utils import verificar_posicoes_desafiante_desafiado, alterar_ladder, \
    recalcular_ladder, validar_e_salvar_lutas_ladder


MENSAGEM_ERRO_EDITAR_REGISTRO_CANCELADO = 'Não é possível editar registro cancelado'

MENSAGEM_SUCESSO_ADD_REGISTRO_LADDER = 'Registro inserido com sucesso! Peça a um administrador para validar'
MENSAGEM_SUCESSO_CANCELAR_REGISTRO_LADDER = 'Registro cancelado com sucesso'
MENSAGEM_SUCESSO_CANCELAR_MULTIPLOS_REGISTROS_LADDER = 'Registros de ladder cancelados com sucesso'
MENSAGEM_SUCESSO_EDITAR_REGISTRO_LADDER = 'Registro editado com sucesso!'
MENSAGEM_SUCESSO_VALIDAR_REGISTRO_LADDER = 'Registro validado com sucesso!'

@login_required
def add_registro_ladder(request):
    """Adiciona registro para ladder"""
    # Preparar formset
    RegistroLadderLutaFormSet = formset_factory(RegistroLadderLutaForm, extra=RegistroLadder.MELHOR_DE)
    formset_lutas = RegistroLadderLutaFormSet(request.POST or None, prefix='registro_ladder_luta')
    for form_luta in formset_lutas:
        form_luta.fields['ganhador'].required = False
    
    if request.POST:
        form_registro_ladder = RegistroLadderForm(request.POST, initial={'adicionado_por': request.user.jogador.id}, admin=request.user.jogador.admin)
        form_registro_ladder.fields['adicionado_por'].disabled = True
        
        if form_registro_ladder.is_valid():
            
            # Descobrir quantas lutas devem ser cadastradas a partir do resultado
            dados_form_registro_ladder = form_registro_ladder.cleaned_data
            lutas_total = dados_form_registro_ladder['score_desafiante'] + dados_form_registro_ladder['score_desafiado']
            
            # Validar formset com dados do form de registro de ladder
            RegistroLadderLutaFormSet = formset_factory(RegistroLadderLutaForm, extra=RegistroLadder.MELHOR_DE, min_num=lutas_total, 
                                                        max_num=lutas_total)
            formset_lutas = RegistroLadderLutaFormSet(request.POST, prefix='registro_ladder_luta')
            for form_luta in formset_lutas:
                form_luta.fields['ganhador'].required = False
            
            if formset_lutas.is_valid():
                try:
                    with transaction.atomic():
                        registro_ladder = form_registro_ladder.save(commit=False)
                        registro_ladder.save()
                        
                        # Validar lutas
                        validar_e_salvar_lutas_ladder(registro_ladder, formset_lutas)
                        
                        messages.success(request, MENSAGEM_SUCESSO_ADD_REGISTRO_LADDER)
                        return redirect(reverse('ladder:detalhar_registro_ladder', kwargs={'registro_id': registro_ladder.id}))
                    
                except Exception as e:
                    messages.error(request, e)
            else:
                for erro in formset_lutas.non_form_errors():
                    print(erro)
                    # Sobrescrever erro de quantidade de forms
                    if erro.startswith(f'Por favor envie {lutas_total} ou '):
                        messages.error(request, f'Preencha apenas as lutas 1 a {lutas_total}')
                    else:
                        messages.error(request, erro)
        
        else:
            for erro in form_registro_ladder.non_field_errors():
                print(erro)
                messages.error(request, erro)
                
    else:
        form_registro_ladder = RegistroLadderForm(initial={'adicionado_por': request.user.jogador.id}, admin=request.user.jogador.admin)
        form_registro_ladder.fields['adicionado_por'].disabled = True
        
    return render(request, 'ladder/adicionar_registro.html', {'form_registro_ladder': form_registro_ladder, 
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
    
    return render(request, 'ladder/ladder_historico.html', {'ladder': ladder, 'ano': ano, 'mes': mes})

def detalhar_luta(request, luta_id):
    """Detalhar uma luta"""
    luta = get_object_or_404(Luta, id=luta_id)
    participantes = JogadorLuta.objects.filter(luta=luta).select_related('jogador', 'personagem')
    
    return render(request, 'ladder/luta.html', {'luta': luta, 'participantes': participantes})

@login_required
def cancelar_registro_ladder(request, registro_id):
    """Cancelar um registro de ladder"""
    registro_ladder = get_object_or_404(RegistroLadder, id=registro_id)
    
    # Se já for cancelado, retornar para detalhamento
    if registro_ladder.is_cancelado():
        messages.error(request, f'Cancelamento já foi feito por {registro_ladder.cancelamentoregistroladder.jogador.nick}')
        return redirect(reverse('ladder:detalhar_registro_ladder', kwargs={'registro_id': registro_id}))
    
    # Verificar se usuário logado pode cancelar registro
    # Admins podem ver tudo
    if request.user.jogador.admin:
        pass
    # Jogadores comuns podem ver apenas os registros que criaram e não foram validados
    elif registro_ladder.is_validado():
        raise PermissionDenied
    elif request.user.jogador != registro_ladder.adicionado_por:
        raise PermissionDenied
    
    if request.POST:
        confirmacao = request.POST.get('salvar')
        if confirmacao == '1':
            # Cancelar registro
            try:
                with transaction.atomic():
                    # Se validado, verificar alterações decorrentes da operação
                    if registro_ladder.is_validado():
                        # Verificar se registro é de histórico
                        if registro_ladder.is_historico():
                            mes, ano = registro_ladder.mes_ano_ladder
                        else:
                            mes, ano = None, None
                        
                        # Gerar cancelamento para registro e tentar recalcular ladder
                        cancelamento = CancelamentoRegistroLadder(registro_ladder=registro_ladder, jogador=request.user.jogador)
                        cancelamento.save()
                        
                        # Recalcula ladder para verificar se cancelamento é válido
                        recalcular_ladder(mes, ano)
                        
                        # Se registro tinha desafio coringa, verificar último uso do jogador
                        if registro_ladder.desafio_coringa:
                            desafiante = registro_ladder.desafiante
                            # Se esse foi o último uso, voltar para penúltimo ou deixar nulo
                            if registro_ladder.data_hora.date() == desafiante.ultimo_uso_coringa:
                                # Verifica se existe uso anterior
                                if RegistroLadder.objects.filter(data_hora__lt=registro_ladder.data_hora, 
                                                                 cancelamentoregistroladder__isnull=True,
                                                                 admin_validador__isnull=False, desafiante=desafiante, 
                                                                 desafio_coringa=True).exists():
                                    data_penultimo_uso = RegistroLadder.objects.filter(data_hora__lt=registro_ladder.data_hora, 
                                                                                  cancelamentoregistroladder__isnull=True,
                                                                                  admin_validador__isnull=False, desafiante=desafiante, 
                                                                                  desafio_coringa=True).order_by('-data_hora')[0].data_hora
                                    desafiante.ultimo_uso_coringa = data_penultimo_uso
                                else:
                                    desafiante.ultimo_uso_coringa = None
                                desafiante.save()
                        
                    # Se não validado, cancelar
                    else:
                        cancelamento = CancelamentoRegistroLadder(registro_ladder=registro_ladder, jogador=request.user.jogador)
                        cancelamento.save()
                    
                    messages.success(request, MENSAGEM_SUCESSO_CANCELAR_REGISTRO_LADDER)
                    return redirect(reverse('ladder:detalhar_registro_ladder', kwargs={'registro_id': registro_id}))
            
            except Exception as e:
                messages.error(request, str(e))
    
    return render(request, 'ladder/cancelar_registro_ladder.html', {'registro_ladder': registro_ladder})

def detalhar_registro_ladder(request, registro_id):
    """Detalhar um registro de ladder"""
    registro_ladder = get_object_or_404(RegistroLadder, id=registro_id)
    
    return render(request, 'ladder/detalhar_registro_ladder.html', {'registro_ladder': registro_ladder})

@login_required
def editar_registro_ladder(request, registro_id):
    """Editar um registro de ladder, apenas se não estiver validado"""
    # TODO implementar edição de registro validado
    registro_ladder = get_object_or_404(RegistroLadder, id=registro_id)
    
    # Verificar se cancelado
    if registro_ladder.is_cancelado():
        messages.error(request, MENSAGEM_ERRO_EDITAR_REGISTRO_CANCELADO)
        return redirect(reverse('ladder:detalhar_registro_ladder', kwargs={'registro_id': registro_ladder.id}))
    
    # Verificar se usuário logado pode editar registro
    if registro_ladder.is_validado():
        raise PermissionDenied
    # Admins e criadores podem editar
    elif request.user.jogador.admin or request.user.jogador == registro_ladder.adicionado_por:
        pass
    else:
        raise PermissionDenied
    
    # Preparar lutas do registro
    queryset_registro_ladder = Luta.objects.filter(lutaladder__registro_ladder=registro_ladder).select_related('lutaladder') \
        .prefetch_related('jogadorluta_set')
    
    lutas_registro_ladder = list()
    for _ in range(RegistroLadder.MELHOR_DE):
        lutas_registro_ladder.append({})
    
    for luta in queryset_registro_ladder:
        lutas_registro_ladder[luta.lutaladder.indice_registro_ladder-1] = {'id': luta.id,'ganhador': luta.ganhador, 'stage': luta.stage, 
                                   'personagem_desafiante': luta.jogadorluta_set.get(jogador=registro_ladder.desafiante).personagem, 
                                   'personagem_desafiado': luta.jogadorluta_set.get(jogador=registro_ladder.desafiado).personagem}
        
    # Preparar formset
    RegistroLadderLutaFormSet = formset_factory(RegistroLadderLutaForm, extra=(RegistroLadder.MELHOR_DE - len(lutas_registro_ladder)),
                                                can_delete=True)
    formset_lutas = RegistroLadderLutaFormSet(request.POST or None, prefix='registro_ladder_luta', initial=lutas_registro_ladder)
    for form_luta in formset_lutas:
        form_luta.fields['ganhador'].required = False
            
    if request.POST:
        form_registro_ladder = RegistroLadderForm(request.POST, instance=registro_ladder, admin=request.user.jogador.admin)
        form_registro_ladder.fields['adicionado_por'].disabled = True
        
        if form_registro_ladder.is_valid():
            
            # Descobrir quantas lutas devem ser cadastradas a partir do resultado
            dados_form_registro_ladder = form_registro_ladder.cleaned_data
            lutas_total = dados_form_registro_ladder['score_desafiante'] + dados_form_registro_ladder['score_desafiado']
            
            # Validar formset com dados do form de registro de ladder
            RegistroLadderLutaFormSet = formset_factory(RegistroLadderLutaForm, extra=(RegistroLadder.MELHOR_DE - len(lutas_registro_ladder)), 
                                                        max_num=lutas_total, can_delete=True)
            formset_lutas = RegistroLadderLutaFormSet(request.POST, prefix='registro_ladder_luta', initial=lutas_registro_ladder)
            for form_luta in formset_lutas:
                form_luta.fields['ganhador'].required = False
            
            if formset_lutas.is_valid():
                try:
                    with transaction.atomic():
                        registro_ladder = form_registro_ladder.save(commit=False)
                        registro_ladder.save()
                        
                        # Validar lutas
                        validar_e_salvar_lutas_ladder(registro_ladder, formset_lutas)
                        
                        messages.success(request, MENSAGEM_SUCESSO_EDITAR_REGISTRO_LADDER)
                        return redirect(reverse('ladder:detalhar_registro_ladder', kwargs={'registro_id': registro_ladder.id}))
                    
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
        form_registro_ladder = RegistroLadderForm(instance=registro_ladder, admin=request.user.jogador.admin)
        form_registro_ladder.fields['adicionado_por'].disabled = True
        
    return render(request, 'ladder/editar_registro_ladder.html', {'form_registro_ladder': form_registro_ladder,
                                                                  'formset_lutas': formset_lutas})

def detalhar_regras(request):
    """Detalhar regras da ladder"""
    
    return render(request, 'ladder/regras.html', {})

def listar_registros_ladder(request, ano=None, mes=None):
    """Listar registros de ladder específica"""
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
    
    
    # Buscar registros para ladder especificada
    registros_ladder = RegistroLadder.objects.filter(data_hora__month=mes, data_hora__year=ano).order_by('data_hora')
    
    return render(request, 'ladder/listar_registros_ladder.html', {'registros_ladder': registros_ladder})

def listar_registros_ladder_pendentes_validacao(request):
    """Listar registros de ladder pendentes de validação"""
    # Buscar registros pendentes
    registros_pendentes = RegistroLadder.objects.filter(admin_validador__isnull=True, cancelamentoregistroladder__isnull=True).order_by('data_hora')
    
    return render(request, 'ladder/listar_registros_pendente_validacao.html', {'registros_pendentes': registros_pendentes})

@login_required
def validar_registro_ladder(request, registro_id):
    """Validar um registro de ladder"""
    # Usuário deve ser admin
    if not request.user.jogador.admin:
        raise PermissionDenied
    
    registro_ladder = get_object_or_404(RegistroLadder, id=registro_id)
    
    if registro_ladder.is_validado():
        messages.error(request, f'Validação já foi feita por {registro_ladder.admin_validador.nick}')
        return redirect(reverse('ladder:detalhar_registro_ladder', kwargs={'registro_id': registro_id}))
    
    if request.POST:
        confirmacao = request.POST.get('salvar')

        if confirmacao != None:
            try:
                with transaction.atomic():
                    # Validação
                    # Verificar posições
                    verificar_posicoes_desafiante_desafiado(registro_ladder.ladder, registro_ladder.desafiante,
                                                             registro_ladder.desafiado, registro_ladder.data_hora,
                                                             registro_ladder.desafio_coringa)
                    
                    # Alterar ladder referência
                    alterar_ladder(registro_ladder)
                    
                    # Gravar validador
                    registro_ladder.admin_validador = request.user.jogador
                    registro_ladder.save()
                    
                    if registro_ladder.desafio_coringa:
                        desafiante = registro_ladder.desafiante
                        # Verificar se desafiante pode utilizar desafio coringa
                        if not desafiante.pode_usar_coringa_na_data(registro_ladder.data_hora.date()):
                            raise ValueError(RegistroLadder.MENSAGEM_ERRO_PERIODO_ESPERA_CORINGA)
                        
                        # Guardar utilização de coringa
                        desafiante.ultimo_uso_coringa = registro_ladder.data_hora.date()
                        desafiante.save()
                        
                    messages.success(request, MENSAGEM_SUCESSO_VALIDAR_REGISTRO_LADDER)
                    if registro_ladder.is_historico():
                        mes, ano = registro_ladder.mes_ano_ladder
                        return redirect(reverse('ladder:detalhar_ladder_historico', kwargs={'ano': ano, 'mes': mes}))
                    else:
                        return redirect(reverse('ladder:detalhar_ladder_atual'))
            
            except Exception as e:
                messages.error(request, str(e))
        
    return render(request, 'ladder/validar_registro_ladder.html', {'registro_ladder': registro_ladder})
