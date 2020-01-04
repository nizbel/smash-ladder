from django.contrib.messages.api import get_messages
from django.test.testcases import TestCase
from django.urls.base import reverse
from django.utils import timezone

from jogadores.models import Jogador
from jogadores.tests.utils_teste import criar_jogadores_teste, SENHA_TESTE
from ladder.models import PermissaoAumentoRange
from smashLadder import settings
from ladder.tests.utils_teste import criar_season_teste


class ViewAddPermissaoAumentoRange(TestCase):
    """Testes para a view de adicionar permissão de aumento de range"""
    @classmethod
    def setUpTestData(cls):
        super(ViewAddPermissaoAumentoRange, cls).setUpTestData()
        criar_jogadores_teste(['sena', 'teets',])
        cls.jogador_1 = Jogador.objects.get(nick='sena')
        cls.jogador_2 = Jogador.objects.get(nick='teets')
        
        criar_season_teste()
        
    def test_acesso_deslogado(self):
        """Testa acesso a tela de adicionar permissão de aumento de range sem logar"""
        response = self.client.get(reverse('ladder:add_permissao_aumento_range'))
        url_esperada = settings.LOGIN_URL + '?next=' + reverse('ladder:add_permissao_aumento_range')
        self.assertRedirects(response, url_esperada)
        self.assertEqual(response.status_code, 302)
        
    def test_acesso_logado(self):
        """Testa acesso a tela de adicionar permissão de aumento de range logando sem admin"""
        self.client.login(username=self.jogador_1.user.username, password=SENHA_TESTE)
        response = self.client.get(reverse('ladder:add_permissao_aumento_range'))
        self.assertEqual(response.status_code, 403)
    
    def test_acesso_logado_admin(self):
        """Testa acesso a tela de adicionar permissão de aumento de range logando como admin"""
        self.client.login(username=self.jogador_2.user.username, password=SENHA_TESTE)
        response = self.client.get(reverse('ladder:add_permissao_aumento_range'))
        self.assertEqual(response.status_code, 200)
        
    def test_sucesso_adicionar_permissao_jogador(self):
        """Testa adicionar permissão com sucesso"""
        self.client.login(username=self.jogador_2.user.username, password=SENHA_TESTE)
        response = self.client.post(reverse('ladder:add_permissao_aumento_range'), {'jogador': self.jogador_1.id})
        self.assertEqual(response.status_code, 302)
        
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), PermissaoAumentoRange.MENSAGEM_SUCESSO_PERMISSAO_AUMENTO_RANGE)
        
        self.assertRedirects(response, reverse('jogadores:detalhar_jogador', kwargs={'username': self.jogador_1.user.username}))
        
        # Verificar criação de permissão
        self.assertEqual(PermissaoAumentoRange.objects.filter(admin_permissor=self.jogador_2, jogador=self.jogador_1).count(), 1)
        
    def test_erro_adicionar_permissao_admin_permitindo_si_mesmo(self):
        """Testa erro ao adicionar permissão a si mesmo"""
        self.client.login(username=self.jogador_2.user.username, password=SENHA_TESTE)
        response = self.client.post(reverse('ladder:add_permissao_aumento_range'), {'jogador': self.jogador_2.id})
        self.assertEqual(response.status_code, 200)
        
        messages = list(response.context['messages'])
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), PermissaoAumentoRange.MENSAGEM_ERRO_JOGADOR_IGUAL_ADMIN)
        
        # Verificar criação de permissão
        self.assertEqual(PermissaoAumentoRange.objects.filter(admin_permissor=self.jogador_2, jogador=self.jogador_2).count(), 0)
    
    def test_erro_adicionar_permissao_jogador_ja_possui_permissao(self):
        """Testa erro ao adicionar permissão para jogador que já possui permissão válida"""
        # Criar permissão
        PermissaoAumentoRange.objects.create(admin_permissor=self.jogador_2, jogador=self.jogador_1, data_hora=timezone.localtime())
        self.assertEqual(PermissaoAumentoRange.objects.filter(admin_permissor=self.jogador_2, jogador=self.jogador_1).count(), 1)
        
        self.client.login(username=self.jogador_2.user.username, password=SENHA_TESTE)
        response = self.client.post(reverse('ladder:add_permissao_aumento_range'), {'jogador': self.jogador_1.id})
        self.assertEqual(response.status_code, 200)
        
        messages = list(response.context['messages'])
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), PermissaoAumentoRange.MENSAGEM_ERRO_JOGADOR_JA_POSSUI_PERMISSAO_VALIDA)
        
        # Verificar criação de permissão
        self.assertEqual(PermissaoAumentoRange.objects.filter(admin_permissor=self.jogador_2, jogador=self.jogador_1).count(), 1)    
        