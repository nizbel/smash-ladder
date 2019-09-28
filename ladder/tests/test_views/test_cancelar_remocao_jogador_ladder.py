# -*- coding: utf-8 -*-
import datetime
import re

from django.contrib.messages.api import get_messages
from django.test.testcases import TestCase
from django.urls.base import reverse
from django.utils import timezone

from jogadores.models import Jogador
from jogadores.tests.utils_teste import criar_jogadores_teste, SENHA_TESTE
from ladder.models import DesafioLadder, \
    PosicaoLadder, RemocaoJogador
from ladder.tests.utils_teste import criar_ladder_teste, \
    criar_ladder_historico_teste, criar_desafio_ladder_simples_teste, \
    validar_desafio_ladder_teste
from ladder.utils import remover_jogador
from ladder.views import MENSAGEM_ERRO_CANCELAR_REMOCAO_INATIVIDADE, \
    MENSAGEM_SUCESSO_CANCELAR_REMOCAO_JOGADOR_LADDER
from smashLadder import settings
from smashLadder.utils import mes_ano_ant


class ViewCancelarRemocaoJogadorLadderTestCase(TestCase):
    """Testes para a view de cancelar remoção de jogador da ladder"""
    @classmethod
    def setUpTestData(cls):
        super(ViewCancelarRemocaoJogadorLadderTestCase, cls).setUpTestData()
        
        criar_jogadores_teste()
        
        cls.teets = Jogador.objects.get(nick='teets') # Admin, com desafios
        cls.saraiva = Jogador.objects.get(nick='saraiva') # Admin, sem desafios
        cls.sena = Jogador.objects.get(nick='sena') # Não-admin, com desafios
        cls.mad = Jogador.objects.get(nick='mad') # Não-admin, sem desafios
        cls.tiovsky = Jogador.objects.get(nick='tiovsky') # Não-admin, sem desafios
        
        # Criar ladders para verificar que adicionar desafio não as afeta
        criar_ladder_teste()
        
        # Preparar mês anterior para histórico
        horario_atual = timezone.localtime()
        data_atual = horario_atual.date()
        cls.mes, cls.ano = mes_ano_ant(data_atual.month, data_atual.year)
        
        criar_ladder_historico_teste(cls.ano, cls.mes)
        
        # Criar remoção por admin
        cls.remocao_admin = RemocaoJogador.objects.create(jogador=cls.sena, data=timezone.localtime() - datetime.timedelta(days=2),
                                           admin_removedor=cls.teets, posicao_jogador=3, remocao_por_inatividade=False)
        remover_jogador(cls.remocao_admin)

        # Criar remoção por inatividade
        cls.remocao_inatividade = RemocaoJogador.objects.create(jogador=cls.tiovsky, data=timezone.localtime() - datetime.timedelta(days=1),
                                           admin_removedor=cls.teets, posicao_jogador=9, remocao_por_inatividade=True)
        remover_jogador(cls.remocao_inatividade)
        
    def test_acesso_deslogado(self):
        """Testa acesso a tela de cancelar remoção sem logar"""
        response = self.client.get(reverse('ladder:cancelar_remocao_jogador_ladder', kwargs={'remocao_id': self.remocao_admin.id}))
        self.assertEqual(response.status_code, 302)
        
        url_esperada = settings.LOGIN_URL + '?next=' + reverse('ladder:cancelar_remocao_jogador_ladder', 
                                                               kwargs={'remocao_id': self.remocao_admin.id})
        self.assertRedirects(response, url_esperada)
        
    def test_acesso_logado_nao_admin(self):
        """Testa acesso a tela de cancelar remoção logado como não admin"""
        self.client.login(username=self.mad.user.username, password=SENHA_TESTE)
        response = self.client.get(reverse('ladder:cancelar_remocao_jogador_ladder', kwargs={'remocao_id': self.remocao_admin.id}))
        self.assertEqual(response.status_code, 403)
        
    def test_acesso_logado_admin_remocao_inatividade(self):
        """Testa acesso a tela de cancelar remoção por inatividade logado como admin"""
        self.client.login(username=self.teets.user.username, password=SENHA_TESTE)
        response = self.client.get(reverse('ladder:cancelar_remocao_jogador_ladder', kwargs={'remocao_id': self.remocao_inatividade.id}))
        self.assertEqual(response.status_code, 302)
        
        self.assertRedirects(response, reverse('ladder:listar_remocoes_jogador_ladder'))
        
        # Verificar mensagens
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), MENSAGEM_ERRO_CANCELAR_REMOCAO_INATIVIDADE)
        
    def test_acesso_logado_admin_remocao_admin(self):
        """Testa acesso a tela de cancelar remoção por admin logado como admin"""
        self.client.login(username=self.teets.user.username, password=SENHA_TESTE)
        response = self.client.get(reverse('ladder:cancelar_remocao_jogador_ladder', kwargs={'remocao_id': self.remocao_admin.id}))
        self.assertEqual(response.status_code, 200)
        
        self.assertIn('remocao', response.context)
        # Verificar html
        self.assertContains(response, 'Esta operação não poderá ser desfeita')
        
    def test_cancelar_remocao_sucesso(self):
        """Testa cancelar remoção de jogador com sucesso"""
        # Guardar ladder pré-cancelamento
        ladder_pre = list(PosicaoLadder.objects.all().order_by('posicao'))
        
        self.client.login(username=self.teets.user.username, password=SENHA_TESTE)
        response = self.client.post(reverse('ladder:cancelar_remocao_jogador_ladder', kwargs={'remocao_id': self.remocao_admin.id}),
                                    {'salvar': 1})
        self.assertEqual(response.status_code, 302)
        
        self.assertRedirects(response, reverse('ladder:listar_remocoes_jogador_ladder'))
        
        # Verificar mensagens
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), MENSAGEM_SUCESSO_CANCELAR_REMOCAO_JOGADOR_LADDER)
        
        # Jogador deve voltar a ladder e alterar posições
        ladder_pos = list(PosicaoLadder.objects.all().order_by('posicao'))
        
        self.assertEqual(len(ladder_pre) + 1, len(ladder_pos))
        
        # Do 1 ao 2, não há diferença
        for posicao_pre, posicao_pos in zip(ladder_pre[:2], ladder_pos[:2]):
            self.assertEqual(posicao_pre, posicao_pos)
        
        # O 3 é o jogador que retorna
        self.assertEqual(ladder_pos[2].jogador, self.sena)
        
        # Do 4 em diante
        for posicao_pre, posicao_pos in zip(ladder_pre[2:], ladder_pos[3:]):
            self.assertEqual(posicao_pre.jogador, posicao_pos.jogador)
            self.assertEqual(posicao_pre.posicao + 1, posicao_pos.posicao)
            
        # Remoção do admin deve ter sido apagada
        self.assertFalse(RemocaoJogador.objects.filter(id=self.remocao_admin.id).exists())
        
        # Remoção do tiovsky agora deve ter posicao decimo
        self.assertEqual(RemocaoJogador.objects.get(jogador=self.tiovsky).posicao_jogador, 10)
        
    def test_cancelar_remocao_desafio_posterior_sucesso(self):
        """Testa cancelar remoção com desafio de jogador que continua sendo possível"""
        # Guardar ladder pré-cancelamento
        ladder_pre = list(PosicaoLadder.objects.all().order_by('posicao'))
        
        # Gerar desafio entre o 3 e o 2
        desafio_ladder = criar_desafio_ladder_simples_teste(self.mad, self.saraiva, 1, 3, 
                                                                          timezone.localtime(), False, self.mad)
        validar_desafio_ladder_teste(desafio_ladder, self.teets)
        
        self.client.login(username=self.teets.user.username, password=SENHA_TESTE)
        response = self.client.post(reverse('ladder:cancelar_remocao_jogador_ladder', kwargs={'remocao_id': self.remocao_admin.id}),
                                    {'salvar': 1})
        self.assertEqual(response.status_code, 302)
        
        self.assertRedirects(response, reverse('ladder:listar_remocoes_jogador_ladder'))
        
        # Verificar mensagens
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), f'Remoção cancelada com sucesso')
        
        # Jogador deve voltar a ladder e alterar posições
        ladder_pos = list(PosicaoLadder.objects.all().order_by('posicao'))
        
        self.assertEqual(len(ladder_pre) + 1, len(ladder_pos))
        
        # Do 1 ao 2, não há diferença
        for posicao_pre, posicao_pos in zip(ladder_pre[:2], ladder_pos[:2]):
            self.assertEqual(posicao_pre, posicao_pos)
        
        # O 3 é o jogador que retorna
        self.assertEqual(ladder_pos[2].jogador, self.sena)
        
        # Do 4 em diante
        for posicao_pre, posicao_pos in zip(ladder_pre[2:], ladder_pos[3:]):
            self.assertEqual(posicao_pre.jogador, posicao_pos.jogador)
            self.assertEqual(posicao_pre.posicao + 1, posicao_pos.posicao)
            
        # Desafio deve ser atualizado, agora é entre o 4 e o 2
        desafio_ladder = DesafioLadder.objects.get(desafiante=self.mad)
        self.assertEqual(desafio_ladder.posicao_desafiante, 4)
        
    def test_erro_cancelar_remocao_desafio_posterior_impossivel(self):
        """Testa cancelar remoção com desafio de jogador que se torna impossível"""
        # Gerar desafio entre o 2 + LIMITE_POSICOES_DESAFIO e o 2
        jogador_limite = PosicaoLadder.objects.get(posicao=(2 + DesafioLadder.LIMITE_POSICOES_DESAFIO)).jogador
        desafio_ladder = criar_desafio_ladder_simples_teste(jogador_limite, self.saraiva, 1, 3, 
                                                                          timezone.localtime(), False, self.saraiva)
        validar_desafio_ladder_teste(desafio_ladder, self.teets)
        
        self.client.login(username=self.teets.user.username, password=SENHA_TESTE)
        response = self.client.post(reverse('ladder:cancelar_remocao_jogador_ladder', kwargs={'remocao_id': self.remocao_admin.id}),
                                    {'salvar': 1})
        self.assertEqual(response.status_code, 200)
        
        # Verificar mensagens
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
#         self.assertEqual(str(messages[0]), f'Remoção não pode ser cancelada')
        regex = re.escape(f'Desafio Ladder {desafio_ladder.id}: ') + r'.+'
        self.assertRegex(str(messages[0]), regex)
        
        self.assertTrue(RemocaoJogador.objects.filter(id=self.remocao_admin.id).exists())
