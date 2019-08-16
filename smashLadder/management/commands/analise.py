# -*- coding: utf-8 -*-

import datetime
import os

from django.core.management.base import BaseCommand
from django.db.models.expressions import F, Case, When, Value
from django.db.models.fields import IntegerField
from django.utils import timezone

from ladder.models import DesafioLadder, JogadorLuta, Luta
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from smashLadder import settings


CAMINHO_ANALISES = 'smashLadder/static/analises/' if settings.DEBUG else f'{settings.STATIC_ROOT}/analises/'
TEMPO_APAGAR_IMAGENS = 300
TEMPO_GERAR_NOVA_IMAGEM = 180


class Command(BaseCommand):
    help = 'Teste pandas'

    def handle(self, *args, **options):
        analisar()
        
def analisar():
    """Roda análises cadastradas"""
    # Apagar imagens anteriores
    for img in [f for f in os.listdir(CAMINHO_ANALISES) if os.path.isfile(os.path.join(CAMINHO_ANALISES, f))]:
        if '-' in img:
            horario = datetime.datetime.strptime(img.split('-', 1)[1].split('.')[0], '%Y-%m-%d-%H-%M-%S')
            if (datetime.datetime.now() - horario).seconds > TEMPO_APAGAR_IMAGENS:
                os.remove(os.path.join(CAMINHO_ANALISES, img))
        
    
    desafios_df = pd.DataFrame(list(DesafioLadder.validados.all().annotate(nick_desafiante=F('desafiante__nick')) \
                                    .annotate(nick_desafiado=F('desafiado__nick')).values(
                                        'data_hora', 'nick_desafiante', 'score_desafiante', 'posicao_desafiante', 'nick_desafiado', 
                                        'score_desafiado', 'posicao_desafiado', 'desafio_coringa').order_by('data_hora')))
    
    imgs = {}
       
#     imgs['result_por_posicao'] = analisar_resultados_por_posicao(desafios_df)
       
    imgs_resultados_dif_posicao = analisar_resultados_por_dif_de_posicao(desafios_df)
    imgs['result_dif_posicao'] = imgs_resultados_dif_posicao[0]
    imgs['result_dif_posicao_perc'] = imgs_resultados_dif_posicao[1]
     
    desafios_personagens_df = pd.DataFrame(list(JogadorLuta.objects.filter(personagem__isnull=False, 
                                                                           luta__lutaladder__desafio_ladder__cancelamentodesafioladder__isnull=True, 
                                                                           luta__lutaladder__desafio_ladder__admin_validador__isnull=False) \
                                                .annotate(nome_personagem=F('personagem__nome')) \
                                                .annotate(vitoria=Case(When(luta__ganhador=F('jogador'), then=Value(1)), default=0,
                                                                        output_field=IntegerField())) \
                                                .values('nome_personagem', 'vitoria')))
      
    imgs['vitorias_por_personagem'] = analisar_vitorias_por_personagem(desafios_personagens_df)
    
#     desafios_jogadores_personagens_df = pd.DataFrame(list(JogadorLuta.objects.filter(personagem__isnull=False) \
#                                                 .annotate(vitoria=Case(When(luta__ganhador=F('jogador'), then=Value(1)), default=0,
#                                                                         output_field=IntegerField())) \
#                                                 .values('jogador__nick', 'personagem__nome', 'vitoria', 'luta')))
#      
#     imgs['vitorias_contra_personagem'] = analisar_vitorias_contra_personagens(desafios_jogadores_personagens_df)
    
    # ANÁLISE ESPECÍFICA
#     nick_especifico = 'Mad'
#     desafios_especifico = desafios_df[(desafios_df['nick_desafiado'] == nick_especifico) | (desafios_df['nick_desafiante'] == nick_especifico)]
#     desafios_especifico['score'] = np.where(desafios_especifico['nick_desafiante'] == nick_especifico, 
#                                             desafios_especifico['score_desafiante'], desafios_especifico['score_desafiado'])
#     desafios_especifico['oponente'] = np.where(desafios_especifico['nick_desafiante'] == nick_especifico, 
#                                                desafios_especifico['nick_desafiado'], desafios_especifico['nick_desafiante'])
#     print(desafios_especifico)
    
#     desafios_especifico.plot(kind='bar', x='oponente', y='score', title='Resultado desafiante')

    return imgs
    
def analisar_resultado_acumulado_entre_jogadores(df, mes_ano=None):
    if not mes_ano:
        data_atual = timezone.localtime()
        mes_ano = (data_atual.month, data_atual.year)
    nome_arquivo = f'acumulado_entre_jogadores_{mes_ano[1]}_{mes_ano[0]}'
    
    # Retornar imagem já existente
    for img in [f for f in os.listdir(CAMINHO_ANALISES) if os.path.isfile(os.path.join(CAMINHO_ANALISES, f))]:
        if f'{nome_arquivo}' in img and '-' in img:
            horario = datetime.datetime.strptime(img.split('-', 1)[1].split('.')[0], '%Y-%m-%d-%H-%M-%S')
            if (datetime.datetime.now() - horario).seconds <= TEMPO_GERAR_NOVA_IMAGEM:
                return img
    
    resultado_pares_df = df.copy(True)
     
    # Adicionar coluna para contar qtd de desafios entre pares
    resultado_pares_df['qtd_desafios'] = 1
    
    # Organizar pares de forma que o desafiante seja sempre o menor nome
    resultado_pares_df['min'] = resultado_pares_df[['nick_desafiante', 'nick_desafiado']].min(axis=1)
    
    inverter_idx = resultado_pares_df['nick_desafiante'] != resultado_pares_df['min']
    resultado_pares_df.loc[inverter_idx, ['nick_desafiante', 'nick_desafiado', 'score_desafiante', 'score_desafiado']] = resultado_pares_df.loc[inverter_idx, [
        'nick_desafiado', 'nick_desafiante', 'score_desafiado', 'score_desafiante']].values
    
    # Agrupar registros de desafio entre mesmo par
    resultado_pares_df = resultado_pares_df.groupby(['nick_desafiante', 'nick_desafiado']).sum()
    
    # Calcular resultado de partidas entre mesmo par
    resultado_pares_df['resultado'] = (resultado_pares_df['score_desafiante'] - resultado_pares_df['score_desafiado']) / resultado_pares_df['qtd_desafios']
    
    # Remover colunas não utilizadas
    resultado_pares_df = resultado_pares_df.drop(['score_desafiante', 'qtd_desafios', 'score_desafiado'], axis=1)
    
    # Remover índices
    resultado_pares_df = resultado_pares_df.reset_index([0,1])
    
    # Adicionar pares alternos
    aux_df = resultado_pares_df.copy(True)
    aux_df[['nick_desafiante', 'nick_desafiado']] = aux_df[['nick_desafiado', 'nick_desafiante']].values
    aux_df['resultado'] *= -1
    
    resultado_pares_df = resultado_pares_df.append(aux_df, sort=True, ignore_index=True)
    
    del(aux_df)
    
    resultado_pares_df = resultado_pares_df.pivot(index='nick_desafiante', columns='nick_desafiado', values='resultado')
     
    return resultado_pares_df

def analisar_resultados_por_posicao(df):
    """Gera imagem para resultado de desafios por posição de desafiante/desafiado"""
    nome_arquivo = 'qtd_result_por_pos'
    
    # Retornar imagem já existente
    for img in [f for f in os.listdir(CAMINHO_ANALISES) if os.path.isfile(os.path.join(CAMINHO_ANALISES, f))]:
        if f'{nome_arquivo}_' in img and '-' in img:
            horario = datetime.datetime.strptime(img.split('-', 1)[1].split('.')[0], '%Y-%m-%d-%H-%M-%S')
            if (datetime.datetime.now() - horario).seconds <= TEMPO_GERAR_NOVA_IMAGEM:
                return img
            
    resultados_posicao_df = df.copy(True)
    
    resultados_posicao_df['qtd_desafios'] = 1
     
    resultados_posicao_df = resultados_posicao_df.groupby(['posicao_desafiante', 'posicao_desafiado']).sum()
    resultados_posicao_df['resultado'] = (resultados_posicao_df['score_desafiante'] - resultados_posicao_df['score_desafiado']) / resultados_posicao_df['qtd_desafios']
     
    resultados_posicao_df = resultados_posicao_df.reset_index(level=[0,1])
    
    max_qtd_desafios = int(resultados_posicao_df['qtd_desafios'].max())
    resultados_posicao_df['qtd_desafios'] = resultados_posicao_df['qtd_desafios'] / max_qtd_desafios * 25
    
    return resultados_posicao_df
    
def analisar_resultados_por_dif_de_posicao(df):
    """Gera imagens para resultados de desafios com base na diferença de posição"""
    nome_arquivo_1 = 'vit_derr'
    nome_arquivo_2 = 'percentual'
    
    img_retornar_1 = None
    img_retornar_2 = None
    # Retornar imagem já existente
    for img in [f for f in os.listdir(CAMINHO_ANALISES) if os.path.isfile(os.path.join(CAMINHO_ANALISES, f))]:
        if img_retornar_1 == None and f'{nome_arquivo_1}_' in img and '-' in img:
            horario = datetime.datetime.strptime(img.split('-', 1)[1].split('.')[0], '%Y-%m-%d-%H-%M-%S')
            if (datetime.datetime.now() - horario).seconds <= TEMPO_GERAR_NOVA_IMAGEM:
                img_retornar_1 = img
        if img_retornar_2 == None and f'{nome_arquivo_2}_' in img and '-' in img:
            horario = datetime.datetime.strptime(img.split('-', 1)[1].split('.')[0], '%Y-%m-%d-%H-%M-%S')
            if (datetime.datetime.now() - horario).seconds <= TEMPO_GERAR_NOVA_IMAGEM:
                img_retornar_2 = img
                
        if img_retornar_1 != None and img_retornar_2 != None:
            return (img_retornar_1, img_retornar_2)
            
    perc_resultados_dif_pos_df = df.copy(True)
    
    perc_resultados_dif_pos_df['resultado'] = np.where(perc_resultados_dif_pos_df['score_desafiante'] == 3, 
                                                'Vitória', 'Derrota')
    
    perc_resultados_dif_pos_df['diferenca_posicoes'] = perc_resultados_dif_pos_df['posicao_desafiante'] - perc_resultados_dif_pos_df['posicao_desafiado']
    
    perc_resultados_dif_pos_df = perc_resultados_dif_pos_df.drop(['data_hora', 'nick_desafiante', 'score_desafiante', 'posicao_desafiante', 'nick_desafiado', 
                                        'score_desafiado', 'posicao_desafiado', 'desafio_coringa'], axis=1)
    
    plt.rcParams.update({'font.size': 10, 'figure.figsize': (8, 5)})
    plt.figure()
    
    val_min = int(perc_resultados_dif_pos_df['diferenca_posicoes'].describe()['min'])
    val_max = int(perc_resultados_dif_pos_df['diferenca_posicoes'].describe()['max'])
    variacao = val_max - val_min
    perc_resultados_dif_pos_df.hist(alpha=0.5, bins=variacao, by='resultado')

    nome_formatado_1 = salvar_imagem(nome_arquivo_1, plt)
    
    perc_resultados_dif_pos_df['qtd_desafios'] = 1

    perc_resultados_dif_pos_df = perc_resultados_dif_pos_df.groupby(['resultado', 'diferenca_posicoes']).sum()
    
    perc_resultados_dif_pos_df = perc_resultados_dif_pos_df.reset_index(level=[0])

    perc_resultados_dif_pos_df = perc_resultados_dif_pos_df.pivot(columns='resultado', values='qtd_desafios')
    
    perc_resultados_dif_pos_df = perc_resultados_dif_pos_df.fillna(0)
    
    perc_resultados_dif_pos_df['% Vitórias'] = 100 * perc_resultados_dif_pos_df['Vitória'] / \
        (perc_resultados_dif_pos_df['Vitória'] + perc_resultados_dif_pos_df['Derrota'])
    perc_resultados_dif_pos_df['% Derrotas'] = 100 * perc_resultados_dif_pos_df['Derrota'] / \
        (perc_resultados_dif_pos_df['Vitória'] + perc_resultados_dif_pos_df['Derrota'])
    
    perc_resultados_dif_pos_df = perc_resultados_dif_pos_df.drop(['Derrota', 'Vitória'], axis=1)
    
    perc_resultados_dif_pos_df = perc_resultados_dif_pos_df.rename_axis('', axis='columns')
    
    perc_resultados_dif_pos_df.plot.bar(stacked=True, legend=False)
    
    plt.legend(loc=9, bbox_to_anchor=(0.5, 1.1), ncol=2, fancybox=True, shadow=True)
    
    plt.xlabel('Diferença de posições')

    nome_formatado_2 = salvar_imagem(nome_arquivo_2, plt)
    
    return (nome_formatado_1, nome_formatado_2)

def gerar_acumulados_anteriores():
    """Gera análises de acumulados de resultados anteriores, que não sejam alteráveis"""
    for ano in range(2019, timezone.localtime().year+1):
        for mes in range(5, timezone.localtime().month+1):
            if f'acumulado_entre_jogadores_{ano}_{mes-1}.png' not in \
                    [f for f in os.listdir(CAMINHO_ANALISES) if os.path.isfile(os.path.join(CAMINHO_ANALISES, f))]:
                desafios_anteriores_df = pd.DataFrame(list(DesafioLadder.validados.filter(data_hora__lt=timezone.datetime(ano, mes, 1, 0, 0, tzinfo=timezone.get_current_timezone())) \
                                                           .annotate(nick_desafiante=F('desafiante__nick')) \
                                                .annotate(nick_desafiado=F('desafiado__nick')).values(
                                                    'data_hora', 'nick_desafiante', 'score_desafiante', 'posicao_desafiante', 'nick_desafiado', 
                                                    'score_desafiado', 'posicao_desafiado', 'desafio_coringa').order_by('data_hora')))
                
                analisar_resultado_acumulado_entre_jogadores(desafios_anteriores_df, (mes-1, ano))
        
def analisar_vitorias_por_personagem(df):
    """Gera imagem para quantidade de vitórias por personagem"""
    nome_arquivo = 'vitorias_por_personagem'
    
    # Retornar imagem já existente
    for img in [f for f in os.listdir(CAMINHO_ANALISES) if os.path.isfile(os.path.join(CAMINHO_ANALISES, f))]:
        if f'{nome_arquivo}_' in img and '-' in img:
            horario = datetime.datetime.strptime(img.split('-', 1)[1].split('.')[0], '%Y-%m-%d-%H-%M-%S')
            if (datetime.datetime.now() - horario).seconds <= TEMPO_GERAR_NOVA_IMAGEM:
                return img
            
    vitorias_por_personagem_df = df.copy(True)

    vitorias_por_personagem_df['Qtd. lutas'] = 1    
    
    vitorias_por_personagem_df = vitorias_por_personagem_df.groupby('nome_personagem').sum()
    
    vitorias_por_personagem_df['% Vitórias'] = 100 * vitorias_por_personagem_df['vitoria'] / vitorias_por_personagem_df['Qtd. lutas']
    
    vitorias_por_personagem_df = vitorias_por_personagem_df.drop('vitoria', axis=1)

    # Reordenar colunas
    cols = vitorias_por_personagem_df.columns.tolist()
    cols = cols[-1:] + cols[:-1]
    vitorias_por_personagem_df = vitorias_por_personagem_df[cols]
    
    vitorias_por_personagem_df = vitorias_por_personagem_df.loc[vitorias_por_personagem_df['Qtd. lutas'] >= 10]
    
    plt.rcParams.update({'font.size': 10, 'figure.figsize': (14, 7)})
    plt.figure()
    
    ax = vitorias_por_personagem_df.plot.bar(secondary_y='% Vitórias')
    
    ax.set_xlabel('Personagem (com 10 lutas ou mais)')
    ax.grid('on', which='major', axis='y', linestyle=':', alpha=0.5)

    # Alterar eixo da direita
    ax.right_ax.set_yticks(list(range(10, 101, 10)))
    ax.right_ax.set_yticklabels([f'{n}%' for n in list(range(10, 101, 10))])
    ax.right_ax.grid('on', which='major', axis='y', linestyle='--', c='b', alpha=0.2)
    
    nome_formatado = salvar_imagem(nome_arquivo, plt)
    
    return nome_formatado

def analisar_vitorias_contra_personagens_para_um_jogador(df, nick_jogador, mes_ano=None):
    """Gera imagem para vitórias contra cada personagem para um jogador até mês/ano"""
    vitorias_contra_personagem_df = df.copy(True)
     
    idx_jogador = vitorias_contra_personagem_df['jogador__nick'] == nick_jogador
    vitorias_contra_personagem_df.loc[idx_jogador, ['personagem__nome']] = ''
     
    idx_oponente = vitorias_contra_personagem_df['jogador__nick'] != nick_jogador
    vitorias_contra_personagem_df.loc[idx_oponente, ['jogador__nick']] = ''
    vitorias_contra_personagem_df.loc[idx_oponente, ['vitoria']] = 0
     
    vitorias_contra_personagem_df = vitorias_contra_personagem_df.groupby('luta')['personagem__nome', 'vitoria'].apply(lambda x: x.sum())
     
    vitorias_contra_personagem_df['quantidade_lutas'] = 1
     
    vitorias_contra_personagem_df = vitorias_contra_personagem_df.groupby(['personagem__nome']).sum()
    
    vitorias_contra_personagem_df['percentual_vitorias'] = 100 * vitorias_contra_personagem_df['vitoria'] / vitorias_contra_personagem_df['quantidade_lutas']
    
    vitorias_contra_personagem_df = vitorias_contra_personagem_df.drop('vitoria', axis=1)
    
#     vitorias_contra_personagem_df = vitorias_contra_personagem_df.reset_index([0])
#     print(vitorias_contra_personagem_df)
#      
#     vitorias_contra_personagem_df = vitorias_contra_personagem_df.pivot(index='personagem__nome', values=['Qtd. lutas', 'vitoria'])
                                        
    return vitorias_contra_personagem_df

def salvar_imagem(nome_arquivo, plot_ctrl, formato='png', alteravel=True):
    """Salva imagem no formato especificado"""
    hora_atual = timezone.localtime()
    
    # Arquivos que podem ser alterados com o tempo possuem timestamp mostrando último horário
    if alteravel:
        nome_formatado = nome_arquivo + f'-{hora_atual.strftime("%Y-%m-%d-%H-%M-%S")}.{formato}'
    else:
        nome_formatado = nome_arquivo + f'.{formato}'
        
    caminho = CAMINHO_ANALISES + nome_formatado
    
    plot_ctrl.savefig(caminho, bbox_inches='tight')
    plot_ctrl.close('all')
    
    return nome_formatado
    
def analisar_resultado_acumulado_para_um_jogador(df, nick_jogador, mes_ano=None):
    """Gera dados de resultados de desafio acumulados para um jogador até mês/ano"""
    if not mes_ano:
        data_atual = timezone.localtime()
        mes_ano = (data_atual.month, data_atual.year)

    resultado_pares_df = df.copy(True)
     
    # Adicionar coluna para contar qtd de desafios entre pares
    resultado_pares_df['qtd_desafios'] = 1
    
    # Organizar pares de forma que o desafiante seja sempre o menor nome
    resultado_pares_df['min'] = resultado_pares_df[['nick_desafiante', 'nick_desafiado']].min(axis=1)
    
    inverter_idx = resultado_pares_df['nick_desafiante'] != resultado_pares_df['min']
    resultado_pares_df.loc[inverter_idx, ['nick_desafiante', 'nick_desafiado', 'score_desafiante', 'score_desafiado']] = resultado_pares_df.loc[inverter_idx, [
        'nick_desafiado', 'nick_desafiante', 'score_desafiado', 'score_desafiante']].values
    
    # Agrupar registros de desafio entre mesmo par
    resultado_pares_df = resultado_pares_df.groupby(['nick_desafiante', 'nick_desafiado']).sum()
    
    # Calcular resultado de partidas entre mesmo par
    resultado_pares_df['resultado'] = (resultado_pares_df['score_desafiante'] - resultado_pares_df['score_desafiado']) / resultado_pares_df['qtd_desafios']
    
    # Remover colunas não utilizadas
    resultado_pares_df = resultado_pares_df.drop(['score_desafiante', 'qtd_desafios', 'score_desafiado'], axis=1)
    
    # Remover índices
    resultado_pares_df = resultado_pares_df.reset_index([0,1])
    
    # Colocar jogador como coluna desafiante sempre
    desafiado_idx = resultado_pares_df['nick_desafiado'] == nick_jogador
    resultado_pares_df.loc[desafiado_idx, ['resultado']] = resultado_pares_df.loc[desafiado_idx, ['resultado']] * -1
    resultado_pares_df.loc[desafiado_idx, ['nick_desafiante', 'nick_desafiado']] = resultado_pares_df.loc[desafiado_idx, ['nick_desafiado', 'nick_desafiante']].values
    
    
    resultado_pares_df = resultado_pares_df.drop(['nick_desafiante'], axis=1)
    
    return resultado_pares_df
