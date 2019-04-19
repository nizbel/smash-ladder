# -*- coding: utf-8 -*-
from django.contrib.auth.models import User
from django.test.testcases import TestCase
from django.urls.base import reverse

from jogadores.models import Jogador, Personagem
from jogadores.tests.utils_teste import criar_jogadores_teste, SENHA_TESTE, \
    criar_personagens_teste, JOGADORES_TESTE
from smashLadder import settings
from ladder.tests.utils_teste import LADDER_FORMATO_TESTE


class ViewListarJogadoresTestCase(TestCase):
    """Testes para a view de listar jogadores"""
    @classmethod
    def setUpTestData(cls):
        super(ViewListarJogadoresTestCase, cls).setUpTestData()
        cls.user = User.objects.create_user('teste', 'teste@teste.com', 'teste')
        
        criar_jogadores_teste()
        
        cls.jogadores = list(Jogador.objects.all())
        
    def test_acesso_deslogado(self):
        """Testa acesso a tela de listar jogadores sem logar"""
        response = self.client.get(reverse('jogadores:listar_jogadores'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['jogadores']), len(JOGADORES_TESTE))
        self.assertEqual(response.context['jogadores'], self.jogadores)
        
    def test_acesso_logado(self):
        """Testa acesso a tela de listar jogadores logado"""
        self.client.login(username=self.user.username, password=SENHA_TESTE)
        response = self.client.get(reverse('jogadores:listar_jogadores'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['jogadores']), len(JOGADORES_TESTE))
        self.assertEqual(response.context['jogadores'], self.jogadores)
        for jogador in self.jogadores:
            self.assertContains(response, reverse('jogadores:detalhar_jogador', kwargs={'username': jogador.user.username}), 1)
            
        

class ViewDetalharJogadorTestCase(TestCase):
    """Testes para a view de detalhar jogador"""
    @classmethod
    def setUpTestData(cls):
        super(ViewDetalharJogadorTestCase, cls).setUpTestData()
        criar_jogadores_teste(['sena', 'teets'])
        
        cls.jogador_1 = Jogador.objects.get(nick='sena')
        cls.jogador_2 = Jogador.objects.get(nick='teets')
        
    def test_acesso_deslogado(self):
        """Testa acesso a tela de detalhar jogador sem logar"""
        response = self.client.get(reverse('jogadores:detalhar_jogador', kwargs={'username': self.jogador_2.user.username}))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['jogador'], self.jogador_2)
        self.assertNotContains(response, reverse('jogadores:editar_jogador', kwargs={'username': self.jogador_2.user.username}))
        
    def test_acesso_logado(self):
        """Testa acesso a tela de detalhar jogador logado"""
        self.client.login(username=self.jogador_1.user.username, password=SENHA_TESTE)
        response = self.client.get(reverse('jogadores:detalhar_jogador', kwargs={'username': self.jogador_2.user.username}))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['jogador'], self.jogador_2)
        self.assertNotContains(response, reverse('jogadores:editar_jogador', kwargs={'username': self.jogador_2.user.username}))
        
    def test_acesso_logado_proprio_usuario(self):
        """Testa acesso a tela de detalhar a si mesmo"""
        self.client.login(username=self.jogador_2.user.username, password=SENHA_TESTE)
        response = self.client.get(reverse('jogadores:detalhar_jogador', kwargs={'username': self.jogador_2.user.username}))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['jogador'], self.jogador_2)
        self.assertContains(response, reverse('jogadores:editar_jogador', kwargs={'username': self.jogador_2.user.username}), 1)
        
    def test_acesso_logado_admin(self):
        """Testa acesso a tela de detalhar outro jogador, sendo admin"""
        self.client.login(username=self.jogador_2.user.username, password=SENHA_TESTE)
        response = self.client.get(reverse('jogadores:detalhar_jogador', kwargs={'username': self.jogador_1.user.username}))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['jogador'], self.jogador_1)
        self.assertContains(response, reverse('jogadores:editar_jogador', kwargs={'username': self.jogador_1.user.username}), 1)

class ViewEditarJogadorTestCase(TestCase):
    """Testes para a view de detalhar jogador"""
    @classmethod
    def setUpTestData(cls):
        super(ViewEditarJogadorTestCase, cls).setUpTestData()
        criar_jogadores_teste(['sena', 'teets'])
        
        cls.jogador_1 = Jogador.objects.get(nick='sena')
        cls.jogador_2 = Jogador.objects.get(nick='teets')
        
        criar_personagens_teste()
        
    def test_acesso_deslogado(self):
        """Testa acesso a tela de editar jogador sem logar"""
        response = self.client.get(reverse('jogadores:editar_jogador', kwargs={'username': self.jogador_2.user.username}))
        url_esperada = settings.LOGIN_URL + '?next=' + reverse('jogadores:editar_jogador', kwargs={'username': self.jogador_2.user.username})
        self.assertRedirects(response, url_esperada)
        self.assertEqual(response.status_code, 302)
        
    def test_acesso_logado_outro_usuario(self):
        """Testa acesso a tela de editar jogador logado com outro usuário"""
        self.client.login(username=self.jogador_1.user.username, password=SENHA_TESTE)
        response = self.client.get(reverse('jogadores:editar_jogador', kwargs={'username': self.jogador_2.user.username}))
        self.assertEqual(response.status_code, 403)
        
    def test_acesso_logado_outro_usuario_admin(self):
        """Testa acesso a tela de editar jogador logado com outro usuário admin"""
        self.client.login(username=self.jogador_2.user.username, password=SENHA_TESTE)
        response = self.client.get(reverse('jogadores:editar_jogador', kwargs={'username': self.jogador_1.user.username}))
        self.assertEqual(response.status_code, 200)
        self.assertIn('form_jogador', response.context)
        self.assertEqual(response.context['jogador'], self.jogador_1)
        self.assertFalse(response.context['form_jogador'].fields['admin'].disabled)
        self.assertTrue(response.context['form_jogador'].fields['main'].disabled)
        self.assertTrue(response.context['form_jogador'].fields['nick'].disabled)
        
    def test_acesso_logado_proprio_usuario(self):
        """Testa acesso a tela de editar o próprio usuário"""
        self.client.login(username=self.jogador_1.user.username, password=SENHA_TESTE)
        response = self.client.get(reverse('jogadores:editar_jogador', kwargs={'username': self.jogador_1.user.username}))
        self.assertEqual(response.status_code, 200)
        self.assertIn('form_jogador', response.context)
        self.assertEqual(response.context['jogador'], self.jogador_1)
        self.assertTrue(response.context['form_jogador'].fields['admin'].disabled)
        self.assertFalse(response.context['form_jogador'].fields['main'].disabled)
        self.assertFalse(response.context['form_jogador'].fields['nick'].disabled)
        
    def test_acesso_logado_proprio_usuario_admin(self):
        """Testa acesso a tela de editar o próprio usuário sendo admin"""
        self.client.login(username=self.jogador_2.user.username, password=SENHA_TESTE)
        response = self.client.get(reverse('jogadores:editar_jogador', kwargs={'username': self.jogador_2.user.username}))
        self.assertEqual(response.status_code, 200)
        self.assertIn('form_jogador', response.context)
        self.assertEqual(response.context['jogador'], self.jogador_2)
        self.assertFalse(response.context['form_jogador'].fields['admin'].disabled)
        self.assertFalse(response.context['form_jogador'].fields['main'].disabled)
        self.assertFalse(response.context['form_jogador'].fields['nick'].disabled)
        
    def test_edicao_campos_proprio_usuario(self):
        """Testa edição de campos pelo próprio usuário"""
        marth = Personagem.objects.get(nome='Marth')
        self.client.login(username=self.jogador_1.user.username, password=SENHA_TESTE)
        response = self.client.post(reverse('jogadores:editar_jogador', kwargs={'username': self.jogador_1.user.username}),
                                    {'nick': 'sena2', 'main': marth.id})
        self.assertRedirects(response, reverse('jogadores:detalhar_jogador', kwargs={'username': self.jogador_1.user.username}))
        
        # Atualizar objeto
        self.jogador_1 = Jogador.objects.get(user__username=self.jogador_1.user.username)
        self.assertEqual(self.jogador_1.nick, 'sena2')
        self.assertEqual(self.jogador_1.main, marth)
        
    def test_edicao_campos_admin(self):
        """Testa edição de campos pelo admin"""
        self.client.login(username=self.jogador_2.user.username, password=SENHA_TESTE)
        response = self.client.post(reverse('jogadores:editar_jogador', kwargs={'username': self.jogador_1.user.username}),
                                    {'admin': True})
        self.assertRedirects(response, reverse('jogadores:detalhar_jogador', kwargs={'username': self.jogador_1.user.username}))
        
        # Atualizar objeto
        self.jogador_1 = Jogador.objects.get(user__username=self.jogador_1.user.username)
        self.assertEqual(self.jogador_1.admin, True)
        
    def test_edicao_campos_proprio_usuario_admin(self):
        """Testa edição de campos pelo admin"""
        marth = Personagem.objects.get(nome='Marth')
        self.client.login(username=self.jogador_2.user.username, password=SENHA_TESTE)
        response = self.client.post(reverse('jogadores:editar_jogador', kwargs={'username': self.jogador_2.user.username}),
                                    {'nick': 'teets2', 'main': marth.id, 'admin': False})
        self.assertRedirects(response, reverse('jogadores:detalhar_jogador', kwargs={'username': self.jogador_2.user.username}))
        
        # Atualizar objeto
        self.jogador_2 = Jogador.objects.get(user__username=self.jogador_2.user.username)
        self.assertEqual(self.jogador_2.admin, False)
        self.assertEqual(self.jogador_2.main, marth)
        self.assertEqual(self.jogador_2.nick, 'teets2')
