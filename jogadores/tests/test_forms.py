# -*- coding: utf-8 -*-
import datetime
from decimal import Decimal

from django.test import TestCase
from django.utils import timezone

from jogadores.forms import JogadorForm, StagesValidasForm, FeedbackForm, \
    SugestaoLadderForm
from jogadores.models import Jogador, Personagem, Stage
from jogadores.tests.utils_teste import criar_jogadores_teste, \
    criar_personagens_teste, criar_stages_teste


class JogadorFormTestCase(TestCase):
    """Testes para JogadorForm"""
    @classmethod
    def setUpTestData(cls):
        super(JogadorFormTestCase, cls).setUpTestData()
        
        # Configurar jogador
        criar_jogadores_teste(['teets'])
        
        cls.jogador = Jogador.objects.get(user__username='teets')
        
        # Configurar personagens
        criar_personagens_teste()
        
        cls.jogador.main = Personagem.objects.get(nome='Fox')
        
    def test_form_editar_nick_sucesso(self):
        """Testa edição de nick com sucesso"""
        form = JogadorForm({'nick': 'teets2', 'main': self.jogador.main.id, 'admin': self.jogador.admin}, instance=self.jogador)
        self.assertTrue(form.is_valid())
        # Usar commit=False como nas views
        jogador = form.save(commit=False)
        jogador.save()
        
        # Buscar edição
        self.jogador = Jogador.objects.get(user__username='teets')
        self.assertEqual(jogador.nick, self.jogador.nick)
        self.assertEqual(jogador.main, self.jogador.main)
        self.assertEqual(jogador.admin, self.jogador.admin)
        

    def test_form_editar_nick_vazio(self):
        """Testa edição de nick vazio"""
        form = JogadorForm({'nick': '', 'main': self.jogador.main.id, 'admin': self.jogador.admin}, instance=self.jogador)
        
        self.assertFalse(form.is_valid())
        self.assertIn('nick', form.errors)
        self.assertTrue(len(form.errors) == 1)
        
    def test_form_editar_nick_duplicado(self):
        """Testa edição de nick que está sendo utilizado"""
        criar_jogadores_teste(['sena'])
        form = JogadorForm({'nick': 'sena', 'main': self.jogador.main.id, 'admin': self.jogador.admin}, instance=self.jogador)
        
        self.assertFalse(form.is_valid())
        self.assertIn('nick', form.errors)
        self.assertTrue(len(form.errors) == 1)
        
    def test_form_editar_main_sucesso_preenchido(self):
        """Testa edição de main preenchido com sucesso"""
        form = JogadorForm({'nick': self.jogador.nick, 'main': Personagem.objects.get(nome='Marth').id, 'admin': self.jogador.admin}, instance=self.jogador)
        self.assertTrue(form.is_valid())
        # Usar commit=False como nas views
        jogador = form.save(commit=False)
        jogador.save()
        
        # Buscar edição
        self.jogador = Jogador.objects.get(user__username='teets')
        self.assertEqual(jogador.nick, self.jogador.nick)
        self.assertEqual(jogador.main, self.jogador.main)
        self.assertEqual(jogador.admin, self.jogador.admin)
        
    def test_form_editar_main_sucesso_nao_preenchido(self):
        """Testa edição de main não preenchido com sucesso"""
        form = JogadorForm({'nick': self.jogador.nick, 'main': None, 'admin': self.jogador.admin}, instance=self.jogador)
        self.assertTrue(form.is_valid())
        # Usar commit=False como nas views
        jogador = form.save(commit=False)
        jogador.save()
        
        # Buscar edição
        self.jogador = Jogador.objects.get(user__username='teets')
        self.assertEqual(jogador.nick, self.jogador.nick)
        self.assertEqual(jogador.main, self.jogador.main)
        self.assertEqual(jogador.admin, self.jogador.admin)
        
    def test_form_editar_main_erro(self):
        """Testa edição de main com erro"""
        id_invalido = Personagem.objects.all().order_by('-id')[0].id + 1
        form = JogadorForm({'nick': self.jogador.nick, 'main': id_invalido, 'admin': self.jogador.admin}, instance=self.jogador)
        
        self.assertFalse(form.is_valid())
        self.assertIn('main', form.errors)
        self.assertTrue(len(form.errors) == 1)
    
    def test_form_editar_admin_sucesso(self):
        """Testa edição de admin com sucesso"""
        self.assertTrue(self.jogador.admin)
        form = JogadorForm({'nick': self.jogador.nick, 'main': self.jogador.main.id, 'admin': (not self.jogador.admin)}, instance=self.jogador)
        self.assertTrue(form.is_valid())
        # Usar commit=False como nas views
        jogador = form.save(commit=False)
        jogador.save()
         
        # Buscar edição
        self.jogador = Jogador.objects.get(user__username='teets')
        self.assertEqual(jogador.nick, self.jogador.nick)
        self.assertEqual(jogador.main, self.jogador.main)
        self.assertEqual(jogador.admin, self.jogador.admin)
        self.assertFalse(self.jogador.admin)
        
    def test_form_editar_admin_bloqueado(self):
        """Testa edição de admin com sucesso"""
        self.assertTrue(self.jogador.admin)
        form = JogadorForm({'nick': self.jogador.nick, 'main': self.jogador.main.id, 'admin': (not self.jogador.admin)}, instance=self.jogador)
        form.fields['admin'].disabled = True
        self.assertTrue(form.is_valid())
        # Usar commit=False como nas views
        jogador = form.save(commit=False)
        jogador.save()
        
        self.assertTrue(self.jogador.admin)
        self.assertTrue(jogador.admin)
        
class StagesValidasFormTestCase(TestCase):
    """Testes para StagesValidasForm"""
    @classmethod
    def setUpTestData(cls):
        super(StagesValidasFormTestCase, cls).setUpTestData()
        
        # Configurar stages
        criar_stages_teste()
        
        # TODO Configurar stages válidas
        
    def test_form_editar_stages_validas_iniciais_sucesso(self):
        """Testa edição de stages válidas iniciais com sucesso"""
#         form = StagesValidasForm({'retorno': False, 'stages_validas': [Stage.objects.all()[0].id]})
#         self.assertTrue(form.is_valid())
#         
#         # TODO verificar esses testes
#         # Usar commit=False como nas views
#         jogador = form.save(commit=False)
#         jogador.save()
#         
#         # Buscar edição
#         self.jogador = Jogador.objects.get(user__username='teets')
#         self.assertEqual(jogador.nick, self.jogador.nick)
#         self.assertEqual(jogador.main, self.jogador.main)
#         self.assertEqual(jogador.admin, self.jogador.admin)
        
    def test_form_editar_stages_validas_retorno_sucesso(self):
        """Testa edição de stages válidas de retorno com sucesso"""
        
    def test_form_stages_vazias(self):
        """Testa erro ao deixar stages válidas vazias"""
        
    def test_form_stage_marcada_para_inicial_e_retorno(self):
        """Testa erro ao marcar uma stage válida para retorno como também válida para inicial"""
        
class FeedbackFormTestCase(TestCase):
    """Testes para FeedbackForm"""
    @classmethod
    def setUpTestData(cls):
        super(FeedbackFormTestCase, cls).setUpTestData()
        
        # Configurar jogador
        criar_jogadores_teste(['teets', 'sena'])
        cls.teets = Jogador.objects.get(nick='teets')
        cls.sena = Jogador.objects.get(nick='sena')
        
    def test_form_texto_sucesso(self):
        """Testa deixar texto de feedback com sucesso"""
        form = FeedbackForm({'texto': 'Teste'})
        self.assertTrue(form.is_valid())
        
        feedback = form.save(commit=False)
        self.assertEqual(feedback.texto, 'Teste')
        
    def test_form_texto_maior_que_limite(self):
        """Testa erro ao deixar feedback maior do que o limite"""
        texto_maior_que_limite = 't' * 1000
        form = FeedbackForm({'texto': texto_maior_que_limite})
        self.assertFalse(form.is_valid())
        
        self.assertIn('texto', form.errors)
        self.assertEqual(len(form.errors), 1)
        
class SugestaoLadderFormTestCase(TestCase):
    """Testes para SugestaoLadderForm"""
    @classmethod
    def setUpTestData(cls):
        super(SugestaoLadderFormTestCase, cls).setUpTestData()
        
        # Configurar jogador
        criar_jogadores_teste(['teets'])
        cls.teets = Jogador.objects.get(nick='teets')
        
    def test_form_texto_sucesso(self):
        """Testa deixar texto de feedback com sucesso"""
        form = SugestaoLadderForm({'texto': 'Teste'})
        self.assertTrue(form.is_valid())
        
        feedback = form.save(commit=False)
        self.assertEqual(feedback.texto, 'Teste')
        
    def test_form_texto_maior_que_limite(self):
        """Testa erro ao deixar feedback maior do que o limite"""
        texto_maior_que_limite = 't' * 10000
        form = SugestaoLadderForm({'texto': texto_maior_que_limite})
        self.assertFalse(form.is_valid())
        
        self.assertIn('texto', form.errors)
        self.assertEqual(len(form.errors), 1)