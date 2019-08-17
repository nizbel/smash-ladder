# -*- coding: utf-8 -*-
"""Views gerais"""
from django.db.models.expressions import F, Case, When, Value
from django.db.models.fields import IntegerField
from django.db.models.query_utils import Q
from django.http.response import JsonResponse
from django.shortcuts import render, get_object_or_404
from django.templatetags.static import static
from django.utils import timezone

from jogadores.models import Jogador
from ladder.models import PosicaoLadder, DesafioLadder, HistoricoLadder, \
    JogadorLuta
import pandas as pd
from smashLadder.management.commands.analise import analisar, \
    gerar_acumulados_anteriores, analisar_resultado_acumulado_entre_jogadores, \
    CAMINHO_ANALISES, analisar_resultado_acumulado_para_um_jogador, \
    analisar_vitorias_contra_personagens_para_um_jogador, \
    analisar_resultados_por_posicao, analisar_vitorias_por_personagem
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
                                            'data_hora', 'nick_desafiante', 'score_desafiante', 'nick_desafiado', 
                                                    'score_desafiado').order_by('data_hora')))
        
        desafios_df = analisar_resultado_acumulado_entre_jogadores(desafios_df, (mes, ano))
        
        # Trocar NaNs por None, para ser codificado em JSON
        desafios_df = desafios_df.where(pd.notnull(desafios_df), None)
        
        return JsonResponse({'resultado_desafios': desafios_df.values.tolist(), 'jogador_enfrentado': desafios_df.columns.tolist(), 
                             'jogador': desafios_df.index.tolist()})
        
def analises_por_jogador(request):
    """Mostrar análises dos dados de desafios por jogador"""
    jogadores = Jogador.objects.all()
    return render(request, 'analises_por_jogador.html', {'jogadores': jogadores})
                             
def analise_resultado_acumulado_para_um_jogador(request):
    """Retorna dados sobre acumulado de resultados de desafios de um jogador"""
    if request.is_ajax():
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
    if request.is_ajax():
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
    
def analise_resultado_por_posicao(request):
    """Retorna dados sobre resultados por posição"""
    if request.is_ajax():
        
        desafios_df = pd.DataFrame(list(DesafioLadder.validados.all().annotate(nick_desafiante=F('desafiante__nick')) \
                                    .annotate(nick_desafiado=F('desafiado__nick')).values(
                                        'data_hora', 'nick_desafiante', 'score_desafiante', 'posicao_desafiante', 'nick_desafiado', 
                                        'score_desafiado', 'posicao_desafiado', 'desafio_coringa').order_by('data_hora')))
        
        desafios_df = analisar_resultados_por_posicao(desafios_df)
        
        return JsonResponse({'posicao_desafiante': desafios_df['posicao_desafiante'].tolist(), 
                             'posicao_desafiado': desafios_df['posicao_desafiado'].tolist(),
                             'qtd_desafios': desafios_df['qtd_desafios'].tolist(),
                             'resultado': desafios_df['resultado'].tolist()})
        
def analise_resultado_por_diferenca_posicao(request):
    pass
        
def analise_vitorias_por_personagem(request):
    """Retorna dados sobre vitórias por personagem"""
    if request.is_ajax():
        
        desafios_personagens_df = pd.DataFrame(list(JogadorLuta.objects.filter(personagem__isnull=False, 
                                                                           luta__lutaladder__desafio_ladder__cancelamentodesafioladder__isnull=True, 
                                                                           luta__lutaladder__desafio_ladder__admin_validador__isnull=False) \
                                                .annotate(nome_personagem=F('personagem__nome')) \
                                                .annotate(vitoria=Case(When(luta__ganhador=F('jogador'), then=Value(1)), default=0,
                                                                        output_field=IntegerField())) \
                                                .values('nome_personagem', 'vitoria')))
        
        desafios_personagens_df = analisar_vitorias_por_personagem(desafios_personagens_df)
        
        return JsonResponse({'qtd_lutas': desafios_personagens_df['qtd_lutas'].tolist(), 
                             'perc_vitorias': desafios_personagens_df['perc_vitorias'].tolist(),
                             'personagem': desafios_personagens_df.index.tolist()})  
