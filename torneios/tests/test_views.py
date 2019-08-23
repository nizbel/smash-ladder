# -*- coding: utf-8 -*-
import datetime

from django.contrib.auth.models import User
from django.test.testcases import TestCase
from django.urls.base import reverse
from django.utils import timezone

class ViewDetalharTorneioTestCase(TestCase):
	"""Testes para a view de detalhar torneio"""
    @classmethod
    def setUpTestData(cls):
        super(ViewDetalharTorneioTestCase, cls).setUpTestData()
		
		criar_jogadores_teste(['teets', 'sena'])
		cls.usuario_comum = Jogador.objects.get(nick='sena')
		cls.usuario_admin = Jogador.objects.get(nick='teets')
		
        cls.torneio = criar_torneio_teste()
	
	def test_acesso_deslogado(self):
		"""Testa acesso a view de detalhar torneio sem estar logado"""
		response = self.client.get(reverse('torneios:detalhar_torneio', kwargs={'torneio_id': self.torneio.id)))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['torneio'], self.torneio)
		
		# Verificar dados do torneio
		self.assertIn('dados_torneio', response.context)
		
		# Garantir que links para edição do torneio e vinculação de jogadores não esteja visível
		self.assertNotContains(response, reverse('torneios:editar_torneio', kwargs={'torneio_id': self.torneio.id)))
		self.assertNotContains(response, reverse('torneios:vincular_jogadores', kwargs={'torneio_id': self.torneio.id)))
		
	def test_acesso_logado(self):
		"""Testa acesso a view de detalhar torneio estando logado"""
		self.client.login(username=self.usuario_comum.user.username, password=SENHA_TESTE)
		response = self.client.get(reverse('torneios:detalhar_torneio', kwargs={'torneio_id': self.torneio.id)))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['torneio'], self.torneio)
		
		# Verificar dados do torneio
		self.assertIn('dados_torneio', response.context)
		
		# Garantir que links para edição do torneio e vinculação de jogadores não esteja visível
		self.assertNotContains(response, reverse('torneios:editar_torneio', kwargs={'torneio_id': self.torneio.id)))
		self.assertNotContains(response, reverse('torneios:vincular_jogadores', kwargs={'torneio_id': self.torneio.id)))
	
	def test_acesso_logado_admin(self):
		"""Testa acesso a view de detalhar torneio logado como admin"""
		self.client.login(username=self.usuario_admin.user.username, password=SENHA_TESTE)
		response = self.client.get(reverse('torneios:detalhar_torneio', kwargs={'torneio_id': self.torneio.id)))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['torneio'], self.torneio)
		
		# Verificar dados do torneio
		self.assertIn('dados_torneio', response.context)
		
		# Garantir que links para edição do torneio e vinculação de jogadores não esteja visível
		self.assertContains(response, reverse('torneios:editar_torneio', kwargs={'torneio_id': self.torneio.id)), 1)
		self.assertContains(response, reverse('torneios:vincular_jogadores', kwargs={'torneio_id': self.torneio.id)), 1)
		
	def test_mostrar_participantes(self):
		"""Testa se participantes são retornados no contexto"""
		response = self.client.get(reverse('torneios:detalhar_torneio', kwargs={'torneio_id': self.torneio.id)))
        self.assertEqual(response.status_code, 200)
		
		dados_torneio = response.context['dados_torneio'] 
        self.assertEqual(len(dados_torneio['top_3']), 3)
		for jogador_torneio in JogadorTorneio.objects.filter(posicao_final__lte=3):
			self.assertIn(jogador_torneio, dados_torneio['top_3'])
		self.assertContains(response, reverse('torneios:listar_participantes', kwargs={'torneio_id': self.torneio.id)), 1)
		
	def test_mostrar_partidas(self):
		"""Testa se partidas são retornadas no contexto"""
		response = self.client.get(reverse('torneios:detalhar_torneio', kwargs={'torneio_id': self.torneio.id)))
        self.assertEqual(response.status_code, 200)
		
		dados_torneio = response.context['dados_torneio'] 
		self.assertContains(response, reverse('torneios:listar_partidas', kwargs={'torneio_id': self.torneio.id)), 1)
		
class ViewListarTorneiosTestCase(TestCase):
	"""Testes para a view de listar torneios"""
	@classmethod
    def setUpTestData(cls):
        super(ViewDetalharTorneioTestCase, cls).setUpTestData()
		
		cls.user = User.objects.create_user('teste', 'teste@teste.com', SENHA_TESTE)
		
        cls.torneio_1 = criar_torneio_teste('Torneio 1', timezone.localtime() - datetime.timedelta(days=7))
        cls.torneio_2 = criar_torneio_teste('Torneio 2', timezone.localtime())
		
	def test_acesso_deslogado(self):
		"""Testa acesso a view de listar torneios sem estar logado"""
		response = self.client.get(reverse('torneios:listar_torneios'))
        self.assertEqual(response.status_code, 200)
		
		self.assertEqual(len(response.context['torneios']), 2)
		self.assertIn(self.torneio_1, response.context['torneios'])
		self.assertIn(self.torneio_2, response.context['torneios'])
		
	def test_acesso_logado(self):
		"""Testa acesso a view de listar torneios estando logado"""
		response = self.client.get(reverse('torneios:listar_torneios'))
        self.assertEqual(response.status_code, 200)
		
		self.assertEqual(len(response.context['torneios']), 2)
		self.assertIn(self.torneio_1, response.context['torneios'])
		self.assertIn(self.torneio_2, response.context['torneios'])

class ViewDetalharPartidaTestCase(TestCase):
	"""Testes para a view de detalhar partida"""
	@classmethod
    def setUpTestData(cls):
        super(ViewDetalharPartidaTestCase, cls).setUpTestData()
		
		cls.user = User.objects.create_user('teste', 'teste@teste.com', SENHA_TESTE)
		
        cls.torneio = criar_torneio_teste()
		
		cls.partida = Partida.objects.filter(jogador_1__nome='aceblind', jogador_2__nome='blower', round__indice=7)

	def test_acesso_deslogado(self):
		"""Testa acesso a view de detalhar partida sem estar logado"""
		response = self.client.get(reverse('torneios:detalhar_partida', kwargs={'torneio_id': self.partida.id}))
        self.assertEqual(response.status_code, 200)
		
		self.assertEqual(response.context['partida'], self.partida)
		self.assertContains(response, reverse('torneios:detalhar_jogador_torneio', kwargs={'jogador_id': partida.jogador_1.id}), 1)
		self.assertContains(response, reverse('torneios:detalhar_jogador_torneio', kwargs={'jogador_id': partida.jogador_2.id}), 1)
		
	def test_acesso_logado(self):
		"""Testa acesso a view de detalhar partida estando logado"""
		self.client.login(username=self.user.username, password=SENHA_TESTE)
		response = self.client.get(reverse('torneios:detalhar_partida', kwargs={'torneio_id': self.partida.id}))
        self.assertEqual(response.status_code, 200)
		
		self.assertEqual(response.context['partida'], self.partida)
		self.assertContains(response, reverse('torneios:detalhar_jogador_torneio', kwargs={'jogador_id': partida.jogador_1.id}), 1)
		self.assertContains(response, reverse('torneios:detalhar_jogador_torneio', kwargs={'jogador_id': partida.jogador_2.id}), 1)
		
		

class ViewListarPartidasTestCase(TestCase):
	"""Testes para a view de listar partidas"""
	@classmethod
    def setUpTestData(cls):
        super(ViewListarPartidasTestCase, cls).setUpTestData()
		
		cls.user = User.objects.create_user('teste', 'teste@teste.com', SENHA_TESTE)
		
        cls.torneio_1 = criar_torneio_teste()

	def test_acesso_deslogado(self):
		"""Testa acesso a view de listar partidas sem estar logado"""
		response = self.client.get(reverse('torneios:listar_partidas', kwargs={'torneio_id': self.torneio.id}))
        self.assertEqual(response.status_code, 200)
		
		self.assertEqual(len(response.context['torneios']), 2)
		self.assertIn(self.torneio_1, response.context['torneios'])
		self.assertIn(self.torneio_2, response.context['torneios'])
		
	def test_acesso_logado(self):
		"""Testa acesso a view de listar partidas estando logado"""
		self.client.login(username=self.user.username, password=SENHA_TESTE)
		response = self.client.get(reverse('torneios:listar_partidas', kwargs={'torneio_id': self.torneio.id}))
        self.assertEqual(response.status_code, 200)
		
		self.assertEqual(len(response.context['torneios']), 2)
		self.assertIn(self.torneio_1, response.context['torneios'])
		self.assertIn(self.torneio_2, response.context['torneios'])
		
class ViewDetalharJogadorTestCase(TestCase):
	"""Testes para a view de detalhar jogador"""
	@classmethod
    def setUpTestData(cls):
        super(ViewDetalharJogadorTestCase, cls).setUpTestData()
		
		criar_jogadores_teste(['teets', 'sena'])
		cls.usuario_comum = Jogador.objects.get(nick='sena')
		cls.usuario_admin = Jogador.objects.get(nick='teets')
		
        cls.torneio = criar_torneio_teste()
		
		cls.jogador_torneio = JogadorTorneio.objects.get(nome='sena')
		# Vincular jogador do torneio a jogador da ladder
		cls.jogador_torneio.jogador = cls.usuario_comum
		cls.jogador_torneio.save()

	def test_acesso_deslogado(self):
		"""Testa acesso a view de detalhar jogador sem estar logado"""
		response = self.client.get(reverse('torneios:detalhar_jogador_torneio', kwargs={'jogador_id': self.partida.id}))
        self.assertEqual(response.status_code, 200)
		
		self.assertEqual(response.context['jogador'], self.jogador_torneio)
		self.assertContains(response, reverse('jogadores:detalhar_jogador', kwargs={'jogador_id': self.jogador_torneio.jogador_id}), 1)
		self.assertNotContains(response, reverse('torneios:editar_jogador_torneio', kwargs={'jogador_id': self.jogador_torneio.id}), 1)
		
	def test_acesso_logado(self):
		"""Testa acesso a view de detalhar jogador estando logado"""
		self.client.login(username=self.usuario_comum.user.username, password=SENHA_TESTE)
		response = self.client.get(reverse('torneios:detalhar_partida', kwargs={'torneio_id': self.partida.id}))
        self.assertEqual(response.status_code, 200)
		
		self.assertEqual(response.context['jogador'], self.jogador_torneio)
		self.assertContains(response, reverse('jogadores:detalhar_jogador', kwargs={'jogador_id': self.jogador_torneio.jogador_id}), 1)
		self.assertNotContains(response, reverse('torneios:editar_jogador_torneio', kwargs={'jogador_id': self.jogador_torneio.id}), 1)
		
	def test_acesso_logado_admin(self):
		"""Testa acesso a view de detalhar jogador estando logado como admin"""
		self.client.login(username=self.usuario_admin.user.username, password=SENHA_TESTE)
		response = self.client.get(reverse('torneios:detalhar_partida', kwargs={'torneio_id': self.partida.id}))
        self.assertEqual(response.status_code, 200)
		
		self.assertEqual(response.context['jogador'], self.jogador_torneio)
		self.assertContains(response, reverse('jogadores:detalhar_jogador', kwargs={'jogador_id': self.jogador_torneio.jogador_id}), 1)
		self.assertContains(response, reverse('torneios:editar_jogador_torneio', kwargs={'jogador_id': self.jogador_torneio.id}), 1)
		
class ViewEditarJogadorTorneioTestCase(self):
	"""Testes para view de editar jogador do torneio"""
	@classmethod
    def setUpTestData(cls):
        super(ViewDetalharJogadorTestCase, cls).setUpTestData()
		
		criar_jogadores_teste(['teets', 'sena'])
		cls.usuario_comum = Jogador.objects.get(nick='sena')
		cls.usuario_admin = Jogador.objects.get(nick='teets')
		
        cls.torneio = criar_torneio_teste()
		
		cls.jogador_torneio = JogadorTorneio.objects.get(nome='sena')
	
	def test_acesso_deslogado(self):
		"""Testa acesso a view de editar jogador sem estar logado"""
        response = self.client.get(reverse('torneios:editar_jogador_torneio', kwargs={'jogador_id': self.jogador_torneio.id}))
        url_esperada = settings.LOGIN_URL + '?next=' + reverse('torneios:editar_jogador_torneio', kwargs={'jogador_id': self.jogador_torneio.id})
        self.assertRedirects(response, url_esperada)
        self.assertEqual(response.status_code, 302)
		
	def test_acesso_logado(self):
		"""Testa acesso a view de editar jogador estando logado"""
		self.client.login(username=self.usuario_comum.user.username, password=SENHA_TESTE)
        response = self.client.get(reverse('torneios:editar_jogador_torneio', kwargs={'jogador_id': self.jogador_torneio.id}))
        self.assertEqual(response.status_code, 403)
	
	def test_acesso_logado_admin(self):
		"""Testa acesso a view de editar jogador estando logado como admin"""
		self.client.login(username=self.usuario_admin.user.username, password=SENHA_TESTE)
        response = self.client.get(reverse('torneios:editar_jogador_torneio', kwargs={'jogador_id': self.jogador_torneio.id}))
        self.assertEqual(response.status_code, 200)
		
		self.assertIn('form_jogador_torneio', response.context)
		
	def test_vincular_a_jogador_ladder(self):
		"""Testa vincular jogador de torneio a jogador da ladder"""
		
	def test_invalidar_jogador_torneio(self):
		"""Testa invalidar jogador de torneio"""