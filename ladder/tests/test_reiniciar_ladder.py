# -*- coding: utf-8 -*-
import datetime

from django.contrib.auth.models import User
from django.test.testcases import TestCase
from django.utils import timezone
from ladder.tests.utils_teste import validar_desafio_ladder_teste
from ladder.models import HistoricoLadder, InicioLadder


class ReiniciarLadderTestCase(TestCase):
    """Testes para a função de reiniciar"""
    @classmethod
    def setUpTestData(cls):
        super(ReiniciarLadderTestCase, cls).setUpTestData()
        
        criar_jogadores_teste()
        
        # Pegar objetos de jogador de acordo com sua posição
        cls.jogador_pos_1 = Jogador.objects.get(nick='teets')
        cls.jogador_pos_2 = Jogador.objects.get(nick='saraiva')
        cls.jogador_pos_3 = Jogador.objects.get(nick='sena')
        cls.jogador_pos_4 = Jogador.objects.get(nick='mad')
        cls.jogador_pos_5 = Jogador.objects.get(nick='blöwer')
        cls.jogador_pos_6 = Jogador.objects.get(nick='frodo')
        cls.jogador_pos_7 = Jogador.objects.get(nick='dan')
        cls.jogador_pos_8 = Jogador.objects.get(nick='phils')
        cls.jogador_pos_9 = Jogador.objects.get(nick='rata')
        cls.jogador_pos_10 = Jogador.objects.get(nick='tiovsky')
        
        # Jogadores para validar alterações no ranking
        cls.jogadores = [cls.jogador_pos_1, cls.jogador_pos_2,
                         cls.jogador_pos_3, cls.jogador_pos_4,
                         cls.jogador_pos_5, cls.jogador_pos_6,
                         cls.jogador_pos_7]
        
        # Criar ladders para verificar que adicionar desafio não as afeta
        criar_ladder_teste()
        
        # Preparar mês anterior para histórico
        data_atual = timezone.now().date()
        cls.mes, cls.ano = mes_ano_ant(data_atual.month, data_atual.year)
        
        criar_ladder_historico_teste(cls.ano, cls.mes)
        
        # Criar novo entrante
        cls.new = criar_jogador_teste('new')
        
        # Criar outro novo entrante
        cls.new_2 = criar_jogador_teste('new_2')
        
        horario_atual = timezone.localtime()
        horario_historico = horario_atual.replace(month=cls.mes, year=cls.ano)
        
        cls.desafio_ladder = criar_desafio_ladder_simples_teste(cls.jogador_pos_3, cls.jogador_pos_1, 3, 1, 
                                                                          horario_atual, False, cls.jogador_pos_1)
        validar_desafio_ladder_teste(cls.desafio_ladder)
        
        cls.desafio_ladder_derrota = criar_desafio_ladder_simples_teste(cls.jogador_pos_7, cls.jogador_pos_6, 0, 3, 
                                                                          horario_atual + datetime.timedelta(minutes=1), False, cls.jogador_pos_1)
        validar_desafio_ladder_teste(cls.desafio_ladder_derrota)
        
        cls.desafio_ladder_historico = criar_desafio_ladder_simples_teste(cls.jogador_pos_3, cls.jogador_pos_2, 3, 1, 
                                                                          horario_historico, True, cls.jogador_pos_1)
        validar_desafio_ladder_teste(cls.desafio_ladder_historico)
        
        cls.desafio_ladder_historico_derrota = criar_desafio_ladder_simples_teste(cls.jogador_pos_6, cls.jogador_pos_5, 0, 3, 
                                                                          horario_historico + datetime.timedelta(minutes=1), True, cls.jogador_pos_1)
        validar_desafio_ladder_teste(cls.desafio_ladder_historico_derrota)
        
        
        # Desafios coringa
        cls.desafio_ladder_coringa = criar_desafio_ladder_simples_teste(cls.jogador_pos_7, cls.jogador_pos_1, 3, 1, 
                                                                          horario_atual + datetime.timedelta(minutes=2), False, cls.jogador_pos_1)
        validar_desafio_ladder_teste(cls.desafio_ladder_coringa)
        
        cls.desafio_ladder_historico_coringa = criar_desafio_ladder_simples_teste(cls.jogador_pos_6, cls.jogador_pos_2, 3, 1, 
                                                                          horario_historico + datetime.timedelta(minutes=2), True, cls.jogador_pos_1)
        validar_desafio_ladder_teste(cls.desafio_ladder_historico_coringa)
        
        
                                                                          
    def test_reiniciar(self):
        """Testa reiniciar a ladder"""
        reiniciar_ladder()
        
        # Históricos devem ter desaparecido
        self.assertFalse(HistoricoLadder.objects.all().exist())
        
        # InicioLadder mudado
        
        # PosicaoLadder deve ser igual a InicioLadder
        for posicao_inicial in InicioLadder.objects.all():
            self.assertEqual(posicao_inicial.jogador, PosicaoLadder.objects.get(posicao=posicao_inicial.posicao).jogador)
            
    def test_nao_reiniciar_em_caso_de_erro(self):
        """Manter ladder caso haja erro no reínicio"""
        # Simular erro
    
    