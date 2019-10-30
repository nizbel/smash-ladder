# -*- coding: utf-8 -*-
"""Views para treinamento"""
import datetime

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models.aggregates import Sum
from django.db.models.expressions import ExpressionWrapper, F
from django.db.models.fields import DurationField
from django.shortcuts import render, get_object_or_404, redirect
from django.urls.base import reverse
from django.utils import timezone

from treinamento.forms import RegistroTreinamentoForm, AnotacaoForm, MetricaForm, \
    ResultadoTreinamentoForm, LinkUtilForm
from treinamento.models import RegistroTreinamento, Anotacao, Metrica, \
    ResultadoTreinamento, LinkUtil
from treinamento.utils import converter_segundos_duracao


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
                        
                    messages.success(request, 'Anotação adicionada com sucesso')
                    return redirect(reverse('treinamento:listar_anotacoes'))
                
            except Exception as e:
                messages.error(request, e)
        
        else:
            for erro in form_anotacao.non_field_errors():
                messages.error(request, erro)
                
    else:
        form_anotacao = AnotacaoForm()
        
    return render(request, 'treinamento/adicionar_anotacao.html', {'form_anotacao': form_anotacao})

@login_required
def apagar_anotacao(request, anotacao_id):
    """Apaga uma anotação"""
    jogador = request.user.jogador
    
    anotacao = get_object_or_404(Anotacao, jogador=jogador, id=anotacao_id)
    
    if request.POST:
        try:
            with transaction.atomic():
                anotacao.delete()
                
                messages.success(request, 'Anotação apagada com sucesso')
                return redirect(reverse('treinamento:listar_anotacoes'))
            
        except Exception as e:
            messages.error(request, e)
        
    return render(request, 'treinamento/apagar_anotacao.html', {'anotacao': anotacao})

@login_required
def listar_anotacoes(request):
    """Lista anotações de um jogador"""
    anotacoes = Anotacao.objects.filter(jogador=request.user.jogador)
    
    return render(request, 'treinamento/listar_anotacoes.html', {'anotacoes': anotacoes})
    
@login_required
def add_link_util(request):
    """Adiciona uma link útil"""
    jogador = request.user.jogador
    
    if request.POST:
        form_link_util = LinkUtilForm(request.POST)
        
        if form_link_util.is_valid():
            try:
                with transaction.atomic():
                    link_util = form_link_util.save(commit=False)
                    
                    # Adicionar jogador
                    link_util.jogador = jogador
                    link_util.save()
                        
                    messages.success(request, 'Link útil adicionado com sucesso')
                    return redirect(reverse('treinamento:listar_links_uteis'))
                
            except Exception as e:
                messages.error(request, e)
        
        else:
            for erro in form_link_util.non_field_errors():
                messages.error(request, erro)
                
    else:
        form_link_util = LinkUtilForm()
        
    return render(request, 'treinamento/adicionar_link_util.html', {'form_link_util': form_link_util})

@login_required
def apagar_link_util(request, link_util_id):
    """Apaga uma link útil"""
    jogador = request.user.jogador
    
    link_util = get_object_or_404(LinkUtil, jogador=jogador, id=link_util_id)
    
    if request.POST:
        try:
            with transaction.atomic():
                link_util.delete()
                
                messages.success(request, 'Link útil apagado com sucesso')
                return redirect(reverse('treinamento:listar_links_uteis'))
            
        except Exception as e:
            messages.error(request, e)
        
    return render(request, 'treinamento/apagar_link_util.html', {'link_util': link_util})

@login_required
def listar_links_uteis(request):
    """Lista links úteis de um jogador"""
    links_uteis = LinkUtil.objects.filter(jogador=request.user.jogador)
    
    return render(request, 'treinamento/listar_links_uteis.html', {'links_uteis': links_uteis})

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
                        
                    messages.success(request, 'Métrica adicionada com sucesso')
                    return redirect(reverse('treinamento:detalhar_metrica', kwargs={'metrica_id': metrica.id}))
                
            except Exception as e:
                messages.error(request, e)
        
        else:
            for erro in form_metrica.non_field_errors():
                messages.error(request, erro)
                
    else:
        form_metrica = MetricaForm()
        
    return render(request, 'treinamento/adicionar_metrica.html', {'form_metrica': form_metrica})

@login_required
def apagar_metrica(request, metrica_id):
    """Apaga uma métrica"""
    metrica = get_object_or_404(Metrica, jogador=request.user.jogador, id=metrica_id)
    
    if request.POST:
        try:
            with transaction.atomic():
                metrica.delete()
                
                messages.success(request, 'Métrica apagada com sucesso')
                return redirect(reverse('treinamento:listar_metricas'))
            
        except Exception as e:
            messages.error(request, e)
        
    return render(request, 'treinamento/apagar_metrica.html', {'metrica': metrica})

@login_required
def detalhar_metrica(request, metrica_id):
    """Detalha uma métrica"""
    metrica = get_object_or_404(Metrica, id=metrica_id, jogador=request.user.jogador)
    resultados = list(ResultadoTreinamento.objects.filter(metrica=metrica, registro_treinamento__jogador=request.user.jogador) \
        .order_by('registro_treinamento__fim').values_list('registro_treinamento__inicio', 'quantidade'))
    
    resultados_grafico = [{'x': resultado[0].strftime('%d/%m/%Y %H:%M'), 'y': resultado[1]} for resultado in resultados]
    
    media_resultados = {}
    
    media_resultados['geral'] = sum([resultado[1] for resultado in resultados]) / len(resultados)
    
    resultados_30_dias = [resultado for resultado in resultados if 
                                       resultado[0] >= (timezone.localtime() - datetime.timedelta(days=30))]
    media_resultados['30_dias'] = sum([resultado[1] for resultado in resultados_30_dias]) / len(resultados_30_dias)
    
    maior_resultado = {}
    
    maior_resultado['geral'] = max([resultado[1] for resultado in resultados])
    
    maior_resultado['30_Dias'] = max([resultado[1] for resultado in resultados if 
                                       resultado[0] >= (timezone.localtime() - datetime.timedelta(days=30))])
    
    menor_resultado = {}
    
    menor_resultado['geral'] = min([resultado[1] for resultado in resultados])
    
    menor_resultado['30_Dias'] = min([resultado[1] for resultado in resultados if 
                                       resultado[0] >= (timezone.localtime() - datetime.timedelta(days=30))])
    
    if len(resultados) >= 2:
        metrica.avanco = ((resultados[-1][1] / resultados[0][1]) - 1) * 100
    else:
        metrica.avanco = 0
    
    return render(request, 'treinamento/detalhar_metrica.html', {'metrica': metrica, 'resultados_grafico': resultados_grafico,
                                                                 'media_resultados': media_resultados,
                                                                 'maior_resultado': maior_resultado,
                                                                 'menor_resultado': menor_resultado})

@login_required
def editar_metrica(request, metrica_id):
    """Edita uma métrica"""
    jogador = request.user.jogador
    
    metrica = get_object_or_404(Metrica, jogador=jogador, id=metrica_id)
    
    if request.POST:
        form_metrica = MetricaForm(request.POST, instance=metrica)
        
        if form_metrica.is_valid():
            try:
                with transaction.atomic():
                    metrica = form_metrica.save(commit=False)
                    
                    # Adicionar jogador
                    metrica.jogador = jogador
                    metrica.save()
                    
                    messages.success(request, 'Métrica editada com sucesso')
                    return redirect(reverse('treinamento:detalhar_metrica', kwargs={'metrica_id': metrica.id}))
                
            except Exception as e:
                messages.error(request, e)
        
        else:
            for erro in form_metrica.non_field_errors():
                messages.error(request, erro)
                
    else:
        form_metrica = MetricaForm(instance=metrica)
        
    return render(request, 'treinamento/editar_metrica.html', {'form_metrica': form_metrica})

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
                        
                    messages.success(request, 'Registro de treinamento adicionado com sucesso')
                    return redirect(reverse('treinamento:detalhar_registro_treinamento', 
                                            kwargs={'registro_id': registro_treinamento.id}))
                
            except Exception as e:
                messages.error(request, e)
        
        else:
            for erro in form_registro_treinamento.non_field_errors():
                messages.error(request, erro)
                
    else:
        form_registro_treinamento = RegistroTreinamentoForm()
        
    return render(request, 'treinamento/adicionar_registro_treinamento.html', {'form_registro_treinamento': form_registro_treinamento})

@login_required
def apagar_registro_treinamento(request, registro_id):
    """Apaga um registro de treinamento"""
    jogador = request.user.jogador
    
    registro_treinamento = get_object_or_404(RegistroTreinamento, jogador=jogador, id=registro_id)
    
    if request.POST:
        try:
            with transaction.atomic():
                registro_treinamento.delete()
                
                messages.success(request, 'Registro de treinamento apagado com sucesso')
                return redirect(reverse('treinamento:listar_registros_treinamento'))
            
        except Exception as e:
            messages.error(request, e)
        
    return render(request, 'treinamento/apagar_registro_treinamento.html', {'registro_treinamento': registro_treinamento})

@login_required
def listar_registros_treinamento(request):
    """Lista registros de treinamento de um jogador"""
    registros = RegistroTreinamento.objects.filter(jogador=request.user.jogador)
    
    return render(request, 'treinamento/listar_registros_treinamento.html', {'registros': registros})

@login_required
def detalhar_registro_treinamento(request, registro_id):
    """Detalha um registro de treinamento"""
    
    registro_treinamento = get_object_or_404(RegistroTreinamento.objects.annotate(duracao=ExpressionWrapper(F('fim') - F('inicio'), 
                                                                                                 output_field=DurationField())), 
                                                                                                 id=registro_id, jogador=request.user.jogador)
    
    # Formatar duracao
    segundos = int(registro_treinamento.duracao.total_seconds())
    horas, minutos = converter_segundos_duracao(segundos)
    registro_treinamento.duracao = f'{horas}:{minutos:02d}'
    
    resultados = ResultadoTreinamento.objects.filter(registro_treinamento=registro_treinamento)
    
    return render(request, 'treinamento/detalhar_registro_treinamento.html', {'registro_treinamento': registro_treinamento,
                                                                              'resultados': resultados})

@login_required
def editar_registro_treinamento(request, registro_id):
    """Edita um registro de treinamento"""
    jogador = request.user.jogador
    
    registro_treinamento = get_object_or_404(RegistroTreinamento, jogador=jogador, id=registro_id)
    
    if request.POST:
        form_registro_treinamento = RegistroTreinamentoForm(request.POST, instance=registro_treinamento)
        
        if form_registro_treinamento.is_valid():
            try:
                with transaction.atomic():
                    registro_treinamento = form_registro_treinamento.save(commit=False)
                    
                    # Adicionar jogador
                    registro_treinamento.jogador = jogador
                    registro_treinamento.save()
                        
                    messages.success(request, 'Registro de treinamento editado com sucesso')
                    return redirect(reverse('treinamento:detalhar_registro_treinamento', 
                                            kwargs={'registro_id': registro_treinamento.id}))
                
            except Exception as e:
                messages.error(request, e)
        
        else:
            for erro in form_registro_treinamento.non_field_errors():
                messages.error(request, erro)
                
    else:
        form_registro_treinamento = RegistroTreinamentoForm(instance=registro_treinamento)
        
    return render(request, 'treinamento/editar_registro_treinamento.html', {'form_registro_treinamento': form_registro_treinamento})

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
                        
                    messages.success(request, 'Resultado de treinamento adicionado com sucesso')
                    return redirect(reverse('treinamento:detalhar_registro_treinamento', 
                                            kwargs={'registro_id': registro_id}))
                
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
    
    links_uteis = LinkUtil.objects.filter(jogador=jogador)[:3]
    
    metricas = Metrica.objects.filter(jogador=jogador)[:3]
    
    ultimos_registros = RegistroTreinamento.objects.filter(jogador=jogador).order_by('-fim')[:3]
    
    dados_treinamento = {}
    dados_treinamento['qtd_anotacoes'] = Anotacao.objects.filter(jogador=jogador).count()
    
    dados_treinamento['qtd_metricas'] = Metrica.objects.filter(jogador=jogador).count()
    
    dados_treinamento['qtd_resultados'] = ResultadoTreinamento.objects.filter(registro_treinamento__jogador=jogador).count()
    
    dados_treinamento['qtd_sessoes_treinamento'] = RegistroTreinamento.objects.filter(jogador=jogador).count()
    
    dados_treinamento['tempo_registrado'] = (RegistroTreinamento.objects.filter(jogador=jogador) \
        .annotate(diff=ExpressionWrapper(F('fim') - F('inicio'), output_field=DurationField())) \
        .aggregate(duracao_total=Sum('diff'))['duracao_total'] or 0)
    if dados_treinamento['tempo_registrado']:
        segundos = int(dados_treinamento['tempo_registrado'].total_seconds())
        horas, minutos = converter_segundos_duracao(segundos)
        
        dados_treinamento['tempo_registrado'] = f'{horas}:{minutos:02d}'
    else:
        dados_treinamento['tempo_registrado'] = '0:00'
        
    return render(request, 'treinamento/painel.html', {'ultimas_anotacoes': ultimas_anotacoes, 'metricas': metricas, 
                                                       'ultimos_registros': ultimos_registros, 'dados_treinamento': dados_treinamento,
                                                       'links_uteis': links_uteis})
