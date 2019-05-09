# -*- coding: utf-8 -*-
import datetime

from django.contrib.auth.models import User
from django.test.testcases import TestCase
from django.urls.base import reverse
from django.utils import timezone

from jogadores.models import Jogador, Personagem, Stage, StageValidaLadder,\
    RegistroFerias
from jogadores.tests.utils_teste import criar_jogadores_teste, SENHA_TESTE, \
    criar_personagens_teste, JOGADORES_TESTE, criar_stages_teste,\
    criar_stage_teste
from ladder.models import DesafioLadder
from ladder.tests.utils_teste import LADDER_FORMATO_TESTE
from smashLadder import settings


class ViewListarJogadoresTestCase(TestCase):
    """Testes para a view de listar jogadores"""
    @classmethod
    def setUpTestData(cls):
        super(ViewListarJogadoresTestCase, cls).setUpTestData()
        cls.user = User.objects.create_user('teste', 'teste@teste.com', 'teste')
        
        criar_jogadores_teste()
        
        cls.jogadores = list(Jogador.objects.all())
        
    def test_acesso_deslogado(self):
        """Testa acesso a tela de listar jogadores sem logar"""
        response = self.client.get(reverse('jogadores:listar_jogadores'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['jogadores']), len(JOGADORES_TESTE))
        self.assertEqual(response.context['jogadores'], self.jogadores)
        
    def test_acesso_logado(self):
        """Testa acesso a tela de listar jogadores logado"""
        self.client.login(username=self.user.username, password=SENHA_TESTE)
        response = self.client.get(reverse('jogadores:listar_jogadores'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['jogadores']), len(JOGADORES_TESTE))
        self.assertEqual(response.context['jogadores'], self.jogadores)
        for jogador in self.jogadores:
            self.assertContains(response, reverse('jogadores:detalhar_jogador', kwargs={'username': jogador.user.username}), 1)
            
        

class ViewDetalharJogadorTestCase(TestCase):
    """Testes para a view de detalhar jogador"""
    @classmethod
    def setUpTestData(cls):
        super(ViewDetalharJogadorTestCase, cls).setUpTestData()
        criar_jogadores_teste(['sena', 'teets'])
        
        cls.jogador_1 = Jogador.objects.get(nick='sena')
        cls.jogador_2 = Jogador.objects.get(nick='teets')
        
        dia_anterior = timezone.now() - datetime.timedelta(days=1)
        # Gerar desafios para jogador_2
        cls.desafio_validado_vitoria_1 = DesafioLadder.objects.create(desafiante=cls.jogador_1, desafiado=cls.jogador_2, 
                                                                      data_hora=dia_anterior.replace(hour=1),
                                                                      desafio_coringa=False, adicionado_por=cls.jogador_1,
                                                                      score_desafiante=1, score_desafiado=3, 
                                                                      admin_validador=cls.jogador_2)
        cls.desafio_validado_vitoria_2 = DesafioLadder.objects.create(desafiante=cls.jogador_2, desafiado=cls.jogador_1, 
                                                                      data_hora=dia_anterior.replace(hour=2), 
                                                                      desafio_coringa=False, adicionado_por=cls.jogador_1,
                                                                      score_desafiante=3, score_desafiado=0, 
                                                                      admin_validador=cls.jogador_2)
        cls.desafio_validado_vitoria_3 = DesafioLadder.objects.create(desafiante=cls.jogador_1, desafiado=cls.jogador_2, 
                                                                      data_hora=dia_anterior.replace(hour=3), 
                                                                      desafio_coringa=False, adicionado_por=cls.jogador_1,
                                                                      score_desafiante=2, score_desafiado=3, 
                                                                      admin_validador=cls.jogador_2)
        cls.desafio_validado_derrota_1 = DesafioLadder.objects.create(desafiante=cls.jogador_1, desafiado=cls.jogador_2, 
                                                                      data_hora=dia_anterior.replace(hour=4), 
                                                                      desafio_coringa=False, adicionado_por=cls.jogador_1,
                                                                      score_desafiante=3, score_desafiado=1, 
                                                                      admin_validador=cls.jogador_2)
        cls.desafio_validado_derrota_2 = DesafioLadder.objects.create(desafiante=cls.jogador_1, desafiado=cls.jogador_2, 
                                                                      data_hora=dia_anterior.replace(hour=5),
                                                                      desafio_coringa=False, adicionado_por=cls.jogador_1,
                                                                      score_desafiante=3, score_desafiado=2, 
                                                                      admin_validador=cls.jogador_2)
        
        
        cls.desafio_nao_validado_vitoria = DesafioLadder.objects.create(desafiante=cls.jogador_1, desafiado=cls.jogador_2, 
                                                                      data_hora=dia_anterior.replace(hour=6),
                                                                      desafio_coringa=False, adicionado_por=cls.jogador_1,
                                                                      score_desafiante=1, score_desafiado=3)
        cls.desafio_nao_validado_derrota = DesafioLadder.objects.create(desafiante=cls.jogador_1, desafiado=cls.jogador_2, 
                                                                      data_hora=dia_anterior.replace(hour=7),
                                                                      desafio_coringa=False, adicionado_por=cls.jogador_1,
                                                                      score_desafiante=3, score_desafiado=2)
        
    def test_acesso_deslogado(self):
        """Testa acesso a tela de detalhar jogador sem logar"""
        response = self.client.get(reverse('jogadores:detalhar_jogador', kwargs={'username': self.jogador_2.user.username}))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['jogador'], self.jogador_2)
        self.assertIn('desafios', response.context)
        self.assertNotContains(response, reverse('jogadores:editar_jogador', kwargs={'username': self.jogador_2.user.username}))
        
    def test_acesso_logado(self):
        """Testa acesso a tela de detalhar jogador logado"""
        self.client.login(username=self.jogador_1.user.username, password=SENHA_TESTE)
        response = self.client.get(reverse('jogadores:detalhar_jogador', kwargs={'username': self.jogador_2.user.username}))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['jogador'], self.jogador_2)
        self.assertIn('desafios', response.context)
        self.assertNotContains(response, reverse('jogadores:editar_jogador', kwargs={'username': self.jogador_2.user.username}))
        
    def test_acesso_logado_proprio_usuario(self):
        """Testa acesso a tela de detalhar a si mesmo"""
        self.client.login(username=self.jogador_2.user.username, password=SENHA_TESTE)
        response = self.client.get(reverse('jogadores:detalhar_jogador', kwargs={'username': self.jogador_2.user.username}))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['jogador'], self.jogador_2)
        self.assertIn('desafios', response.context)
        self.assertContains(response, reverse('jogadores:editar_jogador', kwargs={'username': self.jogador_2.user.username}), 1)
        
    def test_acesso_logado_admin(self):
        """Testa acesso a tela de detalhar outro jogador, sendo admin"""
        self.client.login(username=self.jogador_2.user.username, password=SENHA_TESTE)
        response = self.client.get(reverse('jogadores:detalhar_jogador', kwargs={'username': self.jogador_1.user.username}))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['jogador'], self.jogador_1)
        self.assertIn('desafios', response.context)
        self.assertContains(response, reverse('jogadores:editar_jogador', kwargs={'username': self.jogador_1.user.username}), 1)
        
    def test_dados_desafio_jogador_sem_desafios(self):
        """Testa dados de desafios de jogador sem desafios"""
        # Remover desafios
        DesafioLadder.objects.all().delete()
        
        response = self.client.get(reverse('jogadores:detalhar_jogador', kwargs={'username': self.jogador_2.user.username}))
        self.assertEqual(response.status_code, 200)
        self.assertNotEqual(response.context['desafios'], {})
        self.assertEqual(response.context['desafios']['feitos'], 0)
        self.assertEqual(response.context['desafios']['recebidos'], 0)
        self.assertEqual(response.context['desafios']['vitorias'], 0)
        self.assertEqual(response.context['desafios']['derrotas'], 0)
        self.assertEqual(response.context['jogador'].percentual_vitorias, 0)
        
        # Evitar mostrar últimos desafios
        self.assertNotContains(response, 'Últimos desafios')
        
    def test_dados_desafio_jogador_com_desafios(self):
        """Testa dados de desafios de jogador com desafios"""
        response = self.client.get(reverse('jogadores:detalhar_jogador', kwargs={'username': self.jogador_2.user.username}))
        self.assertEqual(response.status_code, 200)
        self.assertNotEqual(response.context['desafios'], {})
        self.assertEqual(response.context['desafios']['feitos'], 1)
        self.assertEqual(response.context['desafios']['recebidos'], 4)
        self.assertEqual(response.context['desafios']['vitorias'], 3)
        self.assertEqual(response.context['desafios']['derrotas'], 2)
        self.assertEqual(response.context['jogador'].percentual_vitorias, 60)
        
    def test_jogador_de_ferias(self):
        """Testa mensagem de jogador de férias"""
        # Colocar jogador de férias
        RegistroFerias.objects.create(jogador=self.jogador_2, data_inicio=timezone.now() - datetime.timedelta(days=5), 
                                      data_fim=timezone.now() + datetime.timedelta(days=5))
        
        response = self.client.get(reverse('jogadores:detalhar_jogador', kwargs={'username': self.jogador_2.user.username}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Jogador está de férias')
        
    def test_jogador_ultimos_desafios(self):
        """Testa mostrar últimos desafios de jogador"""
        response = self.client.get(reverse('jogadores:detalhar_jogador', kwargs={'username': self.jogador_2.user.username}))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['jogador'].ultimos_desafios), 3)
        
        ultimos_desafios = response.context['jogador'].ultimos_desafios
        # Ordem decrescente de horários
        self.assertTrue(ultimos_desafios[0].data_hora > ultimos_desafios[1].data_hora)
        self.assertTrue(ultimos_desafios[1].data_hora > ultimos_desafios[2].data_hora)
        
        # Deve permitir detalhar cada desafio
        for desafio in ultimos_desafios:
            self.assertContains(response, reverse('ladder:detalhar_desafio', kwargs={'desafio_id': desafio.id}), 1)
        
        # Deve mostrar últimos desafios
        self.assertContains(response, 'Últimos desafios')
        self.assertContains(response, reverse('jogadores:listar_desafios_jogador', kwargs={'username': self.jogador_2.user.username}))
        

class ViewEditarJogadorTestCase(TestCase):
    """Testes para a view de detalhar jogador"""
    @classmethod
    def setUpTestData(cls):
        super(ViewEditarJogadorTestCase, cls).setUpTestData()
        criar_jogadores_teste(['sena', 'teets'])
        
        cls.jogador_1 = Jogador.objects.get(nick='sena')
        cls.jogador_2 = Jogador.objects.get(nick='teets')
        
        criar_personagens_teste()
        
    def test_acesso_deslogado(self):
        """Testa acesso a tela de editar jogador sem logar"""
        response = self.client.get(reverse('jogadores:editar_jogador', kwargs={'username': self.jogador_2.user.username}))
        url_esperada = settings.LOGIN_URL + '?next=' + reverse('jogadores:editar_jogador', kwargs={'username': self.jogador_2.user.username})
        self.assertRedirects(response, url_esperada)
        self.assertEqual(response.status_code, 302)
        
    def test_acesso_logado_outro_usuario(self):
        """Testa acesso a tela de editar jogador logado com outro usuário"""
        self.client.login(username=self.jogador_1.user.username, password=SENHA_TESTE)
        response = self.client.get(reverse('jogadores:editar_jogador', kwargs={'username': self.jogador_2.user.username}))
        self.assertEqual(response.status_code, 403)
        
    def test_acesso_logado_outro_usuario_admin(self):
        """Testa acesso a tela de editar jogador logado com outro usuário admin"""
        self.client.login(username=self.jogador_2.user.username, password=SENHA_TESTE)
        response = self.client.get(reverse('jogadores:editar_jogador', kwargs={'username': self.jogador_1.user.username}))
        self.assertEqual(response.status_code, 200)
        self.assertIn('form_jogador', response.context)
        self.assertEqual(response.context['jogador'], self.jogador_1)
        self.assertFalse(response.context['form_jogador'].fields['admin'].disabled)
        self.assertTrue(response.context['form_jogador'].fields['main'].disabled)
        self.assertTrue(response.context['form_jogador'].fields['nick'].disabled)
        
    def test_acesso_logado_proprio_usuario(self):
        """Testa acesso a tela de editar o próprio usuário"""
        self.client.login(username=self.jogador_1.user.username, password=SENHA_TESTE)
        response = self.client.get(reverse('jogadores:editar_jogador', kwargs={'username': self.jogador_1.user.username}))
        self.assertEqual(response.status_code, 200)
        self.assertIn('form_jogador', response.context)
        self.assertEqual(response.context['jogador'], self.jogador_1)
        self.assertTrue(response.context['form_jogador'].fields['admin'].disabled)
        self.assertFalse(response.context['form_jogador'].fields['main'].disabled)
        self.assertFalse(response.context['form_jogador'].fields['nick'].disabled)
        
    def test_acesso_logado_proprio_usuario_admin(self):
        """Testa acesso a tela de editar o próprio usuário sendo admin"""
        self.client.login(username=self.jogador_2.user.username, password=SENHA_TESTE)
        response = self.client.get(reverse('jogadores:editar_jogador', kwargs={'username': self.jogador_2.user.username}))
        self.assertEqual(response.status_code, 200)
        self.assertIn('form_jogador', response.context)
        self.assertEqual(response.context['jogador'], self.jogador_2)
        self.assertFalse(response.context['form_jogador'].fields['admin'].disabled)
        self.assertFalse(response.context['form_jogador'].fields['main'].disabled)
        self.assertFalse(response.context['form_jogador'].fields['nick'].disabled)
        
    def test_edicao_campos_proprio_usuario(self):
        """Testa edição de campos pelo próprio usuário"""
        marth = Personagem.objects.get(nome='Marth')
        self.client.login(username=self.jogador_1.user.username, password=SENHA_TESTE)
        response = self.client.post(reverse('jogadores:editar_jogador', kwargs={'username': self.jogador_1.user.username}),
                                    {'nick': 'sena2', 'main': marth.id})
        self.assertRedirects(response, reverse('jogadores:detalhar_jogador', kwargs={'username': self.jogador_1.user.username}))
        
        # Atualizar objeto
        self.jogador_1 = Jogador.objects.get(user__username=self.jogador_1.user.username)
        self.assertEqual(self.jogador_1.nick, 'sena2')
        self.assertEqual(self.jogador_1.main, marth)
        
    def test_edicao_campos_admin(self):
        """Testa edição de campos pelo admin"""
        self.client.login(username=self.jogador_2.user.username, password=SENHA_TESTE)
        response = self.client.post(reverse('jogadores:editar_jogador', kwargs={'username': self.jogador_1.user.username}),
                                    {'admin': True})
        self.assertRedirects(response, reverse('jogadores:detalhar_jogador', kwargs={'username': self.jogador_1.user.username}))
        
        # Atualizar objeto
        self.jogador_1 = Jogador.objects.get(user__username=self.jogador_1.user.username)
        self.assertEqual(self.jogador_1.admin, True)
        
    def test_edicao_campos_proprio_usuario_admin(self):
        """Testa edição de campos pelo admin"""
        marth = Personagem.objects.get(nome='Marth')
        self.client.login(username=self.jogador_2.user.username, password=SENHA_TESTE)
        response = self.client.post(reverse('jogadores:editar_jogador', kwargs={'username': self.jogador_2.user.username}),
                                    {'nick': 'teets2', 'main': marth.id, 'admin': False})
        self.assertRedirects(response, reverse('jogadores:detalhar_jogador', kwargs={'username': self.jogador_2.user.username}))
        
        # Atualizar objeto
        self.jogador_2 = Jogador.objects.get(user__username=self.jogador_2.user.username)
        self.assertEqual(self.jogador_2.admin, False)
        self.assertEqual(self.jogador_2.main, marth)
        self.assertEqual(self.jogador_2.nick, 'teets2')
        
class ViewListarStagesTestCase(TestCase):
    """Testes para a view de listar stages"""
    @classmethod
    def setUpTestData(cls):
        super(ViewListarStagesTestCase, cls).setUpTestData()
        criar_stages_teste()
        criar_jogadores_teste(['sena',])
        
        cls.jogador_1 = Jogador.objects.get(nick='sena')
        
        cls.stages = list(Stage.objects.all().order_by('nome', 'modelo'))
        
        # Definir 2 stages como válidas para torneio
        StageValidaLadder.objects.create(stage=Stage.objects.get(nome='Final Destination', modelo=Stage.TIPO_NORMAL))
        StageValidaLadder.objects.create(stage=Stage.objects.get(nome='Dreamland', modelo=Stage.TIPO_NORMAL))
        
    def test_acesso_deslogado(self):
        """Testa acesso a tela de listar stages sem logar"""
        response = self.client.get(reverse('stages:listar_stages'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('stages', response.context)
        self.assertEqual(response.context['stages'], self.stages)
        
    def test_acesso_logado(self):
        """Testa acesso a tela de listar stages logado"""
        self.client.login(username=self.jogador_1.user.username, password=SENHA_TESTE)
        response = self.client.get(reverse('stages:listar_stages'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('stages', response.context)
        self.assertEqual(response.context['stages'], self.stages)
        
    def test_indicar_stages_validas_ladder(self):
        """Verificar se página indica stages válidas para ladder"""
        response = self.client.get(reverse('stages:listar_stages'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Válida para Ladder', 2)
        
    def test_ver_apenas_stages_validas_ladder(self):
        """Verificar se a página traz apenas stages válidas caso seja chamada pela URL de ladder"""
        response = self.client.get(reverse('stages:listar_stages_validas'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['stages']), 2)
        self.assertContains(response, 'Válida para Ladder', 2)
        
class ViewDetalharStageTestCase(TestCase):
    """Testes para a view de detalhar stage"""
    @classmethod
    def setUpTestData(cls):
        super(ViewDetalharStageTestCase, cls).setUpTestData()
        cls.stage = criar_stage_teste()
        criar_jogadores_teste(['sena',])
        
        cls.jogador_1 = Jogador.objects.get(nick='sena')
        
    def test_acesso_deslogado(self):
        """Testa acesso a tela de detalhar stage sem logar"""
        response = self.client.get(reverse('stages:detalhar_stage_por_id', kwargs={'stage_id': self.stage.id}))
        self.assertEqual(response.status_code, 200)
        self.assertIn('stage', response.context)
        self.assertEqual(response.context['stage'], self.stage)
        
    def test_acesso_logado(self):
        """Testa acesso a tela de detalhar stage logado"""
        self.client.login(username=self.jogador_1.user.username, password=SENHA_TESTE)
        response = self.client.get(reverse('stages:detalhar_stage_por_id', kwargs={'stage_id': self.stage.id}))
        self.assertEqual(response.status_code, 200)
        self.assertIn('stage', response.context)
        self.assertEqual(response.context['stage'], self.stage)
        
    def test_indicar_stages_validas_torneio(self):
        """Verificar se página indica stage válida para ladder"""
        # Validar para ladder
        StageValidaLadder.objects.create(stage=self.stage)
        
        response = self.client.get(reverse('stages:detalhar_stage_por_id', kwargs={'stage_id': self.stage.id}))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['stage'].valida_para_ladder)
        
        
class ViewListarDesafiosJogadorTestCase(TestCase):
    """Testes para a view de listar desafios de um jogador"""
    @classmethod
    def setUpTestData(cls):
        super(ViewListarJogadoresTestCase, cls).setUpTestData()
        cls.user = User.objects.create_user('teste', 'teste@teste.com', 'teste')
        
        criar_jogadores_teste(['sena', 'teets'])
        cls.jogador_sem_desafios = Jogador.objects.get(nick='sena')
        cls.jogador_com_desafios = Jogador.objects.get(nick='teets')
        
    def test_acesso_deslogado(self):
        """Testa acesso a tela de listar desafios de um jogador sem logar"""
        response = self.client.get(reverse('jogadores:listar_desafios_jogador', kwargs={'username': self.jogador_sem_desafios.user.username}))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['desafios']), 0)
        self.assertContains(response, 'Jogador sem desafios cadastrados')
        
        # Deve conter link para voltar para tela de detalhamento
        self.assertContains(response, reverse('jogadores:detalhar_jogador', kwargs={'username': self.jogador_sem_desafios.user.username}), 1)
        
    def test_acesso_logado(self):
        """Testa acesso a tela de listar desafios de um jogador logado"""
        response = self.client.get(reverse('jogadores:listar_desafios_jogador', kwargs={'username': self.jogador_sem_desafios.user.username}))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['desafios']), 0)
        self.assertContains(response, 'Jogador sem desafios cadastrados')
        
        # Deve conter link para voltar para tela de detalhamento
        self.assertContains(response, reverse('jogadores:detalhar_jogador', kwargs={'username': self.jogador_sem_desafios.user.username}), 1)
        
    def test_visualizar_jogador_com_desafios(self):
        """Testa visualização de desafios de um jogador com desafios cadastrados"""
        response = self.client.get(reverse('jogadores:listar_desafios_jogador', kwargs={'username': self.jogador_com_desafios.user.username}))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['desafios']), 7)
        self.assertNotContains(response, 'Jogador sem desafios cadastrados')
        
        # Deve permitir detalhar cada desafio
        for desafio in response.context['desafios']:
            self.assertContains(response, reverse('ladder:detalhar_desafio', kwargs={'desafio_id': desafio.id}), 1)
        
        # Deve conter link para voltar para tela de detalhamento
        self.assertContains(response, reverse('jogadores:detalhar_jogador', kwargs={'username': self.jogador_sem_desafios.user.username}), 1)