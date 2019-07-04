# -*- coding: utf-8 -*-

import datetime
import os

from django.core.management.base import BaseCommand
from django.db.models.expressions import F, Case, When, Value
from django.db.models.fields import IntegerField
from django.utils import timezone

from ladder.models import DesafioLadder, JogadorLuta
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


CAMINHO_ANALISES = 'smashLadder/static/analises/'

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
            if (datetime.datetime.now() - horario).seconds > 120:
                os.remove(os.path.join(CAMINHO_ANALISES, img))
        
    
    desafios_df = pd.DataFrame(list(DesafioLadder.validados.all().annotate(nick_desafiante=F('desafiante__nick')) \
                                    .annotate(nick_desafiado=F('desafiado__nick')).values(
                                        'data_hora', 'nick_desafiante', 'score_desafiante', 'posicao_desafiante', 'nick_desafiado', 
                                        'score_desafiado', 'posicao_desafiado', 'desafio_coringa').order_by('data_hora')))
    
    imgs = {}
    imgs['result_acum_entre_jogadores'] = analisar_resultado_acumulado_entre_jogadores(desafios_df)
      
    imgs['result_por_posicao'] = analisar_resultados_por_posicao(desafios_df)
      
    imgs_resultados_dif_posicao = analisar_resultados_por_dif_de_posicao(desafios_df)
    imgs['result_dif_posicao'] = imgs_resultados_dif_posicao[0]
    imgs['result_dif_posicao_perc'] = imgs_resultados_dif_posicao[1]
    
    desafios_personagens_df = pd.DataFrame(list(JogadorLuta.objects.filter(personagem__isnull=False) \
                                                .annotate(nome_personagem=F('personagem__nome')) \
                                                .annotate(vitoria=Case(When(luta__ganhador=F('jogador'), then=Value(1)), default=0,
                                                                        output_field=IntegerField())) \
                                                .values('nome_personagem', 'vitoria')))
     
    imgs['vitorias_por_personagem'] = analisar_vitorias_por_personagem(desafios_personagens_df)
    
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
    
    # RESULTADO POR PAR DESAFIANTE/DESAFIADO
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
    resultado_pares_df = resultado_pares_df.drop(['score_desafiante', 'posicao_desafiante', 'qtd_desafios',
                                        'score_desafiado', 'posicao_desafiado', 'desafio_coringa'], axis=1)
    
    # Remover índices
    resultado_pares_df = resultado_pares_df.reset_index([0,1])
    
    # Adicionar pares alternos
    aux_df = resultado_pares_df.copy(True)
    aux_df[['nick_desafiante', 'nick_desafiado']] = aux_df[['nick_desafiado', 'nick_desafiante']].values
    aux_df['resultado'] *= -1
    
    resultado_pares_df = resultado_pares_df.append(aux_df, sort=True, ignore_index=True)
    
    del(aux_df)
    
    resultado_pares_df = resultado_pares_df.pivot(index='nick_desafiante', columns='nick_desafiado', values='resultado')
     
    plt.rcParams.update({'font.size': 10, 'figure.figsize': (12, 14)})
    plt.figure()
     
    plt.pcolor(resultado_pares_df)
    plt.yticks(np.arange(0.5, len(resultado_pares_df.index), 1), resultado_pares_df.index)
    plt.xticks(np.arange(0.5, len(resultado_pares_df.columns), 1), resultado_pares_df.columns, rotation='vertical')
    plt.xlabel('Oponente enfrentado')
    plt.title('Média de jogos ganhos ao enfrentar oponente')

    color_bar = plt.colorbar(orientation='horizontal', label='Média de jogos ganhos')          
    cbytick_obj = plt.getp(color_bar.ax.axes, 'yticklabels')               
    plt.setp(cbytick_obj)
    
    if not mes_ano:
        data_atual = timezone.localtime()
        nome_imagem = f'acumulado_entre_jogadores_{data_atual.year}_{data_atual.month}'
        nome_formatado = salvar_imagem(nome_imagem, plt)
    else:
        nome_imagem = f'acumulado_entre_jogadores_{mes_ano[1]}_{mes_ano[0]}'
        nome_formatado = salvar_imagem(nome_imagem, plt, alteravel=False)
    
    return nome_formatado

def analisar_resultados_por_posicao(df):
    """Gera imagem para resultado de desafios por posição de desafiante/desafiado"""
    resultados_posicao_df = df.copy(True)
    
    resultados_posicao_df['qtd_desafios'] = 1
     
    resultados_posicao_df = resultados_posicao_df.groupby(['posicao_desafiante', 'posicao_desafiado']).sum()
    resultados_posicao_df['resultado'] = (resultados_posicao_df['score_desafiante'] - resultados_posicao_df['score_desafiado']) / resultados_posicao_df['qtd_desafios']
     
    resultados_posicao_df = resultados_posicao_df.reset_index(level=[0,1])
    
    plt.rcParams.update({'font.size': 10, 'figure.figsize': (12, 8)})
    plt.figure()
    
    max_qtd_desafios = int(resultados_posicao_df['qtd_desafios'].max())
    resultados_posicao_df.plot.scatter(x='posicao_desafiante', y='posicao_desafiado', c='resultado', cmap='viridis', 
                                       s=resultados_posicao_df['qtd_desafios'] / max_qtd_desafios * 100)
    
    nome_imagem = 'qtd_result_por_pos'
    nome_formatado = salvar_imagem(nome_imagem, plt)
    
    return nome_formatado
    
def analisar_resultados_por_dif_de_posicao(df):
    """Gera imagens para resultados de desafios com base na diferença de posição"""
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

    nome_imagem_1 = 'vit_derr'
    nome_formatado_1 = salvar_imagem(nome_imagem_1, plt)
    
    perc_resultados_dif_pos_df['qtd_desafios'] = 1

    perc_resultados_dif_pos_df = perc_resultados_dif_pos_df.groupby(['resultado', 'diferenca_posicoes']).sum()
    
    perc_resultados_dif_pos_df = perc_resultados_dif_pos_df.reset_index(level=[0])

    perc_resultados_dif_pos_df = perc_resultados_dif_pos_df.pivot(columns='resultado', values='qtd_desafios')
    
    perc_resultados_dif_pos_df = perc_resultados_dif_pos_df.fillna(0)
    
    perc_resultados_dif_pos_df['% Vitórias'] = 100* perc_resultados_dif_pos_df['Vitória'] / \
        (perc_resultados_dif_pos_df['Vitória'] + perc_resultados_dif_pos_df['Derrota'])
    perc_resultados_dif_pos_df['% Derrotas'] = 100* perc_resultados_dif_pos_df['Derrota'] / \
        (perc_resultados_dif_pos_df['Vitória'] + perc_resultados_dif_pos_df['Derrota'])
    
    perc_resultados_dif_pos_df = perc_resultados_dif_pos_df.drop(['Derrota', 'Vitória'], axis=1)
    
    perc_resultados_dif_pos_df = perc_resultados_dif_pos_df.rename_axis('', axis='columns')
    
    perc_resultados_dif_pos_df.plot.bar(stacked=True)

    nome_imagem_2 = 'percentual'
    nome_formatado_2 = salvar_imagem(nome_imagem_2, plt)
    
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
    vitorias_por_personagem_df = df.copy(True)

    vitorias_por_personagem_df['Qtd. lutas'] = 1    
    
    vitorias_por_personagem_df = vitorias_por_personagem_df.groupby('nome_personagem').sum()

    
    plt.rcParams.update({'font.size': 10, 'figure.figsize': (14, 7)})
    plt.figure()
    
    vitorias_por_personagem_df = vitorias_por_personagem_df.rename_axis('Personagem')
    
    vitorias_por_personagem_df['% Vitórias'] = 100 * vitorias_por_personagem_df['vitoria'] / vitorias_por_personagem_df['Qtd. lutas']
    
    vitorias_por_personagem_df = vitorias_por_personagem_df.drop('vitoria', axis=1)

    # Reordenar colunas
    cols = vitorias_por_personagem_df.columns.tolist()
    cols = cols[-1:] + cols[:-1]
    vitorias_por_personagem_df = vitorias_por_personagem_df[cols]
        
    vitorias_por_personagem_df.plot.bar()
    
    nome_imagem = 'vitorias_por_personagem'
    nome_formatado = salvar_imagem(nome_imagem, plt)
    
    return nome_formatado

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
    
