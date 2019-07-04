# -*- coding: utf-8 -*-

import datetime
import os

from django.core.management.base import BaseCommand
from django.db.models.expressions import F
from django.utils import timezone

from ladder.models import DesafioLadder
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


class Command(BaseCommand):
    help = 'Teste pandas'

    def handle(self, *args, **options):
        analisar()
        
def analisar():
    data_atual = timezone.localtime()
    desafios_df = pd.DataFrame(list(DesafioLadder.validados.all().annotate(nick_desafiante=F('desafiante__nick')) \
                                    .annotate(nick_desafiado=F('desafiado__nick')).values(
                                        'data_hora', 'nick_desafiante', 'score_desafiante', 'posicao_desafiante', 'nick_desafiado', 
                                        'score_desafiado', 'posicao_desafiado', 'desafio_coringa').order_by('data_hora')))
    
    # RESULTADO POR PAR DESAFIANTE/DESAFIADO
    resultado_pares_df = desafios_df.copy(True)
     
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
     
    plt.rcParams.update({'font.size': 12, 'figure.figsize': (12, 14)})
    plt.figure()
     
    plt.pcolor(resultado_pares_df)
    plt.yticks(np.arange(0.5, len(resultado_pares_df.index), 1), resultado_pares_df.index)
    plt.xticks(np.arange(0.5, len(resultado_pares_df.columns), 1), resultado_pares_df.columns, rotation='vertical')
    plt.xlabel('Oponente enfrentado')
    plt.title('Média de jogos ganhos ao enfrentar oponente')

    color_bar = plt.colorbar(orientation='horizontal', label='Média de jogos ganhos')          
    cbytick_obj = plt.getp(color_bar.ax.axes, 'yticklabels')               
    plt.setp(cbytick_obj)
    
    salvar_imagem(f'acumulado_entre_jogadores-{data_atual.year}-{data_atual.month}.png', plt)
    
    # RESULTADO POR POSIÇÃO
    resultados_posicao_df = desafios_df.copy(True)
    
    resultados_posicao_df['qtd_desafios'] = 1
     
    resultados_posicao_df = resultados_posicao_df.groupby(['posicao_desafiante', 'posicao_desafiado']).sum()
    resultados_posicao_df['resultado'] = (resultados_posicao_df['score_desafiante'] - resultados_posicao_df['score_desafiado']) / resultados_posicao_df['qtd_desafios']
     
    resultados_posicao_df = resultados_posicao_df.reset_index(level=[0,1])

    # % DE RESULTADOS POR DIFERENÇA DE POSIÇÃO
    perc_resultados_dif_pos_df = desafios_df.copy(True)
    
    perc_resultados_dif_pos_df['resultado'] = np.where(perc_resultados_dif_pos_df['score_desafiante'] == 3, 
                                                'Vitória', 'Derrota')
    
    perc_resultados_dif_pos_df['diferenca_posicoes'] = perc_resultados_dif_pos_df['posicao_desafiante'] - perc_resultados_dif_pos_df['posicao_desafiado']
    
    perc_resultados_dif_pos_df = perc_resultados_dif_pos_df.drop(['data_hora', 'nick_desafiante', 'score_desafiante', 'posicao_desafiante', 'nick_desafiado', 
                                        'score_desafiado', 'posicao_desafiado', 'desafio_coringa'], axis=1)
    
    
    # ANÁLISE ESPECÍFICA
#     nick_especifico = 'Mad'
#     desafios_especifico = desafios_df[(desafios_df['nick_desafiado'] == nick_especifico) | (desafios_df['nick_desafiante'] == nick_especifico)]
#     desafios_especifico['score'] = np.where(desafios_especifico['nick_desafiante'] == nick_especifico, 
#                                             desafios_especifico['score_desafiante'], desafios_especifico['score_desafiado'])
#     desafios_especifico['oponente'] = np.where(desafios_especifico['nick_desafiante'] == nick_especifico, 
#                                                desafios_especifico['nick_desafiado'], desafios_especifico['nick_desafiante'])
#     print(desafios_especifico)
    
#     desafios_especifico.plot(kind='bar', x='oponente', y='score', title='Resultado desafiante')
    plt.rcParams.update({'font.size': 12, 'figure.figsize': (12, 8)})
    plt.figure()
    
    max_qtd_desafios = int(resultados_posicao_df['qtd_desafios'].max())
    resultados_posicao_df.plot.scatter(x='posicao_desafiante', y='posicao_desafiado', c='resultado', cmap='viridis', 
                                       s=resultados_posicao_df['qtd_desafios'] / max_qtd_desafios * 100)
    
    salvar_imagem('qtd_result_por_pos.png', plt)

    plt.rcParams.update({'font.size': 12, 'figure.figsize': (8, 5)})
    plt.figure()
    
    val_min = int(perc_resultados_dif_pos_df['diferenca_posicoes'].describe()['min'])
    val_max = int(perc_resultados_dif_pos_df['diferenca_posicoes'].describe()['max'])
    variacao = val_max - val_min
    perc_resultados_dif_pos_df.hist(alpha=0.5, bins=variacao, by='resultado')

    salvar_imagem('vit_derr.png', plt)
    
    perc_resultados_dif_pos_df['qtd_desafios'] = 1

    perc_resultados_dif_pos_df = perc_resultados_dif_pos_df.groupby(['resultado', 'diferenca_posicoes']).sum()
    
    perc_resultados_dif_pos_df = perc_resultados_dif_pos_df.reset_index(level=[0])

    perc_resultados_dif_pos_df = perc_resultados_dif_pos_df.pivot(columns='resultado', values='qtd_desafios')
    
    perc_resultados_dif_pos_df = perc_resultados_dif_pos_df.fillna(0)
    
    perc_resultados_dif_pos_df['percentual_vitorias'] = 100* perc_resultados_dif_pos_df['Vitória'] / (perc_resultados_dif_pos_df['Vitória'] + perc_resultados_dif_pos_df['Derrota'])
    perc_resultados_dif_pos_df['percentual_derrotas'] = 100* perc_resultados_dif_pos_df['Derrota'] / (perc_resultados_dif_pos_df['Vitória'] + perc_resultados_dif_pos_df['Derrota'])
    
    perc_resultados_dif_pos_df = perc_resultados_dif_pos_df.drop(['Derrota', 'Vitória'], axis=1)
    
    perc_resultados_dif_pos_df.plot.bar(stacked=True)

    salvar_imagem('percentual.png', plt)
    
def salvar_imagem(nome_arquivo, plot_ctrl):
    caminho = 'smashLadder/static/analises/' + nome_arquivo
    if os.path.isfile(caminho):
        os.remove(caminho)
    plot_ctrl.savefig(caminho, bbox_inches='tight')
    
