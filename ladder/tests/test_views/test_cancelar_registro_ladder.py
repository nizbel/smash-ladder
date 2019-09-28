# -*- coding: utf-8 -*-
import re

from django.contrib.messages.api import get_messages
from django.test.testcases import TestCase
from django.urls.base import reverse
from django.utils import timezone

from jogadores.models import Jogador
from jogadores.tests.utils_teste import criar_jogadores_teste, SENHA_TESTE
from ladder.models import CancelamentoDesafioLadder, DesafioLadder,\
    PosicaoLadder
from ladder.tests.utils_teste import criar_ladder_teste, \
    criar_ladder_historico_teste, criar_desafio_ladder_simples_teste, \
    validar_desafio_ladder_teste
from ladder.views import MENSAGEM_SUCESSO_CANCELAR_DESAFIO_LADDER
from smashLadder import settings
from smashLadder.utils import mes_ano_ant


class ViewCancelarDesafioLadderTestCase(TestCase):
    """Testes para a view de cancelar desafio para ladder"""
    @classmethod
    def setUpTestData(cls):
        super(ViewCancelarDesafioLadderTestCase, cls).setUpTestData()
        
        criar_jogadores_teste()
        
        cls.teets = Jogador.objects.get(nick='teets') # Admin, com desafios
        cls.saraiva = Jogador.objects.get(nick='saraiva') # Admin, sem desafios
        cls.sena = Jogador.objects.get(nick='sena') # Não-admin, com desafios
        cls.mad = Jogador.objects.get(nick='mad') # Não-admin, sem desafios
        
        # Criar ladders para verificar que adicionar desafio não as afeta
        criar_ladder_teste()
        
        # Preparar mês anterior para histórico
        horario_atual = timezone.localtime()
        data_atual = horario_atual.date()
        cls.mes, cls.ano = mes_ano_ant(data_atual.month, data_atual.year)
        
        criar_ladder_historico_teste(cls.ano, cls.mes)
        
        # Criar desafios para ladder
        horario_historico = horario_atual.replace(year=cls.ano, month=cls.mes)
        cls.desafio_ladder = criar_desafio_ladder_simples_teste(cls.sena, cls.teets, 3, 1, 
                                                                          horario_atual.replace(day=10), False, cls.sena)
        cls.desafio_ladder_volta = criar_desafio_ladder_simples_teste(cls.teets, cls.sena, 3, 1, 
                                                                          horario_atual.replace(day=20), False, cls.sena)
        
        cls.desafio_ladder_historico = criar_desafio_ladder_simples_teste(cls.sena, cls.teets, 3, 1, 
                                                                                    horario_historico, False, cls.sena)
        
    def test_acesso_deslogado(self):
        """Testa acesso a tela de cancelar desafio de ladder sem logar"""
        response = self.client.get(reverse('ladder:cancelar_desafio_ladder', kwargs={'desafio_id': self.desafio_ladder.id}))
        self.assertEqual(response.status_code, 302)
        
        url_esperada = settings.LOGIN_URL + '?next=' + reverse('ladder:cancelar_desafio_ladder', 
                                                               kwargs={'desafio_id': self.desafio_ladder.id})
        self.assertRedirects(response, url_esperada)
        
    def test_acesso_logado_criador_desafio_nao_validado(self):
        """Testa acesso a tela de cancelar desafio de ladder logado como criador do desafio não validado"""
        self.client.login(username=self.sena.user.username, password=SENHA_TESTE)
        response = self.client.get(reverse('ladder:cancelar_desafio_ladder', kwargs={'desafio_id': self.desafio_ladder.id}))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['desafio_ladder'], self.desafio_ladder)
        
        # Verificar html
        self.assertContains(response, 'Esta operação não poderá ser desfeita')
        
    def test_acesso_logado_terceiro_desafio_nao_validado(self):
        """Testa acesso a tela de cancelar desafio de ladder logado como não criador do desafio não validado"""
        self.client.login(username=self.mad.user.username, password=SENHA_TESTE)
        response = self.client.get(reverse('ladder:cancelar_desafio_ladder', kwargs={'desafio_id': self.desafio_ladder.id}))
        self.assertEqual(response.status_code, 403)
        
    def test_acesso_logado_criador_desafio_validado(self):
        """Testa acesso a tela de cancelar desafio de ladder logado como criador do desafio validado"""
        # Definir desafio como validado
        self.desafio_ladder.admin_validador = self.teets
        self.desafio_ladder.save()
        
        self.client.login(username=self.sena.user.username, password=SENHA_TESTE)
        response = self.client.get(reverse('ladder:cancelar_desafio_ladder', kwargs={'desafio_id': self.desafio_ladder.id}))
        self.assertEqual(response.status_code, 403)
        
    def test_acesso_logado_terceiro_desafio_validado(self):
        """Testa acesso a tela de cancelar desafio de ladder logado como não criador do desafio validado"""
        # Definir desafio como validado
        self.desafio_ladder.admin_validador = self.teets
        self.desafio_ladder.save()
        
        self.client.login(username=self.mad.user.username, password=SENHA_TESTE)
        response = self.client.get(reverse('ladder:cancelar_desafio_ladder', kwargs={'desafio_id': self.desafio_ladder.id}))
        self.assertEqual(response.status_code, 403)
        
    def test_acesso_logado_admin_desafio_nao_validado(self):
        """Testa acesso a tela de cancelar desafio de ladder não validado, logado como admin"""
        self.client.login(username=self.teets.user.username, password=SENHA_TESTE)
        response = self.client.get(reverse('ladder:cancelar_desafio_ladder', kwargs={'desafio_id': self.desafio_ladder.id}))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['desafio_ladder'], self.desafio_ladder)
        
        # Verificar html
        self.assertContains(response, 'Esta operação não poderá ser desfeita')
        
    def test_acesso_logado_admin_desafio_validado(self):
        """Testa acesso a tela de cancelar desafio de ladder validado, logado como admin"""
        # Definir desafio como validado
        self.desafio_ladder.admin_validador = self.teets
        self.desafio_ladder.save()
        
        """Testa acesso a tela de adicionar desafio de ladder logado como admin"""
        self.client.login(username=self.teets.user.username, password=SENHA_TESTE)
        response = self.client.get(reverse('ladder:cancelar_desafio_ladder', kwargs={'desafio_id': self.desafio_ladder.id}))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['desafio_ladder'], self.desafio_ladder)
        
        # Verificar html
        self.assertContains(response, 'Esta operação não poderá ser desfeita')
        
    def test_acesso_logado_desafio_cancelado(self):
        """Testa acesso a tela de cancelar desafio de ladder que já foi cancelado"""
        # Definir desafio como cancelado
        CancelamentoDesafioLadder.objects.create(desafio_ladder=self.desafio_ladder, jogador=self.teets)
        
        self.client.login(username=self.saraiva.user.username, password=SENHA_TESTE)
        response = self.client.get(reverse('ladder:cancelar_desafio_ladder', kwargs={'desafio_id': self.desafio_ladder.id}))
        self.assertEqual(response.status_code, 302)
        
        url_esperada = reverse('ladder:detalhar_desafio_ladder', kwargs={'desafio_id': self.desafio_ladder.id})
        self.assertRedirects(response, url_esperada)
        
        # Verificar mensagens
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), f'Cancelamento já foi feito por {self.desafio_ladder.cancelamentodesafioladder.jogador.nick}')
        
    def test_cancelar_desafio_ja_cancelado(self):
        """Testa cancelar desafio de ladder que já foi cancelado"""
        # Definir desafio como cancelado
        CancelamentoDesafioLadder.objects.create(desafio_ladder=self.desafio_ladder, jogador=self.teets)
        
        self.client.login(username=self.saraiva.user.username, password=SENHA_TESTE)
        response = self.client.post(reverse('ladder:cancelar_desafio_ladder', kwargs={'desafio_id': self.desafio_ladder.id}),
                                    {'salvar': 1})
        self.assertEqual(response.status_code, 302)
        
        url_esperada = reverse('ladder:detalhar_desafio_ladder', kwargs={'desafio_id': self.desafio_ladder.id})
        self.assertRedirects(response, url_esperada)
        
        # Verificar mensagens
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), f'Cancelamento já foi feito por {self.desafio_ladder.cancelamentodesafioladder.jogador.nick}')
        
    def test_cancelar_desafio_nao_validado_atual_sucesso(self):
        """Testa cancelar desafio de ladder atual não validado com sucesso"""
        # Garantir que desafio de ladder não está cancelado
        self.assertTrue(DesafioLadder.objects.filter(id=self.desafio_ladder.id, 
                                                      cancelamentodesafioladder__isnull=True).exists())
        
        self.client.login(username=self.sena.user.username, password=SENHA_TESTE)
        response = self.client.post(reverse('ladder:cancelar_desafio_ladder', kwargs={'desafio_id': self.desafio_ladder.id}),
                                    {'salvar': 1})
        self.assertEqual(response.status_code, 302)
        
        url_esperada = reverse('ladder:detalhar_desafio_ladder', kwargs={'desafio_id': self.desafio_ladder.id})
        self.assertRedirects(response, url_esperada)
        
        # Garantir que desafio de ladder está cancelado
        self.assertTrue(DesafioLadder.objects.filter(id=self.desafio_ladder.id, 
                                                      cancelamentodesafioladder__isnull=False).exists())
        
        # Verificar mensagens
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), MENSAGEM_SUCESSO_CANCELAR_DESAFIO_LADDER)
        
    def test_cancelar_desafio_nao_validado_historico_sucesso(self):
        """Testa cancelar desafio de ladder histórico não validado com sucesso"""
        # Garantir que desafio de ladder não está cancelado
        self.assertTrue(DesafioLadder.objects.filter(id=self.desafio_ladder_historico.id, 
                                                      cancelamentodesafioladder__isnull=True).exists())
        
        self.client.login(username=self.sena.user.username, password=SENHA_TESTE)
        response = self.client.post(reverse('ladder:cancelar_desafio_ladder', kwargs={'desafio_id': self.desafio_ladder_historico.id}),
                                    {'salvar': 1})
        self.assertEqual(response.status_code, 302)
        
        url_esperada = reverse('ladder:detalhar_desafio_ladder', kwargs={'desafio_id': self.desafio_ladder_historico.id})
        self.assertRedirects(response, url_esperada)
        
        # Garantir que desafio de ladder está cancelado
        self.assertTrue(DesafioLadder.objects.filter(id=self.desafio_ladder_historico.id, 
                                                      cancelamentodesafioladder__isnull=False).exists())
        
        # Verificar mensagens
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), MENSAGEM_SUCESSO_CANCELAR_DESAFIO_LADDER)
        
    def test_cancelar_desafio_validado_atual_sucesso(self):
        """Testa cancelar desafio de ladder atual validado com sucesso"""
        # Guardar ladder original pré-validação
        ladder_pre = list(PosicaoLadder.objects.all().order_by('posicao'))
        
        # Definir desafio como validado
        validar_desafio_ladder_teste(self.desafio_ladder, self.teets)
        
        self.client.login(username=self.teets.user.username, password=SENHA_TESTE)
        response = self.client.post(reverse('ladder:cancelar_desafio_ladder', kwargs={'desafio_id': self.desafio_ladder.id}),
                                    {'salvar': 1})
        self.assertEqual(response.status_code, 302)
        
        url_esperada = reverse('ladder:detalhar_desafio_ladder', kwargs={'desafio_id': self.desafio_ladder.id})
        self.assertRedirects(response, url_esperada)
        
        # Garantir que desafio de ladder está cancelado
        self.assertTrue(DesafioLadder.objects.filter(id=self.desafio_ladder.id, 
                                                      cancelamentodesafioladder__isnull=False).exists())
        
        # Verificar mensagens
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), MENSAGEM_SUCESSO_CANCELAR_DESAFIO_LADDER)
        
        # Ladder deve voltar a posição original
        ladder_pos = list(PosicaoLadder.objects.all().order_by('posicao'))
        
        for posicao_pre, posicao_pos in zip(ladder_pre, ladder_pos):
            self.assertEqual(posicao_pre, posicao_pos)
        
        
    def test_cancelar_desafio_validado_historico_sucesso(self):
        """Testa cancelar desafio de ladder histórico validado com sucesso"""
        # Definir desafio como validado
        self.desafio_ladder_historico.admin_validador = self.teets
        self.desafio_ladder_historico.save()
        
        self.client.login(username=self.teets.user.username, password=SENHA_TESTE)
        response = self.client.post(reverse('ladder:cancelar_desafio_ladder', kwargs={'desafio_id': self.desafio_ladder_historico.id}),
                                    {'salvar': 1})
        self.assertEqual(response.status_code, 302)
        
        url_esperada = reverse('ladder:detalhar_desafio_ladder', kwargs={'desafio_id': self.desafio_ladder_historico.id})
        self.assertRedirects(response, url_esperada)
        
        # Garantir que desafio de ladder está cancelado
        self.assertTrue(DesafioLadder.objects.filter(id=self.desafio_ladder_historico.id, 
                                                      cancelamentodesafioladder__isnull=False).exists())
        
        # Verificar mensagens
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), MENSAGEM_SUCESSO_CANCELAR_DESAFIO_LADDER)
        
    def test_cancelar_desafio_validado_com_unico_uso_coringa_sucesso(self):
        """Testa cancelar desafio de ladder com desafiante que só usou um coringa, com sucesso"""
        # Definir desafio como validado e desafio coringa
        self.desafio_ladder.admin_validador = self.teets
        self.desafio_ladder.desafio_coringa = True
        self.desafio_ladder.save()
        
        # Marcar data de último uso de coringa
        self.desafio_ladder.desafiante.ultimo_uso_coringa = self.desafio_ladder.data_hora.date()
        self.desafio_ladder.desafiante.save()
        
        # Garantir que último uso não é nulo
        self.assertNotEqual(Jogador.objects.get(id=self.desafio_ladder.desafiante.id).ultimo_uso_coringa, None)
        
        self.client.login(username=self.teets.user.username, password=SENHA_TESTE)
        response = self.client.post(reverse('ladder:cancelar_desafio_ladder', kwargs={'desafio_id': self.desafio_ladder.id}),
                                    {'salvar': 1})
        self.assertEqual(response.status_code, 302)
        
        url_esperada = reverse('ladder:detalhar_desafio_ladder', kwargs={'desafio_id': self.desafio_ladder.id})
        self.assertRedirects(response, url_esperada)
        
        # Garantir que desafio de ladder está cancelado
        self.assertTrue(DesafioLadder.objects.filter(id=self.desafio_ladder.id, 
                                                      cancelamentodesafioladder__isnull=False).exists())
        
        # Garantir que último uso é nulo
        self.assertEqual(Jogador.objects.get(id=self.desafio_ladder.desafiante.id).ultimo_uso_coringa, None)
        
        # Verificar mensagens
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), MENSAGEM_SUCESSO_CANCELAR_DESAFIO_LADDER)
        
    def test_cancelar_desafio_validado_com_multi_uso_coringa_sucesso(self):
        """Testa cancelar desafio de ladder com desafiante que já usou coringas, com sucesso"""
        # Definir desafio como validado e desafio coringa
        self.desafio_ladder.admin_validador = self.teets
        self.desafio_ladder.desafio_coringa = True
        self.desafio_ladder.save()
        
        # Definir desafio de histórico como validado para servir como utilização anterior de coringa
        self.desafio_ladder_historico.admin_validador = self.teets
        self.desafio_ladder_historico.desafio_coringa = True
        self.desafio_ladder_historico.save()
        
        # Marcar data de último uso de coringa
        self.desafio_ladder.desafiante.ultimo_uso_coringa = self.desafio_ladder.data_hora.date()
        self.desafio_ladder.desafiante.save()
        
        # Garantir que último uso não é nulo
        self.assertEqual(Jogador.objects.get(id=self.desafio_ladder.desafiante.id).ultimo_uso_coringa, 
                         self.desafio_ladder.data_hora.date())
        
        self.client.login(username=self.teets.user.username, password=SENHA_TESTE)
        response = self.client.post(reverse('ladder:cancelar_desafio_ladder', 
                                            kwargs={'desafio_id': self.desafio_ladder.id}), {'salvar': 1})
        self.assertEqual(response.status_code, 302)
        
        url_esperada = reverse('ladder:detalhar_desafio_ladder', kwargs={'desafio_id': self.desafio_ladder.id})
        self.assertRedirects(response, url_esperada)
        
        # Garantir que desafio de ladder está cancelado
        self.assertTrue(DesafioLadder.objects.filter(id=self.desafio_ladder.id, 
                                                      cancelamentodesafioladder__isnull=False).exists())
        
        # Garantir que último uso é nulo
        self.assertEqual(Jogador.objects.get(id=self.desafio_ladder.desafiante.id).ultimo_uso_coringa, 
                         self.desafio_ladder_historico.data_hora.date())
        
        # Verificar mensagens
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), MENSAGEM_SUCESSO_CANCELAR_DESAFIO_LADDER)
        
    def test_cancelar_desafio_validado_erro_ladder_inconsistente(self):
        """Testa cancelar desafio de ladder validado que gera inconsistência em desafio futuro"""
        # Definir desafio como validado
        validar_desafio_ladder_teste(self.desafio_ladder, self.teets)
        validar_desafio_ladder_teste(self.desafio_ladder_volta, self.teets)
        
        self.client.login(username=self.teets.user.username, password=SENHA_TESTE)
        response = self.client.post(reverse('ladder:cancelar_desafio_ladder', kwargs={'desafio_id': self.desafio_ladder.id}),
                                    {'salvar': 1})
        self.assertEqual(response.status_code, 200)
        
        # Garantir que desafio de ladder não está cancelado
        self.assertTrue(DesafioLadder.objects.filter(id=self.desafio_ladder.id, 
                                                      cancelamentodesafioladder__isnull=True).exists())
        
        # Verificar mensagens
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        regex = re.escape(f'Desafio Ladder {self.desafio_ladder_volta.id}: ') + r'.+'
        self.assertRegex(str(messages[0]), regex)
        