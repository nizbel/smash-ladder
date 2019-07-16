# -*- coding: utf-8 -*-
import datetime

from django.contrib.auth.models import User
from django.test.testcases import TestCase
from django.urls.base import reverse
from django.utils import timezone

from jogadores.models import Jogador, Personagem, Stage, StageValidaLadder, \
    RegistroFerias
from jogadores.tests.utils_teste import criar_jogadores_teste, SENHA_TESTE, \
    criar_personagens_teste, JOGADORES_TESTE, criar_stages_teste, \
    criar_stage_teste
from ladder.models import DesafioLadder, RemocaoJogador, DecaimentoJogador, \
    PosicaoLadder
from ladder.tests.utils_teste import criar_ladder_teste, \
    criar_desafio_ladder_simples_teste
from ladder.utils import remover_jogador, decair_jogador, alterar_ladder, \
    processar_remocao
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
#         criar_jogadores_teste(['sena', 'teets', 'mad'])
        criar_jogadores_teste()
        
        cls.jogador_1 = Jogador.objects.get(nick='teets')
        cls.jogador_2 = Jogador.objects.get(nick='saraiva')
        cls.jogador_3 = Jogador.objects.get(nick='sena')
        cls.jogador_4 = Jogador.objects.get(nick='mad')
        cls.jogador_5 = Jogador.objects.get(nick='blöwer')
        cls.jogador_6 = Jogador.objects.get(nick='frodo')
        
        criar_ladder_teste()
        
        dia_anterior = timezone.now() - datetime.timedelta(days=1)
        # Gerar desafios para jogador 1
        cls.desafio_validado_vitoria_1 = DesafioLadder.objects.create(desafiante=cls.jogador_3, desafiado=cls.jogador_1, 
                                                                      data_hora=dia_anterior.replace(hour=1),
                                                                      desafio_coringa=False, adicionado_por=cls.jogador_3,
                                                                      score_desafiante=1, score_desafiado=3, 
                                                                      admin_validador=cls.jogador_1)
        cls.desafio_validado_vitoria_2 = DesafioLadder.objects.create(desafiante=cls.jogador_3, desafiado=cls.jogador_1, 
                                                                      data_hora=dia_anterior.replace(hour=2), 
                                                                      desafio_coringa=False, adicionado_por=cls.jogador_3,
                                                                      score_desafiante=0, score_desafiado=3, 
                                                                      admin_validador=cls.jogador_1)
        cls.desafio_validado_vitoria_3 = DesafioLadder.objects.create(desafiante=cls.jogador_3, desafiado=cls.jogador_1, 
                                                                      data_hora=dia_anterior.replace(hour=3), 
                                                                      desafio_coringa=False, adicionado_por=cls.jogador_3,
                                                                      score_desafiante=2, score_desafiado=3, 
                                                                      admin_validador=cls.jogador_1)
        cls.desafio_validado_vitoria_4 = DesafioLadder.objects.create(desafiante=cls.jogador_3, desafiado=cls.jogador_1, 
                                                                      data_hora=dia_anterior.replace(hour=4), 
                                                                      desafio_coringa=False, adicionado_por=cls.jogador_3,
                                                                      score_desafiante=2, score_desafiado=3, 
                                                                      admin_validador=cls.jogador_1)
        cls.desafio_validado_derrota_1 = DesafioLadder.objects.create(desafiante=cls.jogador_3, desafiado=cls.jogador_1, 
                                                                      data_hora=dia_anterior.replace(hour=5),
                                                                      desafio_coringa=False, adicionado_por=cls.jogador_3,
                                                                      score_desafiante=3, score_desafiado=2, 
                                                                      admin_validador=cls.jogador_1)
        
        # Derrota jogador 5
        cls.desafio_validado_derrota_3 = DesafioLadder.objects.create(desafiante=cls.jogador_5, desafiado=cls.jogador_2, 
                                                                      data_hora=dia_anterior.replace(hour=8),
                                                                      desafio_coringa=False, adicionado_por=cls.jogador_1,
                                                                      score_desafiante=2, score_desafiado=3, 
                                                                      admin_validador=cls.jogador_1,
                                                                      posicao_desafiante=5, posicao_desafiado=2)
                                                            
        
        
        cls.desafio_nao_validado_vitoria = DesafioLadder.objects.create(desafiante=cls.jogador_3, desafiado=cls.jogador_1, 
                                                                      data_hora=dia_anterior.replace(hour=6),
                                                                      desafio_coringa=False, adicionado_por=cls.jogador_3,
                                                                      score_desafiante=1, score_desafiado=3)
        cls.desafio_nao_validado_derrota = DesafioLadder.objects.create(desafiante=cls.jogador_3, desafiado=cls.jogador_1, 
                                                                      data_hora=dia_anterior.replace(hour=7),
                                                                      desafio_coringa=False, adicionado_por=cls.jogador_3,
                                                                      score_desafiante=3, score_desafiado=2)
        
    def test_acesso_deslogado(self):
        """Testa acesso a tela de detalhar jogador sem logar"""
        response = self.client.get(reverse('jogadores:detalhar_jogador', kwargs={'username': self.jogador_1.user.username}))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['jogador'], self.jogador_1)
        self.assertIn('desafios', response.context)
        self.assertNotContains(response, reverse('jogadores:editar_jogador', kwargs={'username': self.jogador_1.user.username}))
        
    def test_acesso_logado(self):
        """Testa acesso a tela de detalhar jogador logado"""
        self.client.login(username=self.jogador_3.user.username, password=SENHA_TESTE)
        response = self.client.get(reverse('jogadores:detalhar_jogador', kwargs={'username': self.jogador_1.user.username}))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['jogador'], self.jogador_1)
        self.assertIn('desafios', response.context)
        self.assertNotContains(response, reverse('jogadores:editar_jogador', kwargs={'username': self.jogador_1.user.username}))
        
    def test_acesso_logado_proprio_usuario(self):
        """Testa acesso a tela de detalhar a si mesmo"""
        self.client.login(username=self.jogador_3.user.username, password=SENHA_TESTE)
        response = self.client.get(reverse('jogadores:detalhar_jogador', kwargs={'username': self.jogador_3.user.username}))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['jogador'], self.jogador_3)
        self.assertIn('desafios', response.context)
        self.assertContains(response, reverse('jogadores:editar_jogador', kwargs={'username': self.jogador_3.user.username}), 1)
        
    def test_acesso_logado_admin(self):
        """Testa acesso a tela de detalhar outro jogador, sendo admin"""
        self.client.login(username=self.jogador_1.user.username, password=SENHA_TESTE)
        response = self.client.get(reverse('jogadores:detalhar_jogador', kwargs={'username': self.jogador_3.user.username}))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['jogador'], self.jogador_3)
        self.assertIn('desafios', response.context)
        self.assertContains(response, reverse('jogadores:editar_jogador', kwargs={'username': self.jogador_3.user.username}), 1)
        
    def test_dados_desafio_jogador_sem_desafios(self):
        """Testa dados de desafios de jogador sem desafios"""
        response = self.client.get(reverse('jogadores:detalhar_jogador', kwargs={'username': self.jogador_6.user.username}))
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
        response = self.client.get(reverse('jogadores:detalhar_jogador', kwargs={'username': self.jogador_1.user.username}))
        self.assertEqual(response.status_code, 200)
        self.assertNotEqual(response.context['desafios'], {})
        self.assertEqual(response.context['desafios']['feitos'], 0)
        self.assertEqual(response.context['desafios']['recebidos'], 5)
        self.assertEqual(response.context['desafios']['vitorias'], 4)
        self.assertEqual(response.context['desafios']['derrotas'], 1)
        self.assertEqual(response.context['jogador'].percentual_vitorias, 80)
        
        response = self.client.get(reverse('jogadores:detalhar_jogador', kwargs={'username': self.jogador_3.user.username}))
        self.assertEqual(response.status_code, 200)
        self.assertNotEqual(response.context['desafios'], {})
        self.assertEqual(response.context['desafios']['feitos'], 5)
        self.assertEqual(response.context['desafios']['recebidos'], 0)
        self.assertEqual(response.context['desafios']['vitorias'], 1)
        self.assertEqual(response.context['desafios']['derrotas'], 4)
        self.assertEqual(response.context['jogador'].percentual_vitorias, 20)
        
    def test_jogador_de_ferias(self):
        """Testa mensagem de jogador de férias"""
        # Colocar jogador de férias
        RegistroFerias.objects.create(jogador=self.jogador_1, data_inicio=timezone.now() - datetime.timedelta(days=5), 
                                      data_fim=timezone.now() + datetime.timedelta(days=5))
        
        response = self.client.get(reverse('jogadores:detalhar_jogador', kwargs={'username': self.jogador_1.user.username}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Jogador está de férias')
        
    def test_jogador_ultimos_desafios(self):
        """Testa mostrar últimos desafios de jogador"""
        response = self.client.get(reverse('jogadores:detalhar_jogador', kwargs={'username': self.jogador_1.user.username}))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['jogador'].ultimos_desafios), 3)
        
        ultimos_desafios = response.context['jogador'].ultimos_desafios
        # Ordem decrescente de horários
        self.assertTrue(ultimos_desafios[0].data_hora > ultimos_desafios[1].data_hora)
        self.assertTrue(ultimos_desafios[1].data_hora > ultimos_desafios[2].data_hora)
        
        # Deve permitir detalhar cada desafio
        for desafio in ultimos_desafios:
            self.assertContains(response, reverse('ladder:detalhar_desafio_ladder', kwargs={'desafio_id': desafio.id}), 1)
        
        # Deve mostrar últimos desafios
        self.assertContains(response, 'Últimos desafios')
        self.assertContains(response, reverse('jogadores:listar_desafios_jogador', kwargs={'username': self.jogador_1.user.username}))
        
    def test_jogador_com_remocoes_afetando_grafico_ladder(self):
        """Testa mostrar gráfico de posições na ladder com remoções que o afetam"""
        # Adicionar remoção para jogador 3
        remocao = RemocaoJogador.objects.create(jogador=self.jogador_3, data=timezone.localtime() - datetime.timedelta(minutes=1), 
                                      admin_removedor=self.jogador_1, posicao_jogador=3)
        processar_remocao(remocao)
        
        response = self.client.get(reverse('jogadores:detalhar_jogador', kwargs={'username': self.jogador_5.user.username}))
        self.assertEqual(response.status_code, 200)
        graf_variacao_ladder = response.context['jogador'].grafico_variacao_posicao
        self.assertNotEqual(graf_variacao_ladder, [])
        self.assertEqual(graf_variacao_ladder[0]['y'], 5)
        self.assertEqual(graf_variacao_ladder[1]['y'], 4)
        
    def test_jogador_com_decaimentos_afetando_grafico_ladder(self):
        """Testa mostrar gráfico de posições na ladder com decaimentos que o afetam"""
        # Adicionar decaimento para jogador 4
        decaimento = DecaimentoJogador.objects.create(jogador=self.jogador_4, data=timezone.localtime() - datetime.timedelta(minutes=1), 
                                         posicao_inicial=4, qtd_periodos_inatividade=1)
        decair_jogador(decaimento)
        
        response = self.client.get(reverse('jogadores:detalhar_jogador', kwargs={'username': self.jogador_5.user.username}))
        self.assertEqual(response.status_code, 200)
        graf_variacao_ladder = response.context['jogador'].grafico_variacao_posicao
        self.assertNotEqual(graf_variacao_ladder, [])
        self.assertEqual(graf_variacao_ladder[0]['y'], 5)
        self.assertEqual(graf_variacao_ladder[1]['y'], 4)
        
    def test_jogador_com_desafios_afetando_grafico_ladder(self):
        """Testa mostrar gráfico de posições na ladder com desafios que o afetam"""
        # Adicionar desafio para jogador 6
        desafio = DesafioLadder.objects.create(desafiante=self.jogador_6, desafiado=self.jogador_4, 
                                                                      data_hora=timezone.localtime() - datetime.timedelta(minutes=1),
                                                                      desafio_coringa=False, adicionado_por=self.jogador_1,
                                                                      score_desafiante=3, score_desafiado=2, 
                                                                      admin_validador=self.jogador_1)
        alterar_ladder(desafio)
        
        response = self.client.get(reverse('jogadores:detalhar_jogador', kwargs={'username': self.jogador_5.user.username}))
        self.assertEqual(response.status_code, 200)
        graf_variacao_ladder = response.context['jogador'].grafico_variacao_posicao
        self.assertNotEqual(graf_variacao_ladder, [])
        self.assertEqual(graf_variacao_ladder[0]['y'], 5)
        self.assertEqual(graf_variacao_ladder[1]['y'], 6)
        
    def test_jogador_removido_recomeca_grafico_ladder(self):
        """Testa recomeço de gráfico de ladder caso jogador tenha sido removido previamente"""
        # Adicionar remoção para jogador 1
        remocao = RemocaoJogador.objects.create(jogador=self.jogador_1, data=timezone.localtime() - datetime.timedelta(minutes=5), 
                                      admin_removedor=self.jogador_1, posicao_jogador=1)
        remover_jogador(remocao)
        
        # Novo desafio recomeçando a ladder, desafiando último (posição 9)
        desafio = DesafioLadder.objects.create(desafiante=self.jogador_1, desafiado=PosicaoLadder.objects.get(posicao=9).jogador, 
                                                                      data_hora=timezone.localtime() - datetime.timedelta(minutes=1),
                                                                      desafio_coringa=False, adicionado_por=self.jogador_1,
                                                                      score_desafiante=3, score_desafiado=2, 
                                                                      admin_validador=self.jogador_1)
        alterar_ladder(desafio)
        
        response = self.client.get(reverse('jogadores:detalhar_jogador', kwargs={'username': self.jogador_1.user.username}))
        self.assertEqual(response.status_code, 200)
        graf_variacao_ladder = response.context['jogador'].grafico_variacao_posicao
        self.assertNotEqual(graf_variacao_ladder, [])
        self.assertEqual(graf_variacao_ladder[0]['y'], 10)
        self.assertEqual(graf_variacao_ladder[1]['y'], 9)
        
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
        for stage in response.context['stages']:
            self.assertTrue(hasattr(stage, 'stagevalidaladder'))
        
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
        super(ViewListarDesafiosJogadorTestCase, cls).setUpTestData()
        cls.user = User.objects.create_user('teste', 'teste@teste.com', 'teste')
        
        criar_jogadores_teste(['sena', 'teets', 'mad'])
        cls.jogador_sem_desafios = Jogador.objects.get(nick='sena')
        cls.jogador_com_desafios = Jogador.objects.get(nick='teets')
        terceiro = Jogador.objects.get(nick='mad')
        
        # Gerar desafios
        for indice in range(7):
            criar_desafio_ladder_simples_teste(terceiro, cls.jogador_com_desafios, 1, 3, 
                                               timezone.now() - datetime.timedelta(days=5*indice), False, cls.jogador_com_desafios)
        
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
            self.assertContains(response, reverse('ladder:detalhar_desafio_ladder', kwargs={'desafio_id': desafio.id}), 1)
        
        # Deve conter link para voltar para tela de detalhamento
        self.assertContains(response, reverse('jogadores:detalhar_jogador', kwargs={'username': self.jogador_com_desafios.user.username}), 1)
        
class ViewListarPersonagensTestCase(TestCase):
    """Testes para a view de listar stages"""
    @classmethod
    def setUpTestData(cls):
        super(ViewListarPersonagensTestCase, cls).setUpTestData()
        criar_personagens_teste()
        cls.personagens = list(Personagem.objects.all().order_by('nome'))
        
        criar_jogadores_teste(['sena',])
        cls.jogador_1 = Jogador.objects.get(nick='sena')
        
    def test_acesso_deslogado(self):
        """Testa acesso a tela de listar personagens sem logar"""
        response = self.client.get(reverse('personagens:listar_personagens'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('personagens', response.context)
        self.assertEqual(response.context['personagens'], self.personagens)
        
    def test_acesso_logado(self):
        """Testa acesso a tela de listar personagens logado"""
        self.client.login(username=self.jogador_1.user.username, password=SENHA_TESTE)
        response = self.client.get(reverse('personagens:listar_personagens'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('personagens', response.context)
        self.assertEqual(response.context['personagens'], self.personagens)
        
class ViewDetalharPersonagemTestCase(TestCase):
    """Testes para a view de detalhar personagem"""
    @classmethod
    def setUpTestData(cls):
        super(ViewDetalharPersonagemTestCase, cls).setUpTestData()
        criar_personagens_teste()
        cls.personagem = Personagem.objects.get(nome='Marth')
        
        criar_jogadores_teste(['sena', 'teets',])
        cls.jogador_1 = Jogador.objects.get(nick='sena')
        cls.jogador_2 = Jogador.objects.get(nick='teets')
        
        cls.stage = criar_stage_teste()
        
        cls.desafio = criar_desafio_ladder_completo_teste(cls.jogador_1, cls.jogador_2, 3, 0, timezone.now(), False, cls.jogador_1)
        
    def test_acesso_deslogado(self):
        """Testa acesso a tela de detalhar personagem sem logar"""
        response = self.client.get(reverse('personagens:detalhar_personagem_por_id', kwargs={'personagem_id': self.personagem.id}))
        self.assertEqual(response.status_code, 200)
        self.assertIn('personagem', response.context)
        self.assertEqual(response.context['personagem'], self.personagem)
        
    def test_acesso_logado(self):
        """Testa acesso a tela de detalhar personagem logado"""
        self.client.login(username=self.jogador_1.user.username, password=SENHA_TESTE)
        response = self.client.get(reverse('personagens:detalhar_stage_por_id', kwargs={'personagem_id': self.personagem.id}))
        self.assertEqual(response.status_code, 200)
        self.assertIn('personagem', response.context)
        self.assertEqual(response.context['personagem'], self.personagem)
        
    def test_nao_mostrar_vitorias_nao_validadas(self):
        """Testa se top 5 não está preenchido pois desafio nao foi validado"""
        validar_desafio_ladder_teste(self.desafio, self.jogador_2)
        response = self.client.get(reverse('personagens:detalhar_personagem_por_id', kwargs={'personagem_id': self.personagem.id}))
        
        self.assertFalse(hasattr(response.context['personagem'], 'top_5_ganhadores')
        
    def test_mostrar_top_5_vitorias(self):
        """Testa se tela mostra corretamente top 5 vitórias de jogadores com o personagem"""
        validar_desafio_ladder_teste(self.desafio, self.jogador_2)
        response = self.client.get(reverse('personagens:detalhar_personagem_por_id', kwargs={'personagem_id': self.personagem.id}))
        
        self.assertTrue(hasattr(response.context['personagem'], 'top_5_ganhadores')
        self.assertEqual(response.context['personagem'].top_5_ganhadores, {'luta__ganhador': self.jogador_1, 'qtd_vitorias': 3})
        
        
        