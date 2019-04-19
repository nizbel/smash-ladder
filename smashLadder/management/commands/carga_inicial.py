# -*- coding: utf-8 -*-
import json

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils.text import slugify

from jogadores.models import Personagem, Stage, Jogador
from ladder.models import InicioLadder, PosicaoLadder


# Mapeia stages que não existem, pois são cópias
STAGE_EXCECOES = [{'nome': 'Battlefield', 'modelo': Stage.TIPO_BATTLEFIELD},
                  {'nome': 'Big Battlefield', 'modelo': Stage.TIPO_BATTLEFIELD},
                  {'nome': 'Final Destination', 'modelo': Stage.TIPO_OMEGA}]


class Command(BaseCommand):
    help = 'Gera carga inicial com personagens, stages e ladder inicial'

    def handle(self, *args, **options):
        try:
            with transaction.atomic():
                # Personagens
                with open('templates/personagens.json', 'r') as arq:
                    personagens = json.loads(arq.read())
                    for personagem in personagens:
                        nome = personagem['nome']
                        if not Personagem.objects.filter(nome=nome).exists():
                            Personagem.objects.create(nome=nome)
        
                # Stages
                with open('templates/stages.json', 'r') as arq:
                    stages = json.loads(arq.read())
                    for stage in stages:
                        nome = stage['nome']
                        for modelo in [Stage.TIPO_NORMAL, Stage.TIPO_BATTLEFIELD, Stage.TIPO_OMEGA]:
                            # Ver se não se trata de exceções
                            if {'nome': nome, 'modelo': modelo} in STAGE_EXCECOES:
                                continue
                            
                            if not Stage.objects.filter(nome=nome, modelo=modelo).exists():
                                Stage.objects.create(nome=nome, modelo=modelo)
        
                with open('templates/ladder_inicial.json', 'r') as arq:
                    posicoes_ladder = json.loads(arq.read())
                    for posicao_ladder in posicoes_ladder:
                        nick_jogador = posicao_ladder['jogador']
                        posicao = posicao_ladder['posicao']
                        
                        # Transformar nick em login mantendo uppercase quando possível
                        username_slug = slugify(nick_jogador)
                        username = ''
                        for caracter_novo, caracter_antigo in zip(username_slug, nick_jogador):
                            if caracter_novo.upper() == caracter_antigo:
                                username += caracter_antigo
                            else:
                                username += caracter_novo
                        
                        # Criar jogador e usuário, todos sem admin na primeira carga
                        user = User.objects.create_user(username=username, password='12345678')
                        jogador = Jogador.objects.create(nick=nick_jogador, admin=False, user=user)
                        
                        InicioLadder.objects.create(posicao=posicao, jogador=jogador)
                        PosicaoLadder.objects.create(posicao=posicao, jogador=jogador)
                        
        except:
            raise