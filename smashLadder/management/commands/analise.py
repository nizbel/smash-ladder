# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand
from django.db.models.expressions import F

from ladder.models import DesafioLadder
import numpy as np
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt


class Command(BaseCommand):
    help = 'Teste pandas'

    def handle(self, *args, **options):
        analisar()
        
def analisar():
    desafios_df = pd.DataFrame(list(DesafioLadder.validados.all().annotate(nick_desafiante=F('desafiante__nick')) \
                                    .annotate(nick_desafiado=F('desafiado__nick')).values(
                                        'data_hora', 'nick_desafiante', 'score_desafiante', 'posicao_desafiante', 'nick_desafiado', 
                                        'score_desafiado', 'posicao_desafiado', 'desafio_coringa').order_by('data_hora')))
#     print(desafios_df.head())
    print(desafios_df['score_desafiante'].value_counts())
    print(desafios_df['score_desafiado'].value_counts())
    
    # RESULTADO POR PAR DESAFIANTE/DESAFIADO
#     resultado_pares_df = desafios_df.copy(True)
#     
#     resultado_pares_df['qtd_desafios'] = 1
#     
#     resultado_pares_df = resultado_pares_df.groupby(['nick_desafiante', 'nick_desafiado']).sum()
#     resultado_pares_df['resultado'] = (resultado_pares_df['score_desafiante'] - resultado_pares_df['score_desafiado']) / resultado_pares_df['qtd_desafios']
#     
#     resultado_pares_df = resultado_pares_df.drop(['score_desafiante', 'posicao_desafiante', 'qtd_desafios',
#                                         'score_desafiado', 'posicao_desafiado', 'desafio_coringa'], axis=1)
#     
#     resultado_pares_df = resultado_pares_df.reset_index(1)
#     
#     resultado_pares_df = resultado_pares_df.pivot(columns='nick_desafiado', values='resultado')
#         
#     print(resultado_pares_df)
#     
#     plt.rcParams.update({'font.size': 12, 'figure.figsize': (12, 8)})
#     
#     
# #     Index= ['aaa', 'bbb', 'ccc', 'ddd', 'eee']
# #     Cols = ['A', 'B', 'C', 'D']
# #     df = pd.DataFrame(abs(np.random.randn(5, 4)), index=Index, columns=Cols)
#     
#     plt.pcolor(resultado_pares_df)
#     plt.yticks(np.arange(0.5, len(resultado_pares_df.index), 1), resultado_pares_df.index)
#     plt.xticks(np.arange(0.5, len(resultado_pares_df.columns), 1), resultado_pares_df.columns)
# #     max_qtd_desafios = int(resultado_pares_df['qtd_desafios'].max())
# #     resultado_pares_df.plot.scatter(x='nick_desafiante', y='nick_desafiado', c='resultado', cmap='viridis', 
# #                                        s=250)
#     
#     
#     plt.savefig('smashLadder/static/teste3.png')
    
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
    
    print(perc_resultados_dif_pos_df)
    
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
    max_qtd_desafios = int(resultados_posicao_df['qtd_desafios'].max())
    resultados_posicao_df.plot.scatter(x='posicao_desafiante', y='posicao_desafiado', c='resultado', cmap='viridis', 
                                       s=resultados_posicao_df['qtd_desafios'] / max_qtd_desafios * 100)
    
    plt.savefig('smashLadder/static/qtd_result_por_pos.png')

    plt.rcParams.update({'font.size': 12, 'figure.figsize': (8, 5)})
    
    val_min = int(perc_resultados_dif_pos_df['diferenca_posicoes'].describe()['min'])
    val_max = int(perc_resultados_dif_pos_df['diferenca_posicoes'].describe()['max'])
    variacao = val_max - val_min
    perc_resultados_dif_pos_df.hist(alpha=0.5, bins=variacao, by='resultado')

    plt.savefig('smashLadder/static/vit_derr.png')
    
    perc_resultados_dif_pos_df['qtd_desafios'] = 1

    perc_resultados_dif_pos_df = perc_resultados_dif_pos_df.groupby(['resultado', 'diferenca_posicoes']).sum()
    
    perc_resultados_dif_pos_df = perc_resultados_dif_pos_df.reset_index(level=[0])

    perc_resultados_dif_pos_df = perc_resultados_dif_pos_df.pivot(columns='resultado', values='qtd_desafios')
    
    perc_resultados_dif_pos_df = perc_resultados_dif_pos_df.fillna(0)
    
    perc_resultados_dif_pos_df['percentual_vitorias'] = 100* perc_resultados_dif_pos_df['Vitória'] / (perc_resultados_dif_pos_df['Vitória'] + perc_resultados_dif_pos_df['Derrota'])
    perc_resultados_dif_pos_df['percentual_derrotas'] = 100* perc_resultados_dif_pos_df['Derrota'] / (perc_resultados_dif_pos_df['Vitória'] + perc_resultados_dif_pos_df['Derrota'])
    
    perc_resultados_dif_pos_df = perc_resultados_dif_pos_df.drop(['Derrota', 'Vitória'], axis=1)
    
    
    perc_resultados_dif_pos_df.plot.bar(stacked=True)
    plt.savefig('smashLadder/static/percentual.png')
    
