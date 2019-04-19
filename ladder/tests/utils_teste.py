# -*- coding: utf-8 -*-

from jogadores.models import Jogador, Personagem, Stage
from ladder.models import PosicaoLadder, HistoricoLadder, Luta, JogadorLuta, \
    RegistroLadder, LutaLadder, InicioLadder
from ladder.utils import alterar_ladder

LADDER_FORMATO_TESTE = [
        {'nick': 'teets', 'posicao': 1,},
        {'nick': 'saraiva', 'posicao': 2,},
        {'nick': 'sena', 'posicao': 3,},
        {'nick': 'mad', 'posicao': 4,},
        {'nick': 'blöwer', 'posicao': 5,},
        {'nick': 'frodo', 'posicao': 6,},
        {'nick': 'dan', 'posicao': 7,},
        {'nick': 'phils', 'posicao': 8,},
        {'nick': 'rata', 'posicao': 9,},
        {'nick': 'tiovsky', 'posicao': 10,}, ]

def criar_ladder_inicial_teste():
    """Cria uma ladder inicial para teste"""
    jogadores = Jogador.objects.filter(nick__in=[posicao['nick'] for posicao in LADDER_FORMATO_TESTE])
    
    for posicao_ladder in LADDER_FORMATO_TESTE:
        for jogador in jogadores:
            if posicao_ladder['nick'] == jogador.nick:
                jogador_atual = jogador
                break
        InicioLadder.objects.create(posicao=posicao_ladder['posicao'], jogador=jogador_atual)

def criar_ladder_teste():
    """Cria uma ladder básica para teste"""
    jogadores = Jogador.objects.filter(nick__in=[posicao['nick'] for posicao in LADDER_FORMATO_TESTE])
    
    ladder = list()
    for posicao_ladder in LADDER_FORMATO_TESTE:
        for jogador in jogadores:
            if posicao_ladder['nick'] == jogador.nick:
                jogador_atual = jogador
                break
        posicao_ladder = PosicaoLadder.objects.create(posicao=posicao_ladder['posicao'], jogador=jogador_atual)
        ladder.append(posicao_ladder)
        
    return ladder


def criar_ladder_historico_teste(ano, mes):
    """Cria um histórico de ladder para teste"""
    jogadores = Jogador.objects.filter(nick__in=[posicao['nick'] for posicao in LADDER_FORMATO_TESTE])
    
    for posicao_ladder in LADDER_FORMATO_TESTE:
        for jogador in jogadores:
            if posicao_ladder['nick'] == jogador.nick:
                jogador_atual = jogador
                break
        HistoricoLadder.objects.create(posicao=posicao_ladder['posicao'], jogador=jogador_atual, ano=ano, mes=mes)

def criar_luta_teste(jogadores, ganhador, data, criador_luta):
    """Cria um registro de luta básico para teste"""
    luta = Luta.objects.create(ganhador=ganhador, data=data, adicionada_por=criador_luta)
    # Participantes
    for jogador in jogadores:
        JogadorLuta.objects.create(jogador=jogador, luta=luta)
        
    return luta

def criar_luta_completa_teste(jogadores, personagens, ganhador, data, criador_luta, stage):
    """Cria um registro de luta básico para teste"""
    if len(jogadores) != len(personagens):
        raise ValueError('Cada jogador deve ter um personagem')
    luta = Luta.objects.create(ganhador=ganhador, data=data, adicionada_por=criador_luta, stage=stage)
    # Participantes
    for jogador, personagem in zip(jogadores, personagens):
        JogadorLuta.objects.create(jogador=jogador, luta=luta, personagem=personagem)
        
    return luta

def criar_registro_ladder_simples_teste(desafiante, desafiado, score_desafiante, score_desafiado, data_hora, 
                                        desafio_coringa, criador_registro):
    """Cria um registro de ladder simples para teste"""
    return RegistroLadder.objects.create(desafiante=desafiante, desafiado=desafiado, score_desafiante=score_desafiante, 
                                         score_desafiado=score_desafiado, data_hora=data_hora, 
                                         desafio_coringa=desafio_coringa, adicionado_por=criador_registro)
    
def criar_registro_ladder_completo_teste(desafiante, desafiado, score_desafiante, score_desafiado, data_hora, 
                                        desafio_coringa, criador_registro):
    """Cria um registro de ladder completo para teste"""
    qtd_vitorias_desafiante = 0
    qtd_vitorias_desafiado = 0
    
    personagens = list(Personagem.objects.filter(nome__in=['Marth', 'Fox']))
    
    stage = Stage.objects.get(nome='Dreamland')
    
    # Guardar lutas para vincular a ladder
    lutas = list()
    
    # Gerar 1 luta para cada por vez
    while (qtd_vitorias_desafiado + qtd_vitorias_desafiante < score_desafiado + score_desafiante):
        if qtd_vitorias_desafiado < score_desafiado:
            luta = criar_luta_completa_teste([desafiante, desafiado], personagens, desafiado, data_hora.date(), criador_registro, stage)
            lutas.append(luta)
            qtd_vitorias_desafiado += 1
            
        if qtd_vitorias_desafiante < score_desafiante:
            luta = criar_luta_completa_teste([desafiante, desafiado], personagens, desafiante, data_hora.date(), criador_registro, stage)
            lutas.append(luta)
            qtd_vitorias_desafiante += 1
            
    registro_ladder = RegistroLadder.objects.create(desafiante=desafiante, desafiado=desafiado, score_desafiante=score_desafiante, 
                                         score_desafiado=score_desafiado, data_hora=data_hora, 
                                         desafio_coringa=desafio_coringa, adicionado_por=criador_registro)
    
    # Vincular lutas
    for indice, luta in enumerate(lutas):
        LutaLadder.objects.create(registro_ladder=registro_ladder, luta=luta, indice_registro_ladder=indice+1)
        
    return registro_ladder

def validar_registro_ladder_teste(registro_ladder, admin_validador):
    """Valida um registro de ladder e altera posições para teste"""
    alterar_ladder(registro_ladder)
    
    registro_ladder.admin_validador = admin_validador
    registro_ladder.save()
    
def gerar_campos_formset(dados, prefixo_form):
    """Instancia um formset diretamente para teste"""
    total_forms = {f'{prefixo_form}-TOTAL_FORMS': f'{len(dados)}'}
    initial_forms = {f'{prefixo_form}-INITIAL_FORMS': '0'}
    
    dados_formatado = {**total_forms, **initial_forms}
    for indice, dados_form in enumerate(dados):
        for nome, valor in dados_form.items():
            dados_formatado[f'{prefixo_form}-{indice}-{nome}'] = valor
    
    return dados_formatado
