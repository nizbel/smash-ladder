# -*- coding: utf-8 -*-
import datetime

from django.contrib.messages.api import get_messages
from django.test.testcases import TestCase
from django.urls.base import reverse
from django.utils import timezone

from jogadores.models import Jogador
from jogadores.tests.utils_teste import criar_jogadores_teste, SENHA_TESTE
from smashLadder import settings
from torneios.models import JogadorTorneio, Partida, Torneio, Time
from torneios.tests.utils_teste import criar_torneio_teste, \
    criar_jogadores_torneio_teste, criar_partidas_teste


class ViewCriarTorneioTestCase(TestCase):
    """Testes para a view de criar torneio"""
    @classmethod
    def setUpTestData(cls):
        super(ViewCriarTorneioTestCase, cls).setUpTestData()
        
        criar_jogadores_teste(['teets', 'sena'])
        cls.usuario_comum = Jogador.objects.get(nick='sena')
        cls.usuario_admin = Jogador.objects.get(nick='teets')
        
    def test_acesso_deslogado(self):
        """Testa acesso a view de criar torneio sem estar logado"""
        response = self.client.get(reverse('torneios:criar_torneio'))
        self.assertEqual(response.status_code, 302)
        
        url_esperada = settings.LOGIN_URL + '?next=' + reverse('torneios:criar_torneio')
        self.assertRedirects(response, url_esperada)
        
    def test_acesso_logado(self):
        """Testa acesso a view de criar torneio estando logado"""
        self.client.login(username=self.usuario_comum.user.username, password=SENHA_TESTE)
        response = self.client.get(reverse('torneios:criar_torneio'))
        self.assertEqual(response.status_code, 403)
    
    def test_acesso_logado_admin(self):
        """Testa acesso a view de criar torneio logado como admin"""
        self.client.login(username=self.usuario_admin.user.username, password=SENHA_TESTE)
        response = self.client.get(reverse('torneios:criar_torneio'))
        self.assertEqual(response.status_code, 200)
        
    def test_criar_torneio_sucesso(self):
        """Testa a criação de torneio com sucesso"""
        self.client.login(username=self.usuario_admin.user.username, password=SENHA_TESTE)
        response = self.client.post(reverse('torneios:criar_torneio'), {'identificador_torneio': 'atevalhalla2', 'site': Torneio.SITE_CHALLONGE_ID, 'delimitador_time': '|'})
        self.assertEqual(response.status_code, 302)
        
        torneio_criado = Torneio.objects.all()[0]
        
        self.assertRedirects(response, reverse('torneios:editar_torneio', kwargs={'torneio_id': torneio_criado.id}))
        
        # Verificar mensagens
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), Torneio.MENSAGEM_SUCESSO_CRIACAO_TORNEIO)
        
    def test_erro_criar_torneio_url_ja_utilizada(self):
        """Testa mensagem de erro ao inserir url de torneio que já foi criado"""
        # Criar torneio
        criar_torneio_teste(url=f'{Torneio.SITE_CHALLONGE_URL}atevalhalla2')
        
        self.client.login(username=self.usuario_admin.user.username, password=SENHA_TESTE)
        response = self.client.post(reverse('torneios:criar_torneio'), {'identificador_torneio': 'atevalhalla2', 'site': Torneio.SITE_CHALLONGE_ID, 'delimitador_time': '|'})
        self.assertEqual(response.status_code, 200)
        
        messages = list(response.context['messages'])
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), Torneio.MENSAGEM_ERRO_URL_TORNEIO_JA_EXISTENTE)

class ViewDetalharTorneioTestCase(TestCase):
    """Testes para a view de detalhar torneio"""
    @classmethod
    def setUpTestData(cls):
        super(ViewDetalharTorneioTestCase, cls).setUpTestData()
        
        criar_jogadores_teste(['teets', 'sena'])
        cls.usuario_comum = Jogador.objects.get(nick='sena')
        cls.usuario_admin = Jogador.objects.get(nick='teets')
        
        cls.torneio = criar_torneio_teste()
        
        criar_jogadores_torneio_teste(cls.torneio)
    
    def test_acesso_deslogado(self):
        """Testa acesso a view de detalhar torneio sem estar logado"""
        response = self.client.get(reverse('torneios:detalhar_torneio', kwargs={'torneio_id': self.torneio.id}))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['torneio'], self.torneio)
        
        # Verificar dados do torneio
        self.assertTrue(hasattr(response.context['torneio'], 'top_3'))
        
        # Garantir que links para edição do torneio e vinculação de jogadores não esteja visível
        self.assertNotContains(response, reverse('torneios:editar_torneio', kwargs={'torneio_id': self.torneio.id}))
        
    def test_acesso_logado(self):
        """Testa acesso a view de detalhar torneio estando logado"""
        self.client.login(username=self.usuario_comum.user.username, password=SENHA_TESTE)
        response = self.client.get(reverse('torneios:detalhar_torneio', kwargs={'torneio_id': self.torneio.id}))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['torneio'], self.torneio)
        
        # Verificar dados do torneio
        self.assertTrue(hasattr(response.context['torneio'], 'top_3'))
        
        # Garantir que links para edição do torneio e vinculação de jogadores não esteja visível
        self.assertNotContains(response, reverse('torneios:editar_torneio', kwargs={'torneio_id': self.torneio.id}))
    
    def test_acesso_logado_admin(self):
        """Testa acesso a view de detalhar torneio logado como admin"""
        self.client.login(username=self.usuario_admin.user.username, password=SENHA_TESTE)
        response = self.client.get(reverse('torneios:detalhar_torneio', kwargs={'torneio_id': self.torneio.id}))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['torneio'], self.torneio)
        
        # Verificar dados do torneio
        self.assertTrue(hasattr(response.context['torneio'], 'top_3'))
        
        # Garantir que links para edição do torneio e vinculação de jogadores não esteja visível
        self.assertContains(response, reverse('torneios:editar_torneio', kwargs={'torneio_id': self.torneio.id}), 1)
        
    def test_mostrar_participantes(self):
        """Testa se participantes são retornados no contexto"""
        response = self.client.get(reverse('torneios:detalhar_torneio', kwargs={'torneio_id': self.torneio.id}))
        self.assertEqual(response.status_code, 200)
        
        self.assertTrue(hasattr(response.context['torneio'], 'top_3'))
        top_3 = response.context['torneio'].top_3
        self.assertEqual(len(top_3), 3)
        for jogador_torneio in JogadorTorneio.objects.filter(posicao_final__lte=3):
            self.assertIn(jogador_torneio, top_3)
        self.assertContains(response, reverse('torneios:listar_jogadores_torneio', kwargs={'torneio_id': self.torneio.id}), 1)
        
    def test_mostrar_partidas(self):
        """Testa se partidas são retornadas no contexto"""
        response = self.client.get(reverse('torneios:detalhar_torneio', kwargs={'torneio_id': self.torneio.id}))
        self.assertEqual(response.status_code, 200)
        
        self.assertTrue(hasattr(response.context['torneio'], 'partidas'))
                        
        self.assertContains(response, reverse('torneios:listar_partidas', kwargs={'torneio_id': self.torneio.id}), 1)
        
class ViewListarTorneiosTestCase(TestCase):
    """Testes para a view de listar torneios"""
    @classmethod
    def setUpTestData(cls):
        super(ViewListarTorneiosTestCase, cls).setUpTestData()
        
        criar_jogadores_teste(['teets'])
        cls.teets = Jogador.objects.get(nick='teets')
        
        cls.torneio_1 = criar_torneio_teste('Torneio 1', timezone.localtime() - datetime.timedelta(days=7))
        cls.torneio_2 = criar_torneio_teste('Torneio 2', timezone.localtime(), url='teste_2')
        
    def test_acesso_deslogado(self):
        """Testa acesso a view de listar torneios sem estar logado"""
        response = self.client.get(reverse('torneios:listar_torneios'))
        self.assertEqual(response.status_code, 200)
        
        self.assertEqual(len(response.context['torneios']), 2)
        self.assertIn(self.torneio_1, response.context['torneios'])
        self.assertIn(self.torneio_2, response.context['torneios'])
        
    def test_acesso_logado(self):
        """Testa acesso a view de listar torneios estando logado"""
        self.client.login(username=self.teets.user.username, password=SENHA_TESTE)
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
        
        criar_jogadores_teste(['teets'])
        cls.teets = Jogador.objects.get(nick='teets')
        
        cls.torneio = criar_torneio_teste()
        
        criar_jogadores_torneio_teste(cls.torneio)
        
        criar_partidas_teste(cls.torneio)
        
        cls.partida = Partida.objects.get(jogador_1__nome='Aceblind', jogador_2__nome='bløwer', round__indice=7)

    def test_acesso_deslogado(self):
        """Testa acesso a view de detalhar partida sem estar logado"""
        response = self.client.get(reverse('torneios:detalhar_partida', kwargs={'torneio_id': self.torneio.id, 
                                                                                'partida_id': self.partida.id}))
        self.assertEqual(response.status_code, 200)
        
        self.assertEqual(response.context['partida'], self.partida)
        self.assertContains(response, reverse('torneios:detalhar_jogador_torneio', kwargs={'torneio_id': self.partida.round.torneio_id, 
                                                                                           'jogador_id': self.partida.jogador_1.id}), 1)
        self.assertContains(response, reverse('torneios:detalhar_jogador_torneio', kwargs={'torneio_id': self.partida.round.torneio_id, 
                                                                                           'jogador_id': self.partida.jogador_2.id}), 1)
        self.assertContains(response, reverse('torneios:detalhar_torneio', kwargs={'torneio_id': self.partida.round.torneio_id}), 4)
        
    def test_acesso_logado(self):
        """Testa acesso a view de detalhar partida estando logado"""
        self.client.login(username=self.teets.user.username, password=SENHA_TESTE)
        response = self.client.get(reverse('torneios:detalhar_partida', kwargs={'torneio_id': self.torneio.id, 
                                                                                'partida_id': self.partida.id}))
        self.assertEqual(response.status_code, 200)
        
        self.assertEqual(response.context['partida'], self.partida)
        self.assertContains(response, reverse('torneios:detalhar_jogador_torneio', kwargs={'torneio_id': self.partida.round.torneio_id, 
                                                                                           'jogador_id': self.partida.jogador_1.id}), 1)
        self.assertContains(response, reverse('torneios:detalhar_jogador_torneio', kwargs={'torneio_id': self.partida.round.torneio_id, 
                                                                                           'jogador_id': self.partida.jogador_2.id}), 1)
        self.assertContains(response, reverse('torneios:detalhar_torneio', kwargs={'torneio_id': self.partida.round.torneio_id}), 3)
        
        
class ViewListarPartidasTestCase(TestCase):
    """Testes para a view de listar partidas"""
    @classmethod
    def setUpTestData(cls):
        super(ViewListarPartidasTestCase, cls).setUpTestData()
        
        criar_jogadores_teste(['teets'])
        cls.teets = Jogador.objects.get(nick='teets')
        
        cls.torneio_1 = criar_torneio_teste()
        
        criar_jogadores_torneio_teste(cls.torneio_1)
        
        criar_partidas_teste(cls.torneio_1)

    def test_acesso_deslogado(self):
        """Testa acesso a view de listar partidas sem estar logado"""
        response = self.client.get(reverse('torneios:listar_partidas', kwargs={'torneio_id': self.torneio_1.id}))
        self.assertEqual(response.status_code, 200)
        
        self.assertEqual(len(response.context['partidas']), 3)
        for partida in Partida.objects.filter(round__torneio=self.torneio_1):
            self.assertIn(partida, response.context['partidas'])
        
    def test_acesso_logado(self):
        """Testa acesso a view de listar partidas estando logado"""
        self.client.login(username=self.teets.user.username, password=SENHA_TESTE)
        response = self.client.get(reverse('torneios:listar_partidas', kwargs={'torneio_id': self.torneio_1.id}))
        self.assertEqual(response.status_code, 200)
        
        self.assertEqual(len(response.context['partidas']), 3)
        for partida in Partida.objects.filter(round__torneio=self.torneio_1):
            self.assertIn(partida, response.context['partidas'])
        
class ViewDetalharJogadorTestCase(TestCase):
    """Testes para a view de detalhar jogador"""
    @classmethod
    def setUpTestData(cls):
        super(ViewDetalharJogadorTestCase, cls).setUpTestData()
        
        criar_jogadores_teste(['teets', 'sena'])
        cls.usuario_comum = Jogador.objects.get(nick='sena')
        cls.usuario_admin = Jogador.objects.get(nick='teets')
        
        cls.torneio = criar_torneio_teste()
        
        criar_jogadores_torneio_teste(cls.torneio)
        cls.jogador_torneio = JogadorTorneio.objects.get(nome='Sena')
        # Vincular jogador do torneio a jogador da ladder
        cls.jogador_torneio.jogador = cls.usuario_comum
        cls.jogador_torneio.save()

    def test_acesso_deslogado(self):
        """Testa acesso a view de detalhar jogador sem estar logado"""
        response = self.client.get(reverse('torneios:detalhar_jogador_torneio', kwargs={'torneio_id': self.torneio.id, 
                                                                                        'jogador_id': self.jogador_torneio.id}))
        self.assertEqual(response.status_code, 200)
        
        self.assertIn('partidas', response.context)
        self.assertEqual(response.context['jogador'], self.jogador_torneio)
        self.assertNotContains(response, reverse('torneios:editar_jogador_torneio', kwargs={'torneio_id': self.torneio.id, 
                                                                                            'jogador_id': self.jogador_torneio.id}))
        
    def test_acesso_logado(self):
        """Testa acesso a view de detalhar jogador estando logado"""
        self.client.login(username=self.usuario_comum.user.username, password=SENHA_TESTE)
        response = self.client.get(reverse('torneios:detalhar_jogador_torneio', kwargs={'torneio_id': self.torneio.id, 
                                                                                        'jogador_id': self.jogador_torneio.id}))
        self.assertEqual(response.status_code, 200)
        
        self.assertIn('partidas', response.context)
        self.assertEqual(response.context['jogador'], self.jogador_torneio)
        self.assertNotContains(response, reverse('torneios:editar_jogador_torneio', kwargs={'torneio_id': self.torneio.id, 
                                                                                            'jogador_id': self.jogador_torneio.id}))
        
    def test_acesso_logado_admin(self):
        """Testa acesso a view de detalhar jogador estando logado como admin"""
        self.client.login(username=self.usuario_admin.user.username, password=SENHA_TESTE)
        response = self.client.get(reverse('torneios:detalhar_jogador_torneio', kwargs={'torneio_id': self.torneio.id, 
                                                                                        'jogador_id': self.jogador_torneio.id}))
        self.assertEqual(response.status_code, 200)
        
        self.assertIn('partidas', response.context)
        self.assertEqual(response.context['jogador'], self.jogador_torneio)
        self.assertContains(response, reverse('torneios:editar_jogador_torneio', kwargs={'torneio_id': self.torneio.id, 
                                                                                         'jogador_id': self.jogador_torneio.id}), 1)
        
    def test_mostrar_link_jogador_vinculado(self):
        """Testa se mostra link para jogador da ladder vinculado"""
        # Jogador vinculado
        response = self.client.get(reverse('torneios:detalhar_jogador_torneio', kwargs={'torneio_id': self.torneio.id, 
                                                                                        'jogador_id': self.jogador_torneio.id}))
        self.assertContains(response, reverse('jogadores:detalhar_jogador', kwargs={'username': response.context['jogador'].jogador.user.username}), 1)
        
    def test_mostrar_outros_torneios(self):
        """Testa se lista outros torneios que o jogador participou"""
        # Criar outro torneio
        torneio = criar_torneio_teste(nome='teste 2', url='teste2')
        criar_jogadores_torneio_teste(torneio)
        # Vincular jogador do torneio a jogador da ladder
        jogador_torneio = JogadorTorneio.objects.get(nome='Sena', torneio=torneio)
        jogador_torneio.jogador = self.usuario_comum
        jogador_torneio.save()
        
        response = self.client.get(reverse('torneios:detalhar_jogador_torneio', kwargs={'torneio_id': self.torneio.id, 
                                                                                        'jogador_id': self.jogador_torneio.id}))
        
        self.assertEqual(len(response.context['jogador'].outros_torneios), 1)
        
class ViewEditarJogadorTorneioTestCase(TestCase):
    """Testes para view de editar jogador do torneio"""
    @classmethod
    def setUpTestData(cls):
        super(ViewEditarJogadorTorneioTestCase, cls).setUpTestData()
        
        criar_jogadores_teste(['teets', 'sena'])
        cls.usuario_comum = Jogador.objects.get(nick='sena')
        cls.usuario_admin = Jogador.objects.get(nick='teets')
        
        cls.torneio = criar_torneio_teste()
        
        criar_jogadores_torneio_teste(cls.torneio)
        cls.jogador_torneio = JogadorTorneio.objects.get(nome='Sena')
    
    def test_acesso_deslogado(self):
        """Testa acesso a view de editar jogador sem estar logado"""
        response = self.client.get(reverse('torneios:editar_jogador_torneio', kwargs={'jogador_id': self.jogador_torneio.id,
                                                                                      'torneio_id': self.torneio.id}))
        url_esperada = settings.LOGIN_URL + '?next=' + reverse('torneios:editar_jogador_torneio', 
                                                               kwargs={'jogador_id': self.jogador_torneio.id, 
                                                                       'torneio_id': self.torneio.id})
        self.assertRedirects(response, url_esperada)
        self.assertEqual(response.status_code, 302)
        
    def test_acesso_logado(self):
        """Testa acesso a view de editar jogador estando logado"""
        self.client.login(username=self.usuario_comum.user.username, password=SENHA_TESTE)
        response = self.client.get(reverse('torneios:editar_jogador_torneio', kwargs={'jogador_id': self.jogador_torneio.id, 
                                                                                      'torneio_id': self.torneio.id}))
        self.assertEqual(response.status_code, 403)
    
    def test_acesso_logado_admin(self):
        """Testa acesso a view de editar jogador estando logado como admin"""
        self.client.login(username=self.usuario_admin.user.username, password=SENHA_TESTE)
        response = self.client.get(reverse('torneios:editar_jogador_torneio', kwargs={'jogador_id': self.jogador_torneio.id, 
                                                                                      'torneio_id': self.torneio.id}))
        self.assertEqual(response.status_code, 200)
        
        self.assertIn('form_jogador', response.context)
        
    def test_vincular_a_jogador_ladder(self):
        """Testa vincular jogador de torneio a jogador da ladder"""
        self.client.login(username=self.usuario_admin.user.username, password=SENHA_TESTE)
        response = self.client.post(reverse('torneios:editar_jogador_torneio', kwargs={'jogador_id': self.jogador_torneio.id, 
                                                                                      'torneio_id': self.torneio.id}),
            {'valido': self.jogador_torneio.valido, 'time': '', 'nome': self.jogador_torneio.nome, 
             'jogador': self.usuario_comum.id})
        self.assertEqual(response.status_code, 302)
        
        self.assertRedirects(response, reverse('torneios:detalhar_jogador_torneio', kwargs={'jogador_id': self.jogador_torneio.id, 
                                                                                      'torneio_id': self.torneio.id}))
        self.assertEqual(self.usuario_comum.id, JogadorTorneio.objects.get(nome='Sena').jogador_id)
        
    def test_invalidar_jogador_torneio(self):
        """Testa invalidar jogador de torneio"""
        self.client.login(username=self.usuario_admin.user.username, password=SENHA_TESTE)
        response = self.client.post(reverse('torneios:editar_jogador_torneio', kwargs={'jogador_id': self.jogador_torneio.id, 
                                                                                      'torneio_id': self.torneio.id}),
            {'valido': False, 'time': '', 'nome': self.jogador_torneio.nome, 
             'jogador': ''})
        self.assertEqual(response.status_code, 302)
        
        self.assertRedirects(response, reverse('torneios:detalhar_jogador_torneio', kwargs={'jogador_id': self.jogador_torneio.id, 
                                                                                      'torneio_id': self.torneio.id}))
        self.assertFalse(JogadorTorneio.objects.get(nome='Sena').valido)
        
    def test_alterar_time(self):
        """Testa alterar time do jogador"""
        time = Time.objects.all()[0]
        self.client.login(username=self.usuario_admin.user.username, password=SENHA_TESTE)
        response = self.client.post(reverse('torneios:editar_jogador_torneio', kwargs={'jogador_id': self.jogador_torneio.id, 
                                                                                      'torneio_id': self.torneio.id}),
            {'valido': self.jogador_torneio.valido, 'time': time.id, 'nome': self.jogador_torneio.nome, 
             'jogador': ''})
        self.assertEqual(response.status_code, 302)
        
        self.assertRedirects(response, reverse('torneios:detalhar_jogador_torneio', kwargs={'jogador_id': self.jogador_torneio.id, 
                                                                                      'torneio_id': self.torneio.id}))
        self.assertEqual(time, JogadorTorneio.objects.get(nome='Sena').time)
                         