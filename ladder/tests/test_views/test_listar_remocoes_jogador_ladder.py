# -*- coding: utf-8 -*-
import datetime

from django.test.testcases import TestCase
from django.urls.base import reverse
from django.utils import timezone

from jogadores.models import Jogador
from jogadores.tests.utils_teste import criar_jogadores_teste, \
    SENHA_TESTE
from ladder.models import RemocaoJogador


class ViewListarRemocoesJogadorLadderTestCase(TestCase):
    """Testes para a view de listar remoções de jogador da ladder"""
    @classmethod
    def setUpTestData(cls):
        super(ViewListarRemocoesJogadorLadderTestCase, cls).setUpTestData()
        
        # Jogadores
        criar_jogadores_teste()
        
        cls.teets = Jogador.objects.get(nick='teets') # Admin, com desafios
        cls.saraiva = Jogador.objects.get(nick='saraiva') # Admin, sem desafios
        cls.sena = Jogador.objects.get(nick='sena') # Não-admin, com desafios
        cls.mad = Jogador.objects.get(nick='mad') # Não-admin, sem desafios
        cls.tiovsky = Jogador.objects.get(nick='tiovsky') # Não-admin, sem desafios
        
        # Criar remoção por admin
        cls.remocao_admin = RemocaoJogador.objects.create(jogador=cls.mad, data=timezone.localtime() - datetime.timedelta(days=2),
                                           admin_removedor=cls.teets, posicao_jogador=4, remocao_por_inatividade=False)

        # Criar remoção por inatividade
        cls.remocao_inatividade = RemocaoJogador.objects.create(jogador=cls.tiovsky, data=timezone.localtime() - datetime.timedelta(days=1),
                                           admin_removedor=cls.teets, posicao_jogador=9, remocao_por_inatividade=True)
        
    def test_acesso_deslogado(self):
        """Testa acesso a tela de listar remoções de jogador de ladder sem logar"""
        response = self.client.get(reverse('ladder:listar_remocoes_jogador_ladder'))
        self.assertEqual(response.status_code, 200)
        
        self.assertIn('remocoes', response.context)
        self.assertNotContains(response, reverse('ladder:cancelar_remocao_jogador_ladder', kwargs={'remocao_id': self.remocao_admin.id}))
        self.assertNotContains(response, reverse('ladder:cancelar_remocao_jogador_ladder', kwargs={'remocao_id': self.remocao_inatividade.id}))
        
    def test_acesso_logado_nao_admin(self):
        """Testa acesso a tela de remover jogador de ladder logado como não admin"""
        self.client.login(username=self.sena.user.username, password=SENHA_TESTE)
        response = self.client.get(reverse('ladder:listar_remocoes_jogador_ladder'))
        self.assertEqual(response.status_code, 200)
        
        self.assertIn('remocoes', response.context)
        self.assertNotContains(response, reverse('ladder:cancelar_remocao_jogador_ladder', kwargs={'remocao_id': self.remocao_admin.id}))
        self.assertNotContains(response, reverse('ladder:cancelar_remocao_jogador_ladder', kwargs={'remocao_id': self.remocao_inatividade.id}))
        
    def test_acesso_logado_admin(self):
        """Testa acesso a tela de editar desafio de ladder não validado, logado como admin"""
        self.client.login(username=self.teets.user.username, password=SENHA_TESTE)
        response = self.client.get(reverse('ladder:listar_remocoes_jogador_ladder'))
        self.assertEqual(response.status_code, 200)
        
        self.assertIn('remocoes', response.context)
        self.assertContains(response, reverse('ladder:cancelar_remocao_jogador_ladder', kwargs={'remocao_id': self.remocao_admin.id}), 1)
        self.assertNotContains(response, reverse('ladder:cancelar_remocao_jogador_ladder', kwargs={'remocao_id': self.remocao_inatividade.id}))
        