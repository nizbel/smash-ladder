# -*- coding: utf-8 -*-
import datetime
import json

from django.test.testcases import TestCase

from conf.conf import CHALLONGE_USER, CHALLONGE_API_KEY
from jogadores.models import Jogador
from jogadores.tests.utils_teste import criar_jogadores_teste
from torneios.models import Torneio, JogadorTorneio
from torneios.tests.utils_teste import criar_torneio_teste, \
    criar_jogadores_torneio_teste
from torneios.utils import logar_challonge, buscar_torneio_challonge, \
    gerar_torneio_challonge, buscar_jogadores_challonge, \
    gerar_jogadores_challonge, buscar_partidas_challonge, \
    gerar_partidas_challonge, \
    vincular_automaticamente_jogadores_torneio_a_ladder


class BuscarTorneioChallongeTestCase(TestCase):
    """Testes para busca de torneio no Challonge"""
    @classmethod
    def setUpTestData(cls):
        super(BuscarTorneioChallongeTestCase, cls).setUpTestData()
        
        logar_challonge()
        
    def test_buscar_torneio(self):
        """Testa se conseguiu encontrar dados de torneio com a API do Challonge"""
        dados_torneio = buscar_torneio_challonge('atevalhalla2')
        
        self.assertIn('id', dados_torneio)
        self.assertIn('started-at', dados_torneio)
        self.assertIn('name', dados_torneio)
        self.assertIn('full-challonge-url', dados_torneio)

class GerarTorneioChallongeTestCase(TestCase):
    """Testes para gerar um torneio com base nos dados do Challonge"""
    @classmethod
    def setUpTestData(cls):
        super(GerarTorneioChallongeTestCase, cls).setUpTestData()
        
        logar_challonge()
        cls.dados_torneio = buscar_torneio_challonge('atevalhalla2')
        
    def test_gerar_torneio(self):
        """Testa se foi gerado um objeto torneio com os dados da API"""
        torneio = gerar_torneio_challonge(self.dados_torneio)
        self.assertEqual(torneio.nome, self.dados_torneio['name'])
        self.assertEqual(torneio.data, self.dados_torneio['started-at'].date())
        self.assertEqual(torneio.url, self.dados_torneio['full-challonge-url'])
        self.assertEqual(torneio.id_site, self.dados_torneio['id'])
        # Admin adicionador não é preenchido agora
        self.assertFalse(hasattr(torneio, 'adicionado_por'))
        
class BuscarJogadoresTorneioChallongeTestCase(TestCase):
    """Testes para busca de jogadores de um torneio no Challonge"""
    @classmethod
    def setUpTestData(cls):
        super(BuscarJogadoresTorneioChallongeTestCase, cls).setUpTestData()
        
        logar_challonge()
        
    def test_buscar_jogadores(self):
        """Testa se conseguiu encontrar dados de jogadores com a API do Challonge"""
        dados_jogadores = buscar_jogadores_challonge('atevalhalla2')
        
        self.assertEqual(len(dados_jogadores), 32)
        for dados_jogador in dados_jogadores:
            self.assertIn('id', dados_jogador)
            self.assertIn('final-rank', dados_jogador)
            self.assertIn('name', dados_jogador)
            self.assertIn('seed', dados_jogador)

class GerarJogadoresTorneioChallongeTestCase(TestCase):
    """Testes para gerar jogadores com base nos dados do Challonge"""
    @classmethod
    def setUpTestData(cls):
        super(GerarJogadoresTorneioChallongeTestCase, cls).setUpTestData()
        
        criar_jogadores_teste(['teets'])
        cls.torneio = criar_torneio_teste()
        
        logar_challonge()
        cls.dados_jogadores = buscar_jogadores_challonge('atevalhalla2')
        
    def test_gerar_jogadores(self):
        """Testa se foram gerados objetos jogadores com os dados da API"""
        jogadores, times = gerar_jogadores_challonge(self.dados_jogadores, self.torneio)
        
        for time in times:
            self.assertTrue(hasattr(time, 'nome'))
            
        for jogador in jogadores:
            self.assertTrue(hasattr(jogador, 'nome'))
            self.assertTrue(hasattr(jogador, 'torneio'))
            self.assertTrue(hasattr(jogador, 'posicao_final'))
            self.assertTrue(hasattr(jogador, 'valido'))
            self.assertTrue(hasattr(jogador, 'id_site'))
            self.assertTrue(hasattr(jogador, 'seed'))
            # Testar se preencheu time
            if jogador.nome == 'Teets':
                self.assertEqual(jogador.time.nome, 'CdL')
            
        
class BuscarPartidasChallongeTestCase(TestCase):
    """Testes para busca de partidas de um torneio no Challonge"""
    @classmethod
    def setUpTestData(cls):
        super(BuscarPartidasChallongeTestCase, cls).setUpTestData()
        
        logar_challonge()
        
    def test_buscar_jogadores(self):
        """Testa se conseguiu encontrar dados de partidas com a API do Challonge"""
        dados_partidas = buscar_partidas_challonge('atevalhalla2')
        
        self.assertEqual(len(dados_partidas), 63)
        for dados_partida in dados_partidas:
            self.assertIn('id', dados_partida)
            self.assertIn('winner-id', dados_partida)
            self.assertIn('player1-id', dados_partida)
            self.assertIn('player2-id', dados_partida)
            self.assertIn('round', dados_partida)
            self.assertIn('scores-csv', dados_partida)
 
class GerarPartidasChallongeTestCase(TestCase):
    """Testes para gerar partidas com base nos dados do Challonge"""
    @classmethod
    def setUpTestData(cls):
        super(GerarPartidasChallongeTestCase, cls).setUpTestData()
        
        criar_jogadores_teste(['teets'])
        cls.torneio = criar_torneio_teste()
        
        logar_challonge()
        jogadores, times = gerar_jogadores_challonge(buscar_jogadores_challonge('atevalhalla2'), cls.torneio)
        for time in times:
            time.save()
        for jogador in jogadores:
            jogador.save()
        cls.dados_partidas = buscar_partidas_challonge('atevalhalla2')
        
    def test_gerar_partidas(self):
        """Testa se foram gerados objetos partidas com os dados da API"""
        partidas, rounds, vitorias_ausencia = gerar_partidas_challonge(self.dados_partidas, self.torneio)
        
        for partida in partidas:
            self.assertTrue(hasattr(partida, 'jogador_1'))
            self.assertTrue(hasattr(partida, 'jogador_2'))
            self.assertTrue(hasattr(partida, 'score_1'))
            self.assertTrue(hasattr(partida, 'score_2'))
            self.assertTrue(hasattr(partida, 'round'))
            self.assertTrue(hasattr(partida, 'ganhador'))
            
        for round_torneio in rounds:
            self.assertTrue(hasattr(round_torneio, 'torneio'))
            self.assertTrue(hasattr(round_torneio, 'indice'))
            
        for vitoria_ausencia in vitorias_ausencia:
            self.assertTrue(hasattr(vitoria_ausencia, 'partida'))

class VincularAutomaticamenteJogadorTorneioAJogadorLadder(TestCase):
    """Testes para vinculação entre jogador de torneio e jogador da ladder"""
    @classmethod
    def setUpTestData(cls):
        super(VincularAutomaticamenteJogadorTorneioAJogadorLadder, cls).setUpTestData()
        
        criar_jogadores_teste()
        # Jogadores
        cls.teets = Jogador.objects.get(nick='teets')
        cls.saraiva = Jogador.objects.get(nick='saraiva')
        cls.sena = Jogador.objects.get(nick='sena')
        cls.mad = Jogador.objects.get(nick='mad')
        cls.blower = Jogador.objects.get(nick='blöwer')
        cls.frodo = Jogador.objects.get(nick='frodo')
        cls.dan = Jogador.objects.get(nick='dan')
        cls.phils = Jogador.objects.get(nick='phils')
        cls.rata = Jogador.objects.get(nick='rata')
        cls.tiovsky = Jogador.objects.get(nick='tiovsky')
        
        cls.torneio = criar_torneio_teste()
        criar_jogadores_torneio_teste(cls.torneio)
    
    
    def test_verificar_se_vinculos_foram_gerados(self):
        vincular_automaticamente_jogadores_torneio_a_ladder(self.torneio)
        
        # Testar jogadores vinculados
        self.assertTrue(self.teets.jogadortorneio_set.count() > 0)
        self.assertFalse(self.saraiva.jogadortorneio_set.count() > 0)
        self.assertTrue(self.sena.jogadortorneio_set.count() > 0)
        self.assertTrue(self.mad.jogadortorneio_set.count() > 0)
        self.assertFalse(self.blower.jogadortorneio_set.count() > 0)
        self.assertFalse(self.frodo.jogadortorneio_set.count() > 0)
        self.assertFalse(self.dan.jogadortorneio_set.count() > 0)
        self.assertTrue(self.phils.jogadortorneio_set.count() > 0)
        self.assertFalse(self.rata.jogadortorneio_set.count() > 0)
        self.assertFalse(self.tiovsky.jogadortorneio_set.count() > 0)
        
    def test_verificar_vinculos_gerados_com_vinculos_recentes(self):
        # Vincular primeiro torneio
        vincular_automaticamente_jogadores_torneio_a_ladder(self.torneio)
        
        # Vincular blower
        JogadorTorneio.objects.filter(nome='bløwer').update(jogador=self.blower)
        
        # Gerar segundo torneio
        torneio_2 = criar_torneio_teste('Torneio 2', self.torneio.data + datetime.timedelta(days=Torneio.PERIODO_TORNEIO_RECENTE - 1),
                                        url='teste_2')
        criar_jogadores_torneio_teste(torneio_2)
        
        vincular_automaticamente_jogadores_torneio_a_ladder(torneio_2)
        
        # Testar jogadores vinculados
        self.assertEqual(self.teets.jogadortorneio_set.count(), 2)
        self.assertEqual(self.saraiva.jogadortorneio_set.count(), 0)
        self.assertEqual(self.sena.jogadortorneio_set.count(), 2)
        self.assertEqual(self.mad.jogadortorneio_set.count(), 2)
        self.assertEqual(self.blower.jogadortorneio_set.count(), 2)
        self.assertEqual(self.frodo.jogadortorneio_set.count(), 0)
        self.assertEqual(self.dan.jogadortorneio_set.count(), 0)
        self.assertEqual(self.phils.jogadortorneio_set.count(), 2)
        self.assertEqual(self.rata.jogadortorneio_set.count(), 0)
        self.assertEqual(self.tiovsky.jogadortorneio_set.count(), 0)
        
    def test_verificar_vinculos_gerados_sem_vinculos_recentes(self):
        # Vincular primeiro torneio
        vincular_automaticamente_jogadores_torneio_a_ladder(self.torneio)
        
        # Vincular blower
        JogadorTorneio.objects.filter(nome='bløwer').update(jogador=self.blower)
        
        # Outro torneio está a uma diferença maior do que é considerado recente
        torneio_2 = criar_torneio_teste('Torneio 2', self.torneio.data + datetime.timedelta(days=Torneio.PERIODO_TORNEIO_RECENTE + 1),
                                        url='teste_2')
        criar_jogadores_torneio_teste(torneio_2)
        
        vincular_automaticamente_jogadores_torneio_a_ladder(torneio_2)
        
        # Testar jogadores vinculados
        self.assertEqual(self.teets.jogadortorneio_set.count(), 2)
        self.assertEqual(self.saraiva.jogadortorneio_set.count(), 0)
        self.assertEqual(self.sena.jogadortorneio_set.count(), 2)
        self.assertEqual(self.mad.jogadortorneio_set.count(), 2)
        self.assertEqual(self.blower.jogadortorneio_set.count(), 1)
        self.assertEqual(self.frodo.jogadortorneio_set.count(), 0)
        self.assertEqual(self.dan.jogadortorneio_set.count(), 0)
        self.assertEqual(self.phils.jogadortorneio_set.count(), 2)
        self.assertEqual(self.rata.jogadortorneio_set.count(), 0)
        self.assertEqual(self.tiovsky.jogadortorneio_set.count(), 0)
    