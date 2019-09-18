# -*- coding: utf-8 -*-
import datetime
import json

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils.text import slugify

from jogadores.models import Personagem, Stage, Jogador
from ladder.models import InicioLadder, PosicaoLadder, DesafioLadder, \
    HistoricoLadder
from ladder.utils import verificar_posicoes_desafiante_desafiado, alterar_ladder
from smashLadder import settings


# Mapeia stages que não existem, pois são cópias
STAGE_EXCECOES = [{'nome': 'Battlefield', 'modelo': Stage.TIPO_BATTLEFIELD},
                  {'nome': 'Big Battlefield', 'modelo': Stage.TIPO_BATTLEFIELD},
                  {'nome': 'Final Destination', 'modelo': Stage.TIPO_OMEGA}]


class Command(BaseCommand):
    help = 'Gera carga inicial com personagens, stages e ladder inicial'

    def add_arguments(self, parser):
        parser.add_argument('--desafios', action='store_true')
        
    def handle(self, *args, **options):
        try:
            with transaction.atomic():
                InicioLadder.objects.all().delete()
                PosicaoLadder.objects.all().delete()
                
                # Personagens
                with open(f'templates/cargas_iniciais/{settings.JOGO}/personagens.json', 'r') as arq:
                    personagens = json.loads(arq.read())
                    for personagem in personagens:
                        nome = personagem['nome']
                        if not Personagem.objects.filter(nome=nome).exists():
                            Personagem.objects.create(nome=nome)
        
                # Stages
                with open(f'templates/cargas_iniciais/{settings.JOGO}/stages.json', 'r') as arq:
                    stages = json.loads(arq.read())
                    for stage in stages:
                        nome = stage['nome']
                        for modelo in [Stage.TIPO_NORMAL, Stage.TIPO_BATTLEFIELD, Stage.TIPO_OMEGA]:
                            # Ver se não se trata de exceções
                            if {'nome': nome, 'modelo': modelo} in STAGE_EXCECOES:
                                continue
                            
                            if not Stage.objects.filter(nome=nome, modelo=modelo).exists():
                                Stage.objects.create(nome=nome, modelo=modelo)
        
                # Ladder
                with open(f'templates/cargas_iniciais/{settings.JOGO}/{settings.UF}/ladder_inicial.json', 'r') as arq:
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
                        if Jogador.objects.filter(nick=nick_jogador).exists():
                            jogador = Jogador.objects.get(nick=nick_jogador)
                        else:
                            user = User.objects.create_user(username=username, password='12345678')
                            jogador = Jogador.objects.create(nick=nick_jogador, admin=False, user=user)
                        
                        InicioLadder.objects.create(posicao=posicao, jogador=jogador)
                        PosicaoLadder.objects.create(posicao=posicao, jogador=jogador)
                        
                if options['desafios']:
                    # Desafios
                    with open('templates/desafios.json', 'r') as arq:
                        desafios = json.loads(arq.read())
                        
                        # Teets fica como administrador responsável
                        admin = Jogador.objects.get(nick='Teets')
                        
                        # Começar as 17:00 e ir avançando 10 min por luta, em 13/04/2019
                        data_hora = datetime.datetime.now().replace(year=2019, month=4, day=13, hour=17, minute=0)
                        for desafio in desafios:
                            jogador_1 = desafio['jogador_1']
                            score_1 = desafio['score_jogador_1']
                            jogador_2 = desafio['jogador_2']
                            score_2 = desafio['score_jogador_2']
                            
                            # Ver posição atual de cada jogador para definir quem desafiou quem
                            posicao_1 = PosicaoLadder.objects.get(jogador__nick=jogador_1).posicao
                            posicao_2 = PosicaoLadder.objects.get(jogador__nick=jogador_2).posicao
                            
                            if posicao_1 > posicao_2:
                                desafiante = Jogador.objects.get(nick=jogador_1)
                                score_desafiante = score_1
                                desafiado = Jogador.objects.get(nick=jogador_2)
                                score_desafiado = score_2
                            else:
                                desafiado = Jogador.objects.get(nick=jogador_1)
                                score_desafiado = score_1
                                desafiante = Jogador.objects.get(nick=jogador_2)
                                score_desafiante = score_2
                                
                            # Adicionar desafio e depois chamar função de validar
                            desafio_ladder = DesafioLadder(desafiante=desafiante, score_desafiante=score_desafiante, desafiado=desafiado, 
                                                           score_desafiado=score_desafiado, data_hora=data_hora, desafio_coringa=False, 
                                                           adicionado_por=admin)
                            desafio_ladder.save()
                            
                            verificar_posicoes_desafiante_desafiado(desafio_ladder)
                        
                            # Alterar ladder referência
                            alterar_ladder(desafio_ladder)
                            
                            # Gravar validador
                            desafio_ladder.admin_validador = admin
                            desafio_ladder.save()
                            
                            # Passar horário
                            data_hora = data_hora + datetime.timedelta(minutes=10)
                
        except:
            raise
        