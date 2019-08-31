# -*- coding: utf-8 -*-
from django.test.testcases import TestCase

from jogadores.tests.utils_teste import criar_jogadores_teste
from torneios.forms import CriarTorneioForm
from torneios.models import Torneio
from torneios.tests.utils_teste import criar_torneio_teste


class CriarTorneioFormTestCase(TestCase):
    """Testes para formulário de criação de torneio"""
    @classmethod
    def setUpTestData(cls):
        super(CriarTorneioFormTestCase, cls).setUpTestData()
        
        criar_jogadores_teste(['teets'])

    def test_criar_torneio_challonge_sucesso(self):
        """Testa criar um torneio no challonge com sucesso"""
        form = CriarTorneioForm({'identificador_torneio': 'teste', 'site': Torneio.SITE_CHALLONGE_ID, 'delimitador_time': '|'})
        self.assertTrue(form.is_valid())
        
        self.assertEqual(form.cleaned_data['identificador_torneio'], 'teste')
        self.assertEqual(form.cleaned_data['delimitador_time'], '|')
        self.assertEqual(form.cleaned_data['site'], Torneio.SITE_CHALLONGE_ID)
        
    def test_erro_url_ja_existente(self):
        """Testa erro ao criar torneio que já existe"""
        # Gera torneio
        criar_torneio_teste(url=f'{Torneio.SITE_CHALLONGE_URL}teste')
        
        form = CriarTorneioForm({'identificador_torneio': 'teste', 'site': Torneio.SITE_CHALLONGE_ID, 'delimitador_time': '|'})
        self.assertFalse(form.is_valid())
        
        self.assertIn('__all__', form.errors)
        self.assertEqual(len(form.errors), 1)
        self.assertIn(Torneio.MENSAGEM_ERRO_URL_TORNEIO_JA_EXISTENTE, form.errors['__all__'])
                