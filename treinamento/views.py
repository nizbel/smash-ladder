# -*- coding: utf-8 -*-
"""Views para treinamento"""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models.aggregates import Sum
from django.db.models.expressions import ExpressionWrapper, F
from django.db.models.fields import DurationField
from django.shortcuts import render, get_object_or_404, redirect
from django.urls.base import reverse

from treinamento.forms import RegistroTreinamentoForm, AnotacaoForm, MetricaForm, \
    ResultadoTreinamentoForm
from treinamento.models import RegistroTreinamento, Anotacao, Metrica, \
    ResultadoTreinamento


@login_required
def add_anotacao(request):
    """Adiciona uma anotação"""
    jogador = request.user.jogador
    
    if request.POST:
        form_anotacao = AnotacaoForm(request.POST)
        
        if form_anotacao.is_valid():
            try:
                with transaction.atomic():
                    anotacao = form_anotacao.save(commit=False)
                    
                    # Adicionar jogador
                    anotacao.jogador = jogador
                    anotacao.save()
                        
                    return redirect(reverse('treinamento:painel_treinamento'))
                
            except Exception as e:
                messages.error(request, e)
        
        else:
            for erro in form_anotacao.non_field_errors():
                messages.error(request, erro)
                
    else:
        form_anotacao = AnotacaoForm()
        
    return render(request, 'treinamento/adicionar_anotacao.html', {'form_anotacao': form_anotacao})

@login_required
def listar_anotacoes(request):
    """Lista anotações de um jogador"""
    anotacoes = Anotacao.objects.filter(jogador=request.user.jogador)
    
    return render(request, 'treinamento/listar_anotacoes.html', {'anotacoes': anotacoes})
    

@login_required
def add_metrica(request):
    """Adiciona uma métrica"""
    jogador = request.user.jogador
    
    if request.POST:
        form_metrica = MetricaForm(request.POST)
        
        if form_metrica.is_valid():
            try:
                with transaction.atomic():
                    metrica = form_metrica.save(commit=False)
                    
                    # Adicionar jogador
                    metrica.jogador = jogador
                    metrica.save()
                        
                    return redirect(reverse('treinamento:painel_treinamento'))
                
            except Exception as e:
                messages.error(request, e)
        
        else:
            for erro in form_metrica.non_field_errors():
                messages.error(request, erro)
                
    else:
        form_metrica = MetricaForm()
        
    return render(request, 'treinamento/adicionar_metrica.html', {'form_metrica': form_metrica})

@login_required
def detalhar_metrica(request, metrica_id):
    """Detalha uma métrica"""
    
    metrica = get_object_or_404(Metrica, id=metrica_id, jogador=request.user.jogador)
    resultados = list(ResultadoTreinamento.objects.filter(metrica=metrica, registro_treinamento__jogador=request.user.jogador) \
        .order_by('registro_treinamento__fim').values_list('registro_treinamento__inicio', 'quantidade'))
    
    resultados = [{'x': resultado[0].strftime('%d/%m/%Y %H:%M'), 'y': resultado[1]} for resultado in resultados]
    
    return render(request, 'treinamento/detalhar_metrica.html', {'metrica': metrica, 'resultados': resultados})

@login_required
def listar_metricas(request):
    """Lista métricas de um jogador"""
    metricas = Metrica.objects.filter(jogador=request.user.jogador)
    
    return render(request, 'treinamento/listar_metricas.html', {'metricas': metricas})

@login_required
def add_registro_treinamento(request):
    """Adiciona um registro de treinamento"""
    jogador = request.user.jogador
    
    if request.POST:
        form_registro_treinamento = RegistroTreinamentoForm(request.POST)
        
        if form_registro_treinamento.is_valid():
            try:
                with transaction.atomic():
                    registro_treinamento = form_registro_treinamento.save(commit=False)
                    
                    # Adicionar jogador
                    registro_treinamento.jogador = jogador
                    registro_treinamento.save()
                        
                    return redirect(reverse('treinamento:painel_treinamento'))
                
            except Exception as e:
                messages.error(request, e)
        
        else:
            for erro in form_registro_treinamento.non_field_errors():
                messages.error(request, erro)
                
    else:
        form_registro_treinamento = RegistroTreinamentoForm()
        
    return render(request, 'treinamento/adicionar_registro_treinamento.html', {'form_registro_treinamento': form_registro_treinamento})

@login_required
def listar_registros_treinamento(request):
    """Lista registros de treinamento de um jogador"""
    registros = RegistroTreinamento.objects.filter(jogador=request.user.jogador)
    
    return render(request, 'treinamento/listar_registros_treinamento.html', {'registros': registros})

@login_required
def detalhar_registro_treinamento(request, registro_id):
    """Detalha um registro de treinamento"""
    
    registro_treinamento = get_object_or_404(RegistroTreinamento, id=registro_id, jogador=request.user.jogador)
    
    resultados = ResultadoTreinamento.objects.filter(registro_treinamento=registro_treinamento)
    
    return render(request, 'treinamento/detalhar_registro_treinamento.html', {'registro_treinamento': registro_treinamento,
                                                                              'resultados': resultados})

@login_required
def add_resultado_treinamento(request, registro_id):
    """Adiciona um resultado de treinamento"""
    jogador = request.user.jogador
    registro = get_object_or_404(RegistroTreinamento, jogador=jogador, id=registro_id)    
    
    if request.POST:
        form_resultado_treinamento = ResultadoTreinamentoForm(request.POST)
        
        if form_resultado_treinamento.is_valid():
            try:
                with transaction.atomic():
                    resultado_treinamento = form_resultado_treinamento.save(commit=False)
                    
                    # Adicionar jogador
                    resultado_treinamento.registro_treinamento = registro
                    resultado_treinamento.save()
                        
                    return redirect(reverse('treinamento:painel_treinamento'))
                
            except Exception as e:
                messages.error(request, e)
        
        else:
            for erro in form_resultado_treinamento.non_field_errors():
                messages.error(request, erro)
                
    else:
        form_resultado_treinamento = ResultadoTreinamentoForm()
        
    return render(request, 'treinamento/adicionar_resultado_treinamento.html', {'form_resultado_treinamento': form_resultado_treinamento,
                                                                                'registro_treinamento': registro})
    
@login_required
def painel_treinamento(request):
    """Painel de treinamento"""
    jogador = request.user.jogador
    
    ultimas_anotacoes = Anotacao.objects.filter(jogador=jogador).order_by('-data_hora')[:3]
    
    metricas = Metrica.objects.filter(jogador=jogador)[:3]
    
    ultimos_registros = RegistroTreinamento.objects.filter(jogador=jogador).order_by('-fim')[:3]
    
    dados_treinamento = {}
    dados_treinamento['qtd_sessoes_treinamento'] = RegistroTreinamento.objects.filter(jogador=jogador).count()
    
    dados_treinamento['tempo_registrado'] = (RegistroTreinamento.objects.filter(jogador=jogador) \
        .annotate(diff=ExpressionWrapper(F('fim') - F('inicio'), output_field=DurationField())) \
        .aggregate(duracao_total=Sum('diff'))['duracao_total'] or 0)
    if dados_treinamento['tempo_registrado']:
        segundos = int(dados_treinamento['tempo_registrado'].total_seconds())
        dados_treinamento['tempo_registrado'] = f'{segundos // 3600}:{segundos % 3600 // 60}'
    else:
        dados_treinamento['tempo_registrado'] = '0:00'
        
    return render(request, 'treinamento/painel.html', {'ultimas_anotacoes': ultimas_anotacoes, 'metricas': metricas, 
                                                       'ultimos_registros': ultimos_registros, 'dados_treinamento': dados_treinamento})
