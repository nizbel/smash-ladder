import datetime

from django.contrib.messages.api import get_messages
from django.test.testcases import TestCase
from django.urls.base import reverse
from django.utils import timezone

from jogadores.models import Jogador
from jogadores.tests.utils_teste import criar_jogadores_teste, SENHA_TESTE
from ladder.models import PermissaoAumentoRange, DesafioLadder, \
    CancelamentoDesafioLadder
from ladder.tests.utils_teste import validar_desafio_ladder_teste, \
    criar_ladder_teste
from ladder.utils import recalcular_ladder
from smashLadder import settings


class ViewRemoverPermissaoAumentoRangeTestCase(TestCase):
    """Testes para a view de remover permissão de aumento de range"""
    @classmethod
    def setUpTestData(cls):
        super(ViewRemoverPermissaoAumentoRangeTestCase, cls).setUpTestData()
        criar_jogadores_teste()
        cls.jogador_2 = Jogador.objects.get(nick='sena')
        cls.admin = Jogador.objects.get(nick='teets')
        cls.jogador_8 = Jogador.objects.get(nick='phils')
        
        criar_ladder_teste()
        
    def test_acesso_deslogado(self):
        """Testa acesso a tela de remover permissão de aumento de range sem logar"""
        response = self.client.get(reverse('ladder:remover_permissao_aumento_range'))
        url_esperada = settings.LOGIN_URL + '?next=' + reverse('ladder:remover_permissao_aumento_range')
        self.assertRedirects(response, url_esperada)
        self.assertEqual(response.status_code, 302)
        
    def test_acesso_logado(self):
        """Testa acesso a tela de remover permissão de aumento de range logando sem admin"""
        self.client.login(username=self.jogador_2.user.username, password=SENHA_TESTE)
        response = self.client.get(reverse('ladder:remover_permissao_aumento_range'))
        self.assertEqual(response.status_code, 403)
    
    def test_acesso_logado_admin(self):
        """Testa acesso a tela de remover permissão de aumento de range logando como admin"""
        self.client.login(username=self.admin.user.username, password=SENHA_TESTE)
        response = self.client.get(reverse('ladder:remover_permissao_aumento_range'))
        self.assertEqual(response.status_code, 200)
        
    def test_remover_permissao_sucesso(self):
        """Testa remover uma permissão com sucesso"""
        # Gerar permissão para remoção
        permissao = PermissaoAumentoRange.objects.create(admin_permissor=self.admin, jogador=self.jogador_2, data_hora=timezone.localtime())
        
        self.client.login(username=self.admin.user.username, password=SENHA_TESTE)
        response = self.client.post(reverse('ladder:remover_permissao_aumento_range', kwargs={'permissao_id': permissao.id}),
                                    {'permissao_id': permissao.id})
        self.assertEqual(response.status_code, 200)
        
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), PermissaoAumentoRange.MENSAGEM_SUCESSO_REMOCAO_PERMISSAO)
        
        # Verificar que não há mais permissões cadastradas
        self.assertEqual(PermissaoAumentoRange.objects.all().count(), 0)
        
    def test_erro_remover_permissao_com_desafio_cadastrado(self):
        """Testa erro ao tentar remover permissão que já possui desafio cadastrado"""
        # Gerar permissão para remoção
        permissao = PermissaoAumentoRange.objects.create(admin_permissor=self.admin, jogador=self.jogador_8, data_hora=timezone.localtime())
        # Cadastrar desafio usando permissão
        desafio = DesafioLadder.objects.create(desafiante=self.jogador_8, desafiado=self.admin, data_hora=timezone.localtime(), score_desafiante=0, 
            score_desafiado=3, desafio_coringa=False, adicionado_por=self.admin)
        validar_desafio_ladder_teste(desafio, self.admin)
        
        self.client.login(username=self.admin.user.username, password=SENHA_TESTE)
        response = self.client.post(reverse('ladder:remover_permissao_aumento_range', kwargs={'permissao_id': permissao.id}),
                                    {'permissao_id': permissao.id})
        self.assertEqual(response.status_code, 200)
        
        messages = list(response.context['messages'])
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), PermissaoAumentoRange.MENSAGEM_ERRO_DESAFIO_UTILIZANDO_PERMISSAO)
        
        # Verificar que não há mais permissões cadastradas
        self.assertEqual(PermissaoAumentoRange.objects.all().count(), 1)
        
    def test_remover_permissao_com_desafio_cancelado(self):
        """Testa sucesso ao remover permissão que possui desafio cadastrado porém cancelado"""
        # Gerar permissão para remoção
        permissao = PermissaoAumentoRange.objects.create(admin_permissor=self.admin, jogador=self.jogador_8, data_hora=timezone.localtime())
        # Cadastrar desafio usando permissão
        desafio = DesafioLadder.objects.create(desafiante=self.jogador_8, desafiado=self.jogador_2, data_hora=timezone.localtime(), score_desafiante=0, 
            score_desafiado=3, desafio_coringa=False, adicionado_por=self.admin)
        validar_desafio_ladder_teste(desafio, self.admin)
        # Cancelar desafio
        CancelamentoDesafioLadder.objects.create(desafio_ladder=desafio, jogador=self.admin)
        recalcular_ladder(desafio)
        
        self.client.login(username=self.admin.user.username, password=SENHA_TESTE)
        response = self.client.post(reverse('ladder:remover_permissao_aumento_range', kwargs={'permissao_id': permissao.id}),
                                    {'permissao_id': permissao.id})
        self.assertEqual(response.status_code, 200)
        
        messages = list(response.context['messages'])
#         messages = list(response.context['messages'])
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), PermissaoAumentoRange.MENSAGEM_SUCESSO_REMOCAO_PERMISSAO)
        
        # Verificar que não há mais permissões cadastradas
        self.assertEqual(PermissaoAumentoRange.objects.all().count(), 0)
        
    def test_nao_mostrar_permissoes_com_remocao_impossivel(self):
        """Testa se tela não mostra permissões cuja remoção não seja possível, por tempo decorrido ou já utilizada"""
        # Adicionar permissão com período inválido
        permissao_passada = PermissaoAumentoRange.objects.create(admin_permissor=self.admin, jogador=self.jogador_2, data_hora=timezone.localtime() \
            - datetime.timedelta(hours=PermissaoAumentoRange.PERIODO_VALIDADE + 1))
        
        # Adicionar permissão com desafio já cadastrado
        permissao_utilizada = PermissaoAumentoRange.objects.create(admin_permissor=self.admin, jogador=self.jogador_8, data_hora=timezone.localtime())
        # Cadastrar desafio usando permissão
        desafio = DesafioLadder.objects.create(desafiante=self.jogador_8, desafiado=self.admin, data_hora=timezone.localtime(), score_desafiante=0, 
            score_desafiado=3, desafio_coringa=False, adicionado_por=self.admin)
        validar_desafio_ladder_teste(desafio, self.admin)
        
        # Adicionar permissão válida
        permissao_valida = PermissaoAumentoRange.objects.create(admin_permissor=self.admin, jogador=self.jogador_2, data_hora=timezone.localtime())
        
        self.client.login(username=self.admin.user.username, password=SENHA_TESTE)
        response = self.client.get(reverse('ladder:remover_permissao_aumento_range'))
        self.assertEqual(response.status_code, 200)
        
        # Verificar quais permissões estão sendo mostradas
        self.assertEqual(len(response.context['permissoes']), 1)
        self.assertEqual(response.context['permissoes'][0], permissao_valida)
        
        # Permitir remover apenas válida
        self.assertContains(response, reverse('ladder:remover_permissao_aumento_range', kwargs={'permissao_id': permissao_valida.id}))
        self.assertNotContains(response, reverse('ladder:remover_permissao_aumento_range', kwargs={'permissao_id': permissao_utilizada.id}))
        self.assertNotContains(response, reverse('ladder:remover_permissao_aumento_range', kwargs={'permissao_id': permissao_passada.id}))
        
        