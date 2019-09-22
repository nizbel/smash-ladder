# -*- coding: utf-8 -*-


from django.core.management.base import BaseCommand
from django.utils import timezone

from jogadores.models import Stage
import numpy as np


class Command(BaseCommand):
    help = 'Teste pandas'

    def handle(self, *args, **options):
        analisar()
        
def analisar():
    """Roda análises cadastradas"""
    pass
    
def analisar_resultado_acumulado_entre_jogadores(df, mes_ano=None):
    """Gera dados para resultado acumulado entre jogadores"""
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
    
    # Adicionar pares alternos
    aux_df = resultado_pares_df.copy(True)
    aux_df[['nick_desafiante', 'nick_desafiado']] = aux_df[['nick_desafiado', 'nick_desafiante']].values
    aux_df['resultado'] *= -1
    
    resultado_pares_df = resultado_pares_df.append(aux_df, sort=True, ignore_index=True)
    
    del(aux_df)
    
    resultado_pares_df = resultado_pares_df.pivot(index='nick_desafiante', columns='nick_desafiado', values='resultado')
     
    return resultado_pares_df

def analisar_resultados_por_posicao(df):
    """Gera dados para resultado de desafios por posição de desafiante/desafiado"""
    resultados_posicao_df = df.copy(True)
    
    resultados_posicao_df['qtd_desafios'] = 1
     
    resultados_posicao_df = resultados_posicao_df.groupby(['posicao_desafiante', 'posicao_desafiado']).sum()
    resultados_posicao_df['resultado'] = (resultados_posicao_df['score_desafiante'] - resultados_posicao_df['score_desafiado']) / resultados_posicao_df['qtd_desafios']
     
    resultados_posicao_df = resultados_posicao_df.reset_index(level=[0,1])
    
    return resultados_posicao_df
    
def analisar_resultados_por_dif_de_posicao(df):
    """Gera dados para resultados de desafios com base na diferença de posição"""
    perc_resultados_dif_pos_df = df.copy(True)
    
    perc_resultados_dif_pos_df['resultado'] = np.where(perc_resultados_dif_pos_df['score_desafiante'] == 3, 
                                                'vitoria', 'derrota')
    
    perc_resultados_dif_pos_df['diferenca_posicoes'] = perc_resultados_dif_pos_df['posicao_desafiante'] - perc_resultados_dif_pos_df['posicao_desafiado']
    
    val_min = int(perc_resultados_dif_pos_df['diferenca_posicoes'].describe()['min'])
    val_max = int(perc_resultados_dif_pos_df['diferenca_posicoes'].describe()['max'])
    variacao = val_max - val_min
    perc_resultados_dif_pos_df.hist(alpha=0.5, bins=variacao, by='resultado')

    perc_resultados_dif_pos_df['qtd_desafios'] = 1

    perc_resultados_dif_pos_df = perc_resultados_dif_pos_df.groupby(['resultado', 'diferenca_posicoes']).sum()
    
    perc_resultados_dif_pos_df = perc_resultados_dif_pos_df.reset_index(level=[0])

    perc_resultados_dif_pos_df = perc_resultados_dif_pos_df.pivot(columns='resultado', values='qtd_desafios')
    
    perc_resultados_dif_pos_df = perc_resultados_dif_pos_df.fillna(0)
    
    perc_resultados_dif_pos_df['percentual_vitorias'] = 100 * perc_resultados_dif_pos_df['vitoria'] / \
        (perc_resultados_dif_pos_df['vitoria'] + perc_resultados_dif_pos_df['derrota'])
    perc_resultados_dif_pos_df['percentual_derrotas'] = 100 * perc_resultados_dif_pos_df['derrota'] / \
        (perc_resultados_dif_pos_df['vitoria'] + perc_resultados_dif_pos_df['derrota'])
    
    return perc_resultados_dif_pos_df

def analisar_vitorias_por_personagem(df):
    """Gera dados para quantidade de vitórias por personagem"""
    vitorias_por_personagem_df = df.copy(True)

    vitorias_por_personagem_df['qtd_lutas'] = 1    
    
    vitorias_por_personagem_df = vitorias_por_personagem_df.groupby('nome_personagem').sum()
    
    vitorias_por_personagem_df['perc_vitorias'] = 100 * vitorias_por_personagem_df['vitoria'] / vitorias_por_personagem_df['qtd_lutas']
    
    vitorias_por_personagem_df = vitorias_por_personagem_df.drop('vitoria', axis=1)

    # Reordenar colunas
    cols = vitorias_por_personagem_df.columns.tolist()
    cols = cols[-1:] + cols[:-1]
    vitorias_por_personagem_df = vitorias_por_personagem_df[cols]
    
    return vitorias_por_personagem_df

def analisar_vitorias_contra_personagens_para_um_jogador(df, nick_jogador, mes_ano=None):
    """Gera dados para vitórias contra cada personagem para um jogador até mês/ano"""
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
    
    return vitorias_contra_personagem_df

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

def analisar_resultados_stages_para_um_jogador(df, nick_jogador):
    """Gera dados de resultados em stages para um jogador"""
    resultado_stages_df = df.copy(True)
    
    # Adicionar coluna para contar qtd de lutas
    resultado_stages_df['qtd_lutas'] = 1
    
    # Se modo for battlefield, contar como battlefield, o mesmo para final destination
    bf_idx = resultado_stages_df['luta__stage__modelo'] == Stage.TIPO_BATTLEFIELD
    resultado_stages_df.loc[bf_idx, ['luta__stage__nome']] = 'Battlefield'
    
    fd_idx = resultado_stages_df['luta__stage__modelo'] == Stage.TIPO_OMEGA
    resultado_stages_df.loc[fd_idx, ['luta__stage__nome']] = 'Final Destination'
        
    resultado_stages_df = resultado_stages_df.drop('luta__stage__modelo', axis=1)
    
    resultado_stages_df = resultado_stages_df.groupby('luta__stage__nome').sum()
    
    resultado_stages_df['percentual_vitorias'] = resultado_stages_df['vitoria'] / resultado_stages_df['qtd_lutas'] * 100
    
    return resultado_stages_df

def analisar_vitorias_desafio_para_um_jogador(df, nick_jogador):
    """Gera dados de resultados em stages para um jogador"""
    vitoria_df = df.copy(True)
    
    # Adicionar coluna para contar qtd de lutas
    vitoria_df['qtd_desafios'] = 1
    
    # Se modo for battlefield, contar como battlefield, o mesmo para final destination
    dif_negativa_idx = vitoria_df['diferenca'] < 0
    vitoria_df.loc[dif_negativa_idx, ['diferenca']] = vitoria_df.loc[dif_negativa_idx, ['diferenca']] * -1
    
    vitoria_df = vitoria_df.groupby('diferenca').sum()
    
    return vitoria_df

