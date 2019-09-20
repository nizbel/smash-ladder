# -*- coding: utf-8 -*-
from django.contrib.auth.models import User, Group
from django.utils.text import slugify

from jogadores.models import Jogador, Personagem, Stage


SENHA_TESTE = 'smashsmash'
JOGADORES_TESTE = [
        {'nick': 'teets', 'admin': True},
        {'nick': 'saraiva', 'admin': True,},
        {'nick': 'sena', 'admin': False,},
        {'nick': 'mad', 'admin': False,},
        {'nick': 'blöwer', 'admin': False,},
        {'nick': 'frodo', 'admin': False,},
        {'nick': 'dan', 'admin': False,},
        {'nick': 'phils', 'admin': False,},
        {'nick': 'rata', 'admin': False,},
        {'nick': 'tiovsky', 'admin': False,}, ]

PERSONAGENS_TESTE = [
    {'nome': 'Marth'},
    {'nome': 'Fox'},
    {'nome': 'Jigglypuff'}, ]

STAGES_TESTE = [
    {'nome': 'Dreamland', 'modelo': Stage.TIPO_NORMAL},
    {'nome': 'Dreamland', 'modelo': Stage.TIPO_BATTLEFIELD},
    {'nome': 'Dreamland', 'modelo': Stage.TIPO_OMEGA},
    {'nome': 'Final Destination', 'modelo': Stage.TIPO_NORMAL}, ]

def criar_jogadores_teste(lista_nicks_criar=None):
    """Gera jogadores para teste de acordo com uma lista de nicks, ou todos se lista vazia"""
    # Criar grupo padrão de admins
    Group.objects.get_or_create(name='Admins')
    
    for jogador in JOGADORES_TESTE:
        if not lista_nicks_criar or jogador['nick'] in lista_nicks_criar:
            user = User.objects.create_user(username=slugify(jogador['nick']), email=(slugify(jogador["nick"]) + '@teste.com'), 
                                                             password=SENHA_TESTE)
            Jogador.objects.create(nick=jogador['nick'], admin=jogador['admin'], user=user)
            
def criar_jogador_teste(tag, admin=False):
    """Cria um jogador para teste"""
    user = User.objects.create_user(username=slugify(tag), password=SENHA_TESTE)
    return Jogador.objects.create(nick=tag, admin=admin, user=user)

def criar_personagens_teste():
    """Gera personagens para teste"""
    for personagem in PERSONAGENS_TESTE:
        Personagem.objects.create(nome=personagem['nome'])
        
def criar_stages_teste():
    """Gera stages para teste"""
    for stage in STAGES_TESTE:
        Stage.objects.create(nome=stage['nome'], modelo=stage['modelo'])
        
def criar_stage_teste():
    """Cria um stage para teste"""
    return Stage.objects.create(nome='Dreamland', modelo=Stage.TIPO_NORMAL)
