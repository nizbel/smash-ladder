# -*- coding: utf-8 -*-
from django.test.testcases import TestCase

from jogadores.models import Jogador
from jogadores.tests.utils_teste import criar_jogadores_teste
from torneios.forms import CriarTorneioForm, JogadorTorneioForm
from torneios.models import Torneio, JogadorTorneio, Time
from torneios.tests.utils_teste import criar_torneio_teste, \
    criar_jogadores_torneio_teste


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
                
class JogadorTorneioFormTestCase(TestCase):
    """Testes para formulário de JogadorTorneio"""
    @classmethod
    def setUpTestData(cls):
        super(JogadorTorneioFormTestCase, cls).setUpTestData()
        
        criar_jogadores_teste(['teets'])
        
        torneio = criar_torneio_teste()
        criar_jogadores_torneio_teste(torneio)
        cls.jogador_vinculado = JogadorTorneio.objects.get(nome='Teets')
        # Vincular a jogador da ladder
        cls.jogador_ladder = Jogador.objects.get(nick='teets')
        cls.jogador_vinculado.jogador = cls.jogador_ladder
        cls.jogador_vinculado.save()
        
        cls.jogador_desvinculado = JogadorTorneio.objects.get(nome='Sena')
        
        
    def test_nao_permitir_vincular_a_jogador_ladder_ja_vinculado(self):
        """Testa erro ao tentar vincular a jogador da ladder que já está vinculado"""
        form = JogadorTorneioForm({'valido': True, 'jogador': self.jogador_ladder.id, 'nome': self.jogador_desvinculado.nome}, 
                                  instance=self.jogador_desvinculado)
        self.assertFalse(form.is_valid())
        
        self.assertIn('__all__', form.errors)
        self.assertEqual(len(form.errors), 1)
        self.assertIn(f'Jogador da Ladder já está vinculado a {self.jogador_vinculado.seed} - {self.jogador_vinculado.nome}', 
                      form.errors['__all__'])
        
    def test_erro_invalido_com_time(self):
        """Testa erro ao deixar jogador inválido quando possui time"""
        form = JogadorTorneioForm({'time': Time.objects.all()[0].id, 'valido': False, 'nome': self.jogador_desvinculado.nome}, 
                                  instance=self.jogador_desvinculado)
        self.assertFalse(form.is_valid())
        
        self.assertIn('__all__', form.errors)
        self.assertEqual(len(form.errors), 1)
        self.assertIn('Jogador inválido não pode estar ligado a time', form.errors['__all__'])
        
    def test_erro_invalido_com_vinculo(self):
        """Testa erro ao deixar jogador inválido quando está vinculado a jogador da ladder"""
        
        form = JogadorTorneioForm({'valido': False, 'nome': self.jogador_vinculado.nome, 'jogador': self.jogador_ladder.id}, 
                                  instance=self.jogador_vinculado)
        self.assertFalse(form.is_valid())
        
        self.assertIn('__all__', form.errors)
        self.assertEqual(len(form.errors), 1)
        self.assertIn('Jogador inválido não pode possui vínculo a jogador da Ladder', form.errors['__all__'])
        