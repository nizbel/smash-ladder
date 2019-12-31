# -*- coding: utf-8 -*-
"""Testa utils de Seasons"""

import datetime

from django.test.testcases import TestCase
from django.urls.base import reverse
from django.utils import timezone

from jogadores.models import Jogador
from jogadores.tests.utils_teste import criar_jogadores_teste
from ladder.models import HistoricoLadder, PosicaoLadder, DesafioLadder, \
    InicioLadder
from ladder.tests.utils_teste import criar_ladder_inicial_teste, \
    criar_ladder_historico_teste, validar_desafio_ladder_teste, \
    criar_desafio_ladder_simples_teste, criar_ladder_teste, criar_season_teste
from smashLadder.management.commands.gerar_season import iniciar_lockdown, \
    encerrar_lockdown, gerar_nova_season, apagar_ladder_season_anterior, \
    guardar_dados_season_anterior
from smashLadder.utils import mes_ano_ant


class IniciarLockdownTestCase(TestCase):
    def tearDown(self):
        TestCase.tearDown(self)
        encerrar_lockdown()
        
    def testa_acesso_apos_lockdown(self):
        """Testa acesso a tela inicial durante lockdown"""
        response = self.client.get(reverse('inicio'))
        self.assertEqual(response.status_code, 200)
        iniciar_lockdown()
        response = self.client.get(reverse('inicio'))
        self.assertEqual(response.status_code, 404)

class EncerrarLockdownTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        super(EncerrarLockdownTestCase, cls).setUpTestData()
        
        iniciar_lockdown()
        
    def tearDown(self):
        TestCase.tearDown(self)
        encerrar_lockdown()
        
    def testa_acesso_apos_encerrar_lockdown(self):
        """Testa acesso a tela inicial durante lockdown"""
        response = self.client.get(reverse('inicio'))
        self.assertEqual(response.status_code, 404)
        encerrar_lockdown()
        response = self.client.get(reverse('inicio'))
        self.assertEqual(response.status_code, 200)
        
class GerarSeasonTestCase(TestCase):
    def testa_gerar_primeira_season(self):
        """Testa gerar primeira season"""
        criar_jogadores_teste()
        
        # Pegar objetos de jogador de acordo com sua posição
        jogador_pos_1 = Jogador.objects.get(nick='teets')
        jogador_pos_2 = Jogador.objects.get(nick='saraiva')
        jogador_pos_3 = Jogador.objects.get(nick='sena')
        jogador_pos_4 = Jogador.objects.get(nick='mad')
        jogador_pos_5 = Jogador.objects.get(nick='blöwer')
        jogador_pos_6 = Jogador.objects.get(nick='frodo')
        jogador_pos_7 = Jogador.objects.get(nick='dan')
        jogador_pos_8 = Jogador.objects.get(nick='phils')
        jogador_pos_9 = Jogador.objects.get(nick='rata')
        jogador_pos_10 = Jogador.objects.get(nick='tiovsky')
        
        criar_season_teste(data_inicio=timezone.localdate() - datetime.timedelta(days=30), 
                           data_fim=timezone.localdate() - datetime.timedelta(days=1))
        criar_ladder_inicial_teste()
        criar_ladder_teste()
        
        horario_atual = timezone.localtime()
        ano, mes = mes_ano_ant(horario_atual.month, horario_atual.year)
        criar_ladder_historico_teste(ano, mes)
        
        # Criar desafios
        desafio_ladder = criar_desafio_ladder_simples_teste(jogador_pos_3, jogador_pos_1, 3, 1, 
                                                                          horario_atual, False, jogador_pos_1)
        validar_desafio_ladder_teste(desafio_ladder, jogador_pos_1)
        
        
        criar_desafio_ladder_simples_teste(jogador_pos_4, jogador_pos_2, 3, 1, 
                                                                          horario_atual, False, jogador_pos_1)
        
        # Pegar situação da ladder inicial antes
        ladder_inicial_antes = list(InicioLadder.objects.all().order_by('posicao').values_list('jogador', 'posicao'))
        
        # Pegar situação da ladder atual antes
        ladder_atual_antes = list(PosicaoLadder.objects.all().order_by('posicao').values_list('jogador', 'posicao'))
        
        guardar_dados_season_anterior()
        apagar_ladder_season_anterior()
        gerar_nova_season()
        
        self.assertFalse(HistoricoLadder.objects.exists())
        
        self.assertEqual(DesafioLadder.objects.count(), 1)
        self.assertTrue(DesafioLadder.objects.filter(id=desafio_ladder.id).exists())
        
        # Validar ladder inicial e atual
        ladder_inicial_apos = list(InicioLadder.objects.all().order_by('posicao').values_list('jogador', 'posicao'))
        ladder_atual_apos = list(PosicaoLadder.objects.all().order_by('posicao').values_list('jogador', 'posicao'))
        
        self.assertEqual(len(ladder_inicial_antes), len(ladder_inicial_apos))
        for situacao_antes, situacao_apos in zip(ladder_inicial_antes, ladder_inicial_apos):
            self.assertNotEqual(situacao_antes, situacao_apos)
            
        self.assertEqual(len(ladder_atual_antes), len(ladder_atual_apos))
        for situacao_antes, situacao_apos in zip(ladder_atual_antes, ladder_atual_apos):
            self.assertNotEqual(situacao_antes, situacao_apos)
        
        