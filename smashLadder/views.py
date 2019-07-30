# -*- coding: utf-8 -*-
"""Views gerais"""
from django.db.models.expressions import F
from django.http.response import JsonResponse
from django.shortcuts import render
from django.templatetags.static import static
from django.utils import timezone

from ladder.models import PosicaoLadder, DesafioLadder, HistoricoLadder
import pandas as pd
from smashLadder.management.commands.analise import analisar, \
    gerar_acumulados_anteriores, analisar_resultado_acumulado_entre_jogadores, \
    CAMINHO_ANALISES
from smashLadder.utils import mes_ano_prox


def home(request):
    """Detalhar regras da ladder"""
    
    top_10_ladder = PosicaoLadder.objects.filter(posicao__lte=10).order_by('posicao').select_related('jogador__user', 'jogador__main') \
        .prefetch_related('jogador__registroferias_set')
    
    ultimos_desafios_ladder = DesafioLadder.objects.all().order_by('-data_hora').select_related('desafiante', 'desafiado', 'cancelamentodesafioladder')[:4]
    
    if request.user.is_authenticated:
        for desafio in ultimos_desafios_ladder:
            desafio.is_cancelavel = desafio.cancelavel_por_jogador(request.user.jogador)
    
    return render(request, 'home.html', {'ultimos_desafios_ladder': ultimos_desafios_ladder,
                                                  'top_10_ladder': top_10_ladder})

def analises(request):
    """Mostrar análises dos dados de desafios"""
    imagens = analisar()
    for imagem in imagens:
        imagens[imagem] = 'analises/' + imagens[imagem]
        
    return render(request, 'analises.html', {'imagens': imagens})

def analise_resultado_acumulado_jogadores(request):
    """Retorna dados sobre acumulado de resultados de desafios entre jogadores"""
    if request.is_ajax():
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
                                            'data_hora', 'nick_desafiante', 'score_desafiante', 'posicao_desafiante', 'nick_desafiado', 
                                                    'score_desafiado', 'posicao_desafiado', 'desafio_coringa').order_by('data_hora')))
        
        
                
        desafios_df = analisar_resultado_acumulado_entre_jogadores(desafios_df, (mes, ano))
        
        # Trocar NaNs por None, para ser codificado em JSON
        desafios_df = desafios_df.where(pd.notnull(desafios_df), None)
        
        return JsonResponse({'resultado_desafios': desafios_df.values.tolist(), 'jogador_enfrentado': desafios_df.columns.tolist(), 
                             'jogador': desafios_df.index.tolist()})
    