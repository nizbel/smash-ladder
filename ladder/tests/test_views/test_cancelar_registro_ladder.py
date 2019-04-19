# -*- coding: utf-8 -*-
import re

from django.contrib.messages.api import get_messages
from django.test.testcases import TestCase
from django.urls.base import reverse
from django.utils import timezone

from jogadores.models import Jogador
from jogadores.tests.utils_teste import criar_jogadores_teste, SENHA_TESTE
from ladder.models import CancelamentoRegistroLadder, RegistroLadder
from ladder.tests.utils_teste import criar_ladder_teste, \
    criar_ladder_historico_teste, criar_registro_ladder_simples_teste, \
    validar_registro_ladder_teste
from ladder.views import MENSAGEM_SUCESSO_CANCELAR_REGISTRO_LADDER
from smashLadder import settings


class ViewCancelarRegistroLadderTestCase(TestCase):
    """Testes para a view de cancelar registro para ladder"""
    @classmethod
    def setUpTestData(cls):
        super(ViewCancelarRegistroLadderTestCase, cls).setUpTestData()
        
        criar_jogadores_teste()
        
        cls.teets = Jogador.objects.get(nick='teets') # Admin, com registros
        cls.saraiva = Jogador.objects.get(nick='saraiva') # Admin, sem registros
        cls.sena = Jogador.objects.get(nick='sena') # Não-admin, com registros
        cls.mad = Jogador.objects.get(nick='mad') # Não-admin, sem registros
        
        # Criar ladders para verificar que adicionar registro não as afeta
        criar_ladder_teste()
        
        # Preparar mês anterior para histórico
        horario_atual = timezone.now()
        data_atual = horario_atual.date()
        cls.ano = data_atual.year
        cls.mes = data_atual.month - 1
        if cls.mes == 0:
            cls.mes = 12
            cls.ano -= 1
        
        criar_ladder_historico_teste(cls.ano, cls.mes)
        
        # Criar registros para ladder
        horario_historico = horario_atual.replace(year=cls.ano, month=cls.mes)
        cls.registro_ladder = criar_registro_ladder_simples_teste(cls.sena, cls.teets, 3, 1, 
                                                                          horario_atual.replace(day=10), False, cls.sena)
        cls.registro_ladder_volta = criar_registro_ladder_simples_teste(cls.teets, cls.sena, 3, 1, 
                                                                          horario_atual.replace(day=20), False, cls.sena)
        
        cls.registro_ladder_historico = criar_registro_ladder_simples_teste(cls.sena, cls.teets, 3, 1, 
                                                                                    horario_historico, False, cls.sena)
        
    def test_acesso_deslogado(self):
        """Testa acesso a tela de cancelar registro de ladder sem logar"""
        response = self.client.get(reverse('ladder:cancelar_registro_ladder', kwargs={'registro_id': self.registro_ladder.id}))
        self.assertEqual(response.status_code, 302)
        
        url_esperada = settings.LOGIN_URL + '?next=' + reverse('ladder:cancelar_registro_ladder', 
                                                               kwargs={'registro_id': self.registro_ladder.id})
        self.assertRedirects(response, url_esperada)
        
    def test_acesso_logado_criador_registro_nao_validado(self):
        """Testa acesso a tela de cancelar registro de ladder logado como criador do registro não validado"""
        self.client.login(username=self.sena.user.username, password=SENHA_TESTE)
        response = self.client.get(reverse('ladder:cancelar_registro_ladder', kwargs={'registro_id': self.registro_ladder.id}))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['registro_ladder'], self.registro_ladder)
        
        # Verificar html
        self.assertContains(response, 'Esta operação não poderá ser desfeita')
        
    def test_acesso_logado_terceiro_registro_nao_validado(self):
        """Testa acesso a tela de cancelar registro de ladder logado como não criador do registro não validado"""
        self.client.login(username=self.mad.user.username, password=SENHA_TESTE)
        response = self.client.get(reverse('ladder:cancelar_registro_ladder', kwargs={'registro_id': self.registro_ladder.id}))
        self.assertEqual(response.status_code, 403)
        
    def test_acesso_logado_criador_registro_validado(self):
        """Testa acesso a tela de cancelar registro de ladder logado como criador do registro validado"""
        # Definir registro como validado
        self.registro_ladder.admin_validador = self.teets
        self.registro_ladder.save()
        
        self.client.login(username=self.sena.user.username, password=SENHA_TESTE)
        response = self.client.get(reverse('ladder:cancelar_registro_ladder', kwargs={'registro_id': self.registro_ladder.id}))
        self.assertEqual(response.status_code, 403)
        
    def test_acesso_logado_terceiro_registro_validado(self):
        """Testa acesso a tela de cancelar registro de ladder logado como não criador do registro validado"""
        # Definir registro como validado
        self.registro_ladder.admin_validador = self.teets
        self.registro_ladder.save()
        
        self.client.login(username=self.mad.user.username, password=SENHA_TESTE)
        response = self.client.get(reverse('ladder:cancelar_registro_ladder', kwargs={'registro_id': self.registro_ladder.id}))
        self.assertEqual(response.status_code, 403)
        
    def test_acesso_logado_admin_registro_nao_validado(self):
        """Testa acesso a tela de cancelar registro de ladder não validado, logado como admin"""
        self.client.login(username=self.teets.user.username, password=SENHA_TESTE)
        response = self.client.get(reverse('ladder:cancelar_registro_ladder', kwargs={'registro_id': self.registro_ladder.id}))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['registro_ladder'], self.registro_ladder)
        
        # Verificar html
        self.assertContains(response, 'Esta operação não poderá ser desfeita')
        
    def test_acesso_logado_admin_registro_validado(self):
        """Testa acesso a tela de cancelar registro de ladder validado, logado como admin"""
        # Definir registro como validado
        self.registro_ladder.admin_validador = self.teets
        self.registro_ladder.save()
        
        """Testa acesso a tela de adicionar registro de ladder logado como admin"""
        self.client.login(username=self.teets.user.username, password=SENHA_TESTE)
        response = self.client.get(reverse('ladder:cancelar_registro_ladder', kwargs={'registro_id': self.registro_ladder.id}))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['registro_ladder'], self.registro_ladder)
        
        # Verificar html
        self.assertContains(response, 'Esta operação não poderá ser desfeita')
        
    def test_acesso_logado_registro_cancelado(self):
        """Testa acesso a tela de cancelar registro de ladder que já foi cancelado"""
        # Definir registro como cancelado
        CancelamentoRegistroLadder.objects.create(registro_ladder=self.registro_ladder, jogador=self.teets)
        
        self.client.login(username=self.saraiva.user.username, password=SENHA_TESTE)
        response = self.client.get(reverse('ladder:cancelar_registro_ladder', kwargs={'registro_id': self.registro_ladder.id}))
        self.assertEqual(response.status_code, 302)
        
        url_esperada = reverse('ladder:detalhar_registro_ladder', kwargs={'registro_id': self.registro_ladder.id})
        self.assertRedirects(response, url_esperada)
        
        # Verificar mensagens
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), f'Cancelamento já foi feito por {self.registro_ladder.cancelamentoregistroladder.jogador.nick}')
        
    def test_cancelar_registro_ja_cancelado(self):
        """Testa cancelar registro de ladder que já foi cancelado"""
        # Definir registro como cancelado
        CancelamentoRegistroLadder.objects.create(registro_ladder=self.registro_ladder, jogador=self.teets)
        
        self.client.login(username=self.saraiva.user.username, password=SENHA_TESTE)
        response = self.client.post(reverse('ladder:cancelar_registro_ladder', kwargs={'registro_id': self.registro_ladder.id}),
                                    {'salvar': 1})
        self.assertEqual(response.status_code, 302)
        
        url_esperada = reverse('ladder:detalhar_registro_ladder', kwargs={'registro_id': self.registro_ladder.id})
        self.assertRedirects(response, url_esperada)
        
        # Verificar mensagens
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), f'Cancelamento já foi feito por {self.registro_ladder.cancelamentoregistroladder.jogador.nick}')
        
    def test_cancelar_registro_nao_validado_atual_sucesso(self):
        """Testa cancelar registro de ladder atual não validado com sucesso"""
        # Garantir que registro de ladder não está cancelado
        self.assertTrue(RegistroLadder.objects.filter(id=self.registro_ladder.id, 
                                                      cancelamentoregistroladder__isnull=True).exists())
        
        self.client.login(username=self.sena.user.username, password=SENHA_TESTE)
        response = self.client.post(reverse('ladder:cancelar_registro_ladder', kwargs={'registro_id': self.registro_ladder.id}),
                                    {'salvar': 1})
        self.assertEqual(response.status_code, 302)
        
        url_esperada = reverse('ladder:detalhar_registro_ladder', kwargs={'registro_id': self.registro_ladder.id})
        self.assertRedirects(response, url_esperada)
        
        # Garantir que registro de ladder está cancelado
        self.assertTrue(RegistroLadder.objects.filter(id=self.registro_ladder.id, 
                                                      cancelamentoregistroladder__isnull=False).exists())
        
        # Verificar mensagens
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), MENSAGEM_SUCESSO_CANCELAR_REGISTRO_LADDER)
        
    def test_cancelar_registro_nao_validado_historico_sucesso(self):
        """Testa cancelar registro de ladder histórico não validado com sucesso"""
        # Garantir que registro de ladder não está cancelado
        self.assertTrue(RegistroLadder.objects.filter(id=self.registro_ladder_historico.id, 
                                                      cancelamentoregistroladder__isnull=True).exists())
        
        self.client.login(username=self.sena.user.username, password=SENHA_TESTE)
        response = self.client.post(reverse('ladder:cancelar_registro_ladder', kwargs={'registro_id': self.registro_ladder_historico.id}),
                                    {'salvar': 1})
        self.assertEqual(response.status_code, 302)
        
        url_esperada = reverse('ladder:detalhar_registro_ladder', kwargs={'registro_id': self.registro_ladder_historico.id})
        self.assertRedirects(response, url_esperada)
        
        # Garantir que registro de ladder está cancelado
        self.assertTrue(RegistroLadder.objects.filter(id=self.registro_ladder_historico.id, 
                                                      cancelamentoregistroladder__isnull=False).exists())
        
        # Verificar mensagens
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), MENSAGEM_SUCESSO_CANCELAR_REGISTRO_LADDER)
        
    def test_cancelar_registro_validado_atual_sucesso(self):
        """Testa cancelar registro de ladder atual validado com sucesso"""
        # Definir registro como validado
        self.registro_ladder.admin_validador = self.teets
        self.registro_ladder.save()
        
        self.client.login(username=self.teets.user.username, password=SENHA_TESTE)
        response = self.client.post(reverse('ladder:cancelar_registro_ladder', kwargs={'registro_id': self.registro_ladder.id}),
                                    {'salvar': 1})
        self.assertEqual(response.status_code, 302)
        
        url_esperada = reverse('ladder:detalhar_registro_ladder', kwargs={'registro_id': self.registro_ladder.id})
        self.assertRedirects(response, url_esperada)
        
        # Garantir que registro de ladder está cancelado
        self.assertTrue(RegistroLadder.objects.filter(id=self.registro_ladder.id, 
                                                      cancelamentoregistroladder__isnull=False).exists())
        
        # Verificar mensagens
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), MENSAGEM_SUCESSO_CANCELAR_REGISTRO_LADDER)
        
    def test_cancelar_registro_validado_historico_sucesso(self):
        """Testa cancelar registro de ladder histórico validado com sucesso"""
        # Definir registro como validado
        self.registro_ladder_historico.admin_validador = self.teets
        self.registro_ladder_historico.save()
        
        self.client.login(username=self.teets.user.username, password=SENHA_TESTE)
        response = self.client.post(reverse('ladder:cancelar_registro_ladder', kwargs={'registro_id': self.registro_ladder_historico.id}),
                                    {'salvar': 1})
        self.assertEqual(response.status_code, 302)
        
        url_esperada = reverse('ladder:detalhar_registro_ladder', kwargs={'registro_id': self.registro_ladder_historico.id})
        self.assertRedirects(response, url_esperada)
        
        # Garantir que registro de ladder está cancelado
        self.assertTrue(RegistroLadder.objects.filter(id=self.registro_ladder_historico.id, 
                                                      cancelamentoregistroladder__isnull=False).exists())
        
        # Verificar mensagens
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), MENSAGEM_SUCESSO_CANCELAR_REGISTRO_LADDER)
        
    def test_cancelar_registro_validado_com_unico_uso_coringa_sucesso(self):
        """Testa cancelar registro de ladder com desafiante que só usou um coringa, com sucesso"""
        # Definir registro como validado e desafio coringa
        self.registro_ladder.admin_validador = self.teets
        self.registro_ladder.desafio_coringa = True
        self.registro_ladder.save()
        
        # Marcar data de último uso de coringa
        self.registro_ladder.desafiante.ultimo_uso_coringa = self.registro_ladder.data_hora.date()
        self.registro_ladder.desafiante.save()
        
        # Garantir que último uso não é nulo
        self.assertNotEqual(Jogador.objects.get(id=self.registro_ladder.desafiante.id).ultimo_uso_coringa, None)
        
        self.client.login(username=self.teets.user.username, password=SENHA_TESTE)
        response = self.client.post(reverse('ladder:cancelar_registro_ladder', kwargs={'registro_id': self.registro_ladder.id}),
                                    {'salvar': 1})
        self.assertEqual(response.status_code, 302)
        
        url_esperada = reverse('ladder:detalhar_registro_ladder', kwargs={'registro_id': self.registro_ladder.id})
        self.assertRedirects(response, url_esperada)
        
        # Garantir que registro de ladder está cancelado
        self.assertTrue(RegistroLadder.objects.filter(id=self.registro_ladder.id, 
                                                      cancelamentoregistroladder__isnull=False).exists())
        
        # Garantir que último uso é nulo
        self.assertEqual(Jogador.objects.get(id=self.registro_ladder.desafiante.id).ultimo_uso_coringa, None)
        
        # Verificar mensagens
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), MENSAGEM_SUCESSO_CANCELAR_REGISTRO_LADDER)
        
    def test_cancelar_registro_validado_com_multi_uso_coringa_sucesso(self):
        """Testa cancelar registro de ladder com desafiante que já usou coringas, com sucesso"""
        # Definir registro como validado e desafio coringa
        self.registro_ladder.admin_validador = self.teets
        self.registro_ladder.desafio_coringa = True
        self.registro_ladder.save()
        
        # Definir registro de histórico como validado para servir como utilização anterior de coringa
        self.registro_ladder_historico.admin_validador = self.teets
        self.registro_ladder_historico.desafio_coringa = True
        self.registro_ladder_historico.save()
        
        # Marcar data de último uso de coringa
        self.registro_ladder.desafiante.ultimo_uso_coringa = self.registro_ladder.data_hora.date()
        self.registro_ladder.desafiante.save()
        
        # Garantir que último uso não é nulo
        self.assertEqual(Jogador.objects.get(id=self.registro_ladder.desafiante.id).ultimo_uso_coringa, 
                         self.registro_ladder.data_hora.date())
        
        self.client.login(username=self.teets.user.username, password=SENHA_TESTE)
        response = self.client.post(reverse('ladder:cancelar_registro_ladder', 
                                            kwargs={'registro_id': self.registro_ladder.id}), {'salvar': 1})
        self.assertEqual(response.status_code, 302)
        
        url_esperada = reverse('ladder:detalhar_registro_ladder', kwargs={'registro_id': self.registro_ladder.id})
        self.assertRedirects(response, url_esperada)
        
        # Garantir que registro de ladder está cancelado
        self.assertTrue(RegistroLadder.objects.filter(id=self.registro_ladder.id, 
                                                      cancelamentoregistroladder__isnull=False).exists())
        
        # Garantir que último uso é nulo
        self.assertEqual(Jogador.objects.get(id=self.registro_ladder.desafiante.id).ultimo_uso_coringa, 
                         timezone.make_naive(self.registro_ladder_historico.data_hora).date())
        
        # Verificar mensagens
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), MENSAGEM_SUCESSO_CANCELAR_REGISTRO_LADDER)
        
    def test_cancelar_registro_validado_erro_ladder_inconsistente(self):
        """Testa cancelar registro de ladder validado que gera inconsistência em registro futuro"""
        # Definir registro como validado
        validar_registro_ladder_teste(self.registro_ladder, self.teets)
        validar_registro_ladder_teste(self.registro_ladder_volta, self.teets)
        
        self.client.login(username=self.teets.user.username, password=SENHA_TESTE)
        response = self.client.post(reverse('ladder:cancelar_registro_ladder', kwargs={'registro_id': self.registro_ladder.id}),
                                    {'salvar': 1})
        self.assertEqual(response.status_code, 200)
        
        # Garantir que registro de ladder não está cancelado
        self.assertTrue(RegistroLadder.objects.filter(id=self.registro_ladder.id, 
                                                      cancelamentoregistroladder__isnull=True).exists())
        
        # Verificar mensagens
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        regex = re.escape(f'Registro Ladder {self.registro_ladder_volta.id}: ') + r'.+'
        self.assertRegex(str(messages[0]), regex)
        