# -*- coding: utf-8 -*-
import datetime
from decimal import Decimal

from django.test import TestCase

from jogadores.forms import JogadorForm
from jogadores.models import Jogador, Personagem
from jogadores.tests.utils_teste import criar_jogadores_teste, \
    criar_personagens_teste


class JogadorFormTestCase(TestCase):
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
