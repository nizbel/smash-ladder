# -*- coding: utf-8 -*-
import datetime

from django.test.testcases import TestCase
from django.utils import timezone

from jogadores.models import Jogador
from jogadores.tests.utils_teste import criar_jogadores_teste, \
    criar_personagens_teste, criar_stage_teste
from ladder.models import InicioLadder, CancelamentoDesafioLadder, \
    HistoricoLadder, PosicaoLadder, RemocaoJogador
from ladder.tests.utils_teste import criar_ladder_teste, \
    criar_ladder_historico_teste, criar_desafio_ladder_simples_teste, \
    validar_desafio_ladder_teste
from ladder.utils import remover_jogador, recalcular_ladder
from smashLadder.utils import mes_ano_ant


class JogadorTestCase(TestCase):
    """Testes para o model Jogador"""
    @classmethod
    def setUpTestData(cls):
        super(JogadorTestCase, cls).setUpTestData()
        
        criar_jogadores_teste()
        
        cls.teets = Jogador.objects.get(nick='teets')
        cls.sena = Jogador.objects.get(nick='sena')
        cls.saraiva = Jogador.objects.get(nick='saraiva')
        cls.tiovsky = Jogador.objects.get(nick='tiovsky')
        
        # Personagens
        criar_personagens_teste()
        
        # Stage
        cls.stage = criar_stage_teste()
        
        # Criar ladders para verificar que adicionar desafio não as afeta
        criar_ladder_teste()
        
        cls.horario_mes = timezone.localtime().replace(day=15)
        cls.horario_atual = cls.horario_mes + datetime.timedelta(minutes=1)
        cls.mes, cls.ano = mes_ano_ant(cls.horario_mes.month, cls.horario_mes.year)
        cls.horario_historico = cls.horario_mes.replace(year=cls.ano, month=cls.mes)
        
        criar_ladder_historico_teste(cls.ano, cls.mes)
        
        # Adicionar desafios
        cls.desafio_ladder = criar_desafio_ladder_simples_teste(cls.sena, cls.teets, 3, 1, cls.horario_mes, False, cls.teets)
        cls.desafio_ladder_historico = criar_desafio_ladder_simples_teste(cls.sena, cls.teets, 1, 3, cls.horario_historico, False, cls.teets)
        
    def test_posicao_em_jogador_sem_desafios_nem_ladder_inicial(self):
        """Testa se retorno é 0 caso jogador não esteja na ladder inicial nem possua desafios"""
        # Remover tiovsky da ladder inicial
        InicioLadder.objects.filter(jogador__nick='tiovsky').delete()
        HistoricoLadder.objects.filter(jogador__nick='tiovsky').delete()
        self.assertEqual(self.tiovsky.posicao_em(self.horario_atual), 0)
        
    def test_posicao_em_jogador_sem_desafios_com_ladder_inicial(self):
        """Testa se retorno é a posição do jogador na ladder inicial"""
        self.assertEqual(self.tiovsky.posicao_em(self.horario_atual), 10)
    
    def test_posicao_em_jogador_com_desafios_validados(self):
        """Testa se retorno é posição do jogador após o último desafio validado"""
        # Validar desafio em que sena toma posição de teets
        validar_desafio_ladder_teste(self.desafio_ladder, self.teets)
        self.assertEqual(self.sena.posicao_em(self.horario_atual), 1)
        self.assertEqual(self.teets.posicao_em(self.horario_atual), 2)
    
    def test_posicao_em_jogador_com_desafios_pendentes(self):
        """Testa se retorno desconsidera desafios pendentes"""
        self.assertEqual(self.teets.posicao_em(self.horario_atual), 1)

    def test_posicao_em_jogador_com_desafios_cancelados(self):
        """Testa se retorno desconsidera desafios cancelados"""
        # Validar desafio em que sena toma posição de teets
        validar_desafio_ladder_teste(self.desafio_ladder, self.teets)
        # Cancelar desafio
        CancelamentoDesafioLadder.objects.create(desafio_ladder=self.desafio_ladder, data_hora=self.horario_mes, jogador=self.teets)
        recalcular_ladder(self.desafio_ladder)
                                                              
        self.assertEqual(self.teets.posicao_em(self.horario_atual), 1)
    
    def test_posicao_em_jogador_com_desafios_removido_ladder(self):
        """Testa se retorno é 0 devido a remoção da ladder"""
        # Validar desafio em que sena toma posição de teets
        validar_desafio_ladder_teste(self.desafio_ladder, self.teets)
        
        # Verificar que sena está em primeiro
        self.assertEqual(self.sena.posicao_em(self.horario_atual.replace(day=16)), 1)
        
        # Remover sena
        remover_jogador(RemocaoJogador.objects.create(jogador=self.sena, data=self.horario_mes.replace(day=16), 
                                      admin_removedor=self.teets, 
                                      posicao_jogador=self.sena.posicao_em(self.horario_mes.replace(day=16))))
        
        self.assertFalse(PosicaoLadder.objects.filter(jogador=self.sena).exists())
        self.assertEqual(self.sena.posicao_em(self.horario_atual.replace(day=16)), 0)
        self.assertEqual(self.teets.posicao_em(self.horario_atual.replace(day=16)), 1)
        
    def test_posicao_em_jogador_afetado_desafios_terceiros(self):
        """Testa se retorno é 3 devido a desafio de terceiros"""
        # Validar desafio em que sena toma posição de teets
        validar_desafio_ladder_teste(self.desafio_ladder, self.teets)
        self.assertEqual(self.saraiva.posicao_em(self.horario_atual), 3)
        