# -*- coding: utf-8 -*-
import datetime

from django.contrib.messages.api import get_messages
from django.test.testcases import TestCase
from django.urls.base import reverse
from django.utils import timezone

from jogadores.models import Jogador, Personagem
from jogadores.tests.utils_teste import criar_jogadores_teste, \
    criar_personagens_teste, criar_stage_teste, SENHA_TESTE
from ladder.models import PosicaoLadder, HistoricoLadder, RemocaoJogador, \
    CancelamentoDesafioLadder
from ladder.tests.utils_teste import criar_ladder_teste, \
    criar_ladder_historico_teste, criar_desafio_ladder_simples_teste,\
    validar_desafio_ladder_teste
from smashLadder import settings
from smashLadder.utils import mes_ano_ant
from ladder.utils import recalcular_ladder


class ViewRemoverJogadorLadderTestCase(TestCase):
    """Testes para a view de remover jogador da ladder"""
    @classmethod
    def setUpTestData(cls):
        super(ViewRemoverJogadorLadderTestCase, cls).setUpTestData()
        
        # Jogadores
        criar_jogadores_teste()
        
        cls.teets = Jogador.objects.get(nick='teets') # Admin, com desafios
        cls.saraiva = Jogador.objects.get(nick='saraiva') # Admin, sem desafios
        cls.sena = Jogador.objects.get(nick='sena') # Não-admin, com desafios
        cls.mad = Jogador.objects.get(nick='mad') # Não-admin, sem desafios
        cls.tiovsky = Jogador.objects.get(nick='tiovsky') # Não-admin, sem desafios
        
        # Personagens
        criar_personagens_teste()
        
        cls.fox = Personagem.objects.get(nome='Fox')
        cls.marth = Personagem.objects.get(nome='Marth')
        
        # Stage
        cls.stage = criar_stage_teste()
        
        # Criar ladders para verificar que adicionar desafio não as afeta
        criar_ladder_teste()
        
        # Preparar mês anterior para histórico
        cls.horario_atual = timezone.localtime()
        cls.mes, cls.ano = mes_ano_ant(cls.horario_atual.month, cls.horario_atual.year)
        
        criar_ladder_historico_teste(cls.ano, cls.mes)
        
        # Criar desafios para ladder
        cls.horario_historico = cls.horario_atual.replace(year=cls.ano, month=cls.mes)
        cls.desafio_ladder = criar_desafio_ladder_simples_teste(cls.sena, cls.teets, 3, 1, 
                                                                          cls.horario_atual.replace(day=15), False, cls.teets)
        
        cls.desafio_ladder_historico = criar_desafio_ladder_simples_teste(cls.sena, cls.teets, 3, 1, 
                                                                                    cls.horario_historico.replace(day=15), False, cls.sena)
        
    def test_acesso_deslogado(self):
        """Testa acesso a tela de remover jogador de ladder sem logar"""
        response = self.client.get(reverse('ladder:remover_jogador_ladder'))
        self.assertEqual(response.status_code, 302)
        
        url_esperada = settings.LOGIN_URL + '?next=' + reverse('ladder:remover_jogador_ladder')
        self.assertRedirects(response, url_esperada)
        
    def test_acesso_logado_nao_admin(self):
        """Testa acesso a tela de remover jogador de ladder logado como não admin"""
        self.client.login(username=self.sena.user.username, password=SENHA_TESTE)
        response = self.client.get(reverse('ladder:remover_jogador_ladder'))
        self.assertEqual(response.status_code, 403)
        
    def test_acesso_logado_admin(self):
        """Testa acesso a tela de editar desafio de ladder não validado, logado como admin"""
        self.client.login(username=self.teets.user.username, password=SENHA_TESTE)
        response = self.client.get(reverse('ladder:remover_jogador_ladder'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('form_remover_jogador', response.context)
        
    def test_remover_jogador_ladder_atual_pos_desafios(self):
        """Testa remover um jogador da ladder, na data atual sem nenhum desafio posterior"""
        # Guardar ladder antes da operação
        ladder_antes = list(PosicaoLadder.objects.all().order_by('posicao'))
        
        self.client.login(username=self.teets.user.username, password=SENHA_TESTE)
        response = self.client.post(reverse('ladder:remover_jogador_ladder'), 
                                    {'jogador': self.sena.id, 'data': datetime.datetime.now().replace(day=16)})
        self.assertEqual(response.status_code, 302)
        
        self.assertRedirects(response, reverse('ladder:detalhar_ladder_atual'))
        
        ladder_depois = list(PosicaoLadder.objects.all().order_by('posicao'))
        
        # Verifica se registro de remoção foi criado
        self.assertTrue(RemocaoJogador.objects.filter(jogador=self.sena).exists())
        
        # Compara ladder
        self.assertEqual(len(ladder_antes) - 1, len(ladder_depois))
        # Jogadores acima na ladder não são afetados
        for posicao_antes, posicao_depois in zip(ladder_antes[0:2], ladder_depois[:2]):
            self.assertEqual(posicao_antes.posicao, posicao_depois.posicao)
            self.assertEqual(posicao_antes.jogador, posicao_depois.jogador)
            
        # Jogadores abaixo sobem uma posição
        for posicao_antes, posicao_depois in zip(ladder_antes[3:], ladder_depois[2:]):
            self.assertEqual(posicao_antes.posicao-1, posicao_depois.posicao)
            self.assertEqual(posicao_antes.jogador, posicao_depois.jogador)
        
        
    def test_remover_jogador_ladder_atual_pre_desafios(self):
        """Testa erro ao remover um jogador da ladder, na data atual antes de um desafio"""
        # Validar desafio
        validar_desafio_ladder_teste(self.desafio_ladder, self.teets)
        
        ladder_antes = list(PosicaoLadder.objects.all().order_by('posicao'))
        
        self.client.login(username=self.teets.user.username, password=SENHA_TESTE)
        response = self.client.post(reverse('ladder:remover_jogador_ladder'), 
                                    {'jogador': self.sena.id, 'data': datetime.datetime.now().replace(day=10)})
        self.assertEqual(response.status_code, 200)
        
        # Verificar mensagens
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        
        # Verificar que ladder se mantém e não foi criada remoção
        ladder_depois = list(PosicaoLadder.objects.all().order_by('posicao'))
        for posicao_antes, posicao_depois in zip(ladder_antes, ladder_depois):
            self.assertEqual(posicao_antes.posicao, posicao_depois.posicao)
            self.assertEqual(posicao_antes.jogador, posicao_depois.jogador)
            
        self.assertFalse(RemocaoJogador.objects.filter(jogador=self.sena).exists())
        
    def test_remover_jogador_ladder_hist_pos_desafios(self):
        """Testa remover um jogador de ladder histórico, sem nenhum desafio posterior"""
        # Guardar ladder antes da operação
        ladder_antes = list(HistoricoLadder.objects.filter(mes=self.mes, ano=self.ano).order_by('posicao'))
        
        self.client.login(username=self.teets.user.username, password=SENHA_TESTE)
        response = self.client.post(reverse('ladder:remover_jogador_ladder'), 
                                    {'jogador': self.sena.id, 'data': datetime.datetime.now().replace(month=self.mes, year=self.ano, day=16)})
        self.assertEqual(response.status_code, 302)
        
        self.assertRedirects(response, reverse('ladder:detalhar_ladder_atual'))
        
        ladder_depois = list(HistoricoLadder.objects.filter(mes=self.mes, ano=self.ano).order_by('posicao'))
        
        # Verifica se registro de remoção foi criado
        self.assertTrue(RemocaoJogador.objects.filter(jogador=self.sena).exists())
        
        # Compara ladder
        self.assertEqual(len(ladder_antes) - 1, len(ladder_depois))
        # Jogadores acima na ladder não são afetados
        for posicao_antes, posicao_depois in zip(ladder_antes[:2], ladder_depois[:2]):
            self.assertEqual(posicao_antes.posicao, posicao_depois.posicao)
            self.assertEqual(posicao_antes.jogador, posicao_depois.jogador)
            
        # Jogadores abaixo sobem uma posição
        for posicao_antes, posicao_depois in zip(ladder_antes[3:], ladder_depois[2:]):
            self.assertEqual(posicao_antes.posicao-1, posicao_depois.posicao)
            self.assertEqual(posicao_antes.jogador, posicao_depois.jogador)
        
        # Verificar que jogador também foi removido da ladder atual
        for posicao_hist, posicao_atual in zip(ladder_depois, PosicaoLadder.objects.all().order_by('posicao')):
            self.assertEqual(posicao_hist.posicao, posicao_atual.posicao)
            self.assertEqual(posicao_hist.jogador, posicao_atual.jogador)
        
    def test_remover_jogador_ladder_hist_pre_desafios(self):
        """Testa erro ao remover um jogador de ladder histórico, antes de um desafio"""
        # Validar desafio
        validar_desafio_ladder_teste(self.desafio_ladder_historico, self.teets)
        
        # Guardar ladder antes da operação
        ladder_antes = list(HistoricoLadder.objects.filter(mes=self.mes, ano=self.ano).order_by('posicao'))
        
        self.client.login(username=self.teets.user.username, password=SENHA_TESTE)
        response = self.client.post(reverse('ladder:remover_jogador_ladder'), 
                                    {'jogador': self.sena.id, 'data': datetime.datetime.now().replace(month=self.mes, year=self.ano, day=10)})
        self.assertEqual(response.status_code, 200)
        
        # Verificar mensagens
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        
        # Verificar que ladder se mantém e não foi criada remoção
        ladder_depois = list(HistoricoLadder.objects.filter(mes=self.mes, ano=self.ano).order_by('posicao'))
        for posicao_antes, posicao_depois in zip(ladder_antes, ladder_depois):
            self.assertEqual(posicao_antes.posicao, posicao_depois.posicao)
            self.assertEqual(posicao_antes.jogador, posicao_depois.jogador)
            
        self.assertFalse(RemocaoJogador.objects.filter(jogador=self.sena).exists())
        
    def test_remover_jogador_ladder_antes_desafio_cancelado(self):
        """Testa remover jogador de ladder em data anterior a um desafio cancelado"""
        # Validar desafio
        validar_desafio_ladder_teste(self.desafio_ladder, self.teets)
        
        # Tornar desafio cancelado
        CancelamentoDesafioLadder.objects.create(desafio_ladder=self.desafio_ladder, data_hora=self.horario_atual, jogador=self.teets)
        recalcular_ladder(self.desafio_ladder)
        
        # Guardar ladder antes da operação
        ladder_antes = list(PosicaoLadder.objects.all().order_by('posicao'))
        
        self.client.login(username=self.teets.user.username, password=SENHA_TESTE)
        response = self.client.post(reverse('ladder:remover_jogador_ladder'), 
                                    {'jogador': self.sena.id, 'data': datetime.datetime.now().replace(day=10)})
        self.assertEqual(response.status_code, 302)
        
        self.assertRedirects(response, reverse('ladder:detalhar_ladder_atual'))
        
        # Verificar mensagens
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        
        ladder_depois = list(PosicaoLadder.objects.all().order_by('posicao'))
        
        # Verifica se registro de remoção foi criado
        self.assertTrue(RemocaoJogador.objects.filter(jogador=self.sena).exists())
        
        # Compara ladder
        self.assertEqual(len(ladder_antes) - 1, len(ladder_depois))
        # Jogadores acima na ladder não são afetados
        for posicao_antes, posicao_depois in zip(ladder_antes[:2], ladder_depois[:2]):
            self.assertEqual(posicao_antes.posicao, posicao_depois.posicao)
            self.assertEqual(posicao_antes.jogador, posicao_depois.jogador)
            
        # Jogadores abaixo sobem uma posição
        for posicao_antes, posicao_depois in zip(ladder_antes[3:], ladder_depois[2:]):
            self.assertEqual(posicao_antes.posicao-1, posicao_depois.posicao)
            self.assertEqual(posicao_antes.jogador, posicao_depois.jogador)
    