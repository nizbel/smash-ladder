# -*- coding: utf-8 -*-
"""Testes para a view de adicionar desafio para ladder no formato completo"""
import datetime

from django.contrib.messages.api import get_messages
from django.test.testcases import TestCase
from django.urls.base import reverse
from django.utils import timezone

from jogadores.models import Jogador, Personagem, StageValidaLadder
from jogadores.tests.utils_teste import criar_jogadores_teste, SENHA_TESTE, \
    criar_stage_teste, criar_personagens_teste, criar_jogador_teste
from ladder.models import DesafioLadder, PosicaoLadder, HistoricoLadder, Luta, \
    LutaLadder, JogadorLuta
from ladder.tests.utils_teste import criar_ladder_teste, \
    criar_ladder_historico_teste, gerar_campos_formset
from ladder.views import MENSAGEM_SUCESSO_ADD_DESAFIO_LADDER
from smashLadder import settings
from smashLadder.utils import mes_ano_ant


class ViewAddDesafioLadderTestCase(TestCase):
    """TestCase da view de adicionar desafio de ladder"""
    @classmethod
    def setUpTestData(cls):
        super(ViewAddDesafioLadderTestCase, cls).setUpTestData()
        
        # Configurar jogadores
        criar_jogadores_teste()
        cls.sena = Jogador.objects.get(nick='sena')
        cls.teets = Jogador.objects.get(nick='teets')
        cls.mad = Jogador.objects.get(nick='mad')
        
        # Jogadores fora da ladder
        cls.new_1 = criar_jogador_teste('new1')
        cls.new_2 = criar_jogador_teste('new2')
        
        # Stage
        cls.stage = criar_stage_teste()
        # Configurar stage como válida
        StageValidaLadder.objects.create(stage=cls.stage)
        
        # Personagens
        criar_personagens_teste()   
        cls.marth = Personagem.objects.get(nome='Marth')
        cls.fox = Personagem.objects.get(nome='Fox')     
        
        # Criar ladders para verificar que adicionar desafio não as afeta
        criar_ladder_teste()
        
        # Preparar mês anterior para histórico
        data_atual = timezone.now().date()
        cls.mes, cls.ano = mes_ano_ant(data_atual.month, data_atual.year)
        
        criar_ladder_historico_teste(cls.ano, cls.mes)
        
    def test_acesso_deslogado(self):
        """Testa acesso a tela de adicionar desafio de ladder sem logar"""
        response = self.client.get(reverse('ladder:adicionar_desafio_ladder'))
        self.assertEqual(response.status_code, 302)
        
        url_esperada = settings.LOGIN_URL + '?next=' + reverse('ladder:adicionar_desafio_ladder')
        self.assertRedirects(response, url_esperada)
        
    def test_acesso_logado(self):
        """Testa acesso a tela de adicionar desafio de ladder logado"""
        self.client.login(username=self.sena.user.username, password=SENHA_TESTE)
        response = self.client.get(reverse('ladder:adicionar_desafio_ladder'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('form_desafio_ladder', response.context)
        
        
    def test_adicionar_desafio_sucesso_sem_preencher_lutas(self):
        """Testa adicionar desafio de ladder com sucesso, sem preencher lutas"""
        # Garantir que não existe desafio de ladder
        self.assertEqual(DesafioLadder.objects.count(), 0)
         
        horario_atual = datetime.datetime.now()
        self.client.login(username=self.sena.user.username, password=SENHA_TESTE)
        
        # Preencher form e formset para enviar no POST
        form = {'desafiante': self.sena.id, 'desafiado': self.teets.id, 'score_desafiante': 3, 'score_desafiado': 2, 
                                      'desafio_coringa': False, 'data_hora': horario_atual}
        
        formset_lutas = gerar_campos_formset([{'ganhador': '', 'stage': '', 
                                     'personagem_desafiante': '', 'personagem_desafiado': ''},
                                    {'ganhador': '', 'stage': '', 
                                     'personagem_desafiante': '', 'personagem_desafiado': ''},
                                    {'ganhador': '', 'stage': '', 
                                     'personagem_desafiante': '', 'personagem_desafiado': ''},
                                    {'ganhador': '', 'stage': '', 
                                     'personagem_desafiante': '', 'personagem_desafiado': ''},
                                    {'ganhador': '', 'stage': '', 
                                     'personagem_desafiante': '', 'personagem_desafiado': ''}], 'desafio_ladder_luta')
        
        dados_post = {**form, **formset_lutas}
        
        response = self.client.post(reverse('ladder:adicionar_desafio_ladder'), 
                                    dados_post)
        self.assertEqual(response.status_code, 302)
         
        desafio_criado_id = DesafioLadder.objects.get(desafiante=self.sena, desafiado=self.teets).id
        url_esperada = reverse('ladder:detalhar_desafio_ladder', kwargs={'desafio_id': desafio_criado_id})
        self.assertRedirects(response, url_esperada)
         
        # Verificar mensagens
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), MENSAGEM_SUCESSO_ADD_DESAFIO_LADDER)
         
        # Testar valores para desafio de ladder criado
        self.assertEqual(DesafioLadder.objects.count(), 1)
        desafio_ladder = DesafioLadder.objects.get(desafiante=self.sena, desafiado=self.teets)
        self.assertEqual(desafio_ladder.data_hora, timezone.make_aware(horario_atual))
        self.assertEqual(desafio_ladder.score_desafiante, 3)
        self.assertEqual(desafio_ladder.score_desafiado, 2)
        self.assertEqual(desafio_ladder.desafio_coringa, False)
        self.assertEqual(desafio_ladder.adicionado_por, self.sena)
        
        self.assertEqual(Luta.objects.count(), 0)
         
         
#     def test_add_desafio_nao_altera_ladder_atual(self):
#         """Testa se adicionar desafio de ladder não altera posições atuais"""
#         posicoes_antes = PosicaoLadder.objects.all().order_by('posicao')
#          
#         self.client.login(username=self.sena.user.username, password=SENHA_TESTE)
#         response = self.client.post(reverse('ladder:adicionar_desafio_ladder'), 
#                                     {'desafiante': self.sena.id, 'desafiado': self.teets.id, 'score_desafiante': 3, 'score_desafiado': 2, 
#                                      'desafio_coringa': False, 'data_hora': datetime.datetime.now()})
#         self.assertEqual(response.status_code, 302)
#          
#         posicoes_depois = PosicaoLadder.objects.all().order_by('posicao')
#          
#         self.assertEqual(len(posicoes_antes), len(posicoes_depois))
#         for posicao_antes, posicao_depois in zip(posicoes_antes, posicoes_depois):
#             self.assertEqual(posicao_antes, posicao_depois)
#      
#     def test_add_desafio_nao_altera_ladder_historica(self):
#         """Testa se adicionar desafio de ladder não altera posições históricas"""
#         posicoes_antes = HistoricoLadder.objects.filter(ano=self.ano, mes=self.mes).order_by('posicao')
#          
#         self.client.login(username=self.sena.user.username, password=SENHA_TESTE)
#         response = self.client.post(reverse('ladder:adicionar_desafio_ladder'), 
#                                     {'desafiante': self.sena.id, 'desafiado': self.teets.id, 'score_desafiante': 3, 'score_desafiado': 2, 
#                                      'desafio_coringa': False, 'data_hora': datetime.datetime.now().replace(year=self.ano, month=self.mes)})
#         self.assertEqual(response.status_code, 302)
#          
#         posicoes_depois = HistoricoLadder.objects.filter(ano=self.ano, mes=self.mes).order_by('posicao')
#          
#         self.assertEqual(len(posicoes_antes), len(posicoes_depois))
#         for posicao_antes, posicao_depois in zip(posicoes_antes, posicoes_depois):
#             self.assertEqual(posicao_antes, posicao_depois)
#              
#     def test_erro_na_adicao_informado_pelo_messages(self):
#         """Testa se aparece mensagem no contexto messages caso haja erro na adição"""
#         self.client.login(username=self.sena.user.username, password=SENHA_TESTE)
#         response = self.client.post(reverse('ladder:adicionar_desafio_ladder'), 
#                                     {'desafiante': self.sena.id, 'desafiado': self.teets.id, 'score_desafiante': 2, 'score_desafiado': 1, 
#                                      'desafio_coringa': False, 'data_hora': datetime.datetime.now()})
#         self.assertEqual(response.status_code, 200)
#          
#         # Verificar erros
#         self.assertContains(response, 'Resultado impossível para melhor de 5')


        
    def test_adicionar_desafio_sucesso_preenchendo_lutas(self):
        """Testa adicionar desafio de ladder com sucesso preenchendo todas as lutas"""
        # Garantir que não existe desafio de ladder nem lutas
        self.assertEqual(DesafioLadder.objects.count(), 0)
        self.assertEqual(Luta.objects.count(), 0)
        
        horario_atual = datetime.datetime.now()
        self.client.login(username=self.sena.user.username, password=SENHA_TESTE)
        
        form = {'desafiante': self.sena.id, 'desafiado': self.teets.id, 'score_desafiante': 3, 'score_desafiado': 2, 
                                      'desafio_coringa': False, 'data_hora': horario_atual}
        
        formset_lutas = gerar_campos_formset([{'ganhador': self.sena.id, 'stage': self.stage.id, 
                                     'personagem_desafiante': self.fox.id, 'personagem_desafiado': self.fox.id},
                                    {'ganhador': self.sena.id, 'stage': self.stage.id, 
                                     'personagem_desafiante': self.marth.id, 'personagem_desafiado': self.fox.id},
                                    {'ganhador': self.teets.id, 'stage': self.stage.id, 
                                     'personagem_desafiante': self.fox.id, 'personagem_desafiado': self.marth.id},
                                    {'ganhador': self.teets.id, 'stage': self.stage.id, 
                                     'personagem_desafiante': self.marth.id, 'personagem_desafiado': self.marth.id},
                                    {'ganhador': self.sena.id, 'stage': self.stage.id, 
                                     'personagem_desafiante': self.marth.id, 'personagem_desafiado': self.fox.id}], 'desafio_ladder_luta')
        
        dados_post = {**form, **formset_lutas}
        
        response = self.client.post(reverse('ladder:adicionar_desafio_ladder'), 
                                    dados_post)
        self.assertEqual(response.status_code, 302)
        
        desafio_criado_id = DesafioLadder.objects.get(desafiante=self.sena, desafiado=self.teets).id
        url_esperada = reverse('ladder:detalhar_desafio_ladder', kwargs={'desafio_id': desafio_criado_id})
        self.assertRedirects(response, url_esperada)
        
        # Verificar mensagens
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), MENSAGEM_SUCESSO_ADD_DESAFIO_LADDER)
        
        # Testar valores para desafio de ladder criado
        self.assertEqual(DesafioLadder.objects.count(), 1)
        desafio_ladder = DesafioLadder.objects.get(desafiante=self.sena, desafiado=self.teets)
        self.assertEqual(desafio_ladder.data_hora, timezone.make_aware(horario_atual))
        self.assertEqual(desafio_ladder.score_desafiante, 3)
        self.assertEqual(desafio_ladder.score_desafiado, 2)
        self.assertEqual(desafio_ladder.desafio_coringa, False)
        self.assertEqual(desafio_ladder.adicionado_por, self.sena)
        
        # Testar desafios de lutas criados
        self.assertEqual(Luta.objects.count(), 5)
        self.assertEqual(JogadorLuta.objects.count(), 10)
        self.assertEqual(LutaLadder.objects.count(), 5)
        
        lutas = desafio_ladder.lutaladder_set.all()
        self.assertEqual(lutas.count(), 5)
        
        # Luta 1
        luta_1 = lutas.get(indice_desafio_ladder=1).luta
        self.assertEqual(luta_1.ganhador, self.sena)
        self.assertEqual(luta_1.stage, self.stage)
        self.assertEqual(luta_1.data, desafio_ladder.data_hora.date())
        self.assertEqual(luta_1.jogadorluta_set.all().count(), 2)
        self.assertIn((self.sena.id, self.fox.id), luta_1.jogadorluta_set.all().values_list('jogador', 'personagem'))
        self.assertIn((self.teets.id, self.fox.id), luta_1.jogadorluta_set.all().values_list('jogador', 'personagem'))
        
        # Luta 2
        luta_2 = lutas.get(indice_desafio_ladder=2).luta
        self.assertEqual(luta_2.ganhador, self.sena)
        self.assertEqual(luta_2.stage, self.stage)
        self.assertEqual(luta_2.data, desafio_ladder.data_hora.date())
        self.assertEqual(luta_2.jogadorluta_set.all().count(), 2)
        self.assertIn((self.sena.id, self.marth.id), luta_2.jogadorluta_set.all().values_list('jogador', 'personagem'))
        self.assertIn((self.teets.id, self.fox.id), luta_2.jogadorluta_set.all().values_list('jogador', 'personagem'))
        
        # Luta 3
        luta_3 = lutas.get(indice_desafio_ladder=3).luta
        self.assertEqual(luta_3.ganhador, self.teets)
        self.assertEqual(luta_3.stage, self.stage)
        self.assertEqual(luta_3.data, desafio_ladder.data_hora.date())
        self.assertEqual(luta_3.jogadorluta_set.all().count(), 2)
        self.assertIn((self.sena.id, self.fox.id), luta_3.jogadorluta_set.all().values_list('jogador', 'personagem'))
        self.assertIn((self.teets.id, self.marth.id), luta_3.jogadorluta_set.all().values_list('jogador', 'personagem'))
        
        # Luta 4
        luta_4 = lutas.get(indice_desafio_ladder=4).luta
        self.assertEqual(luta_4.ganhador, self.teets)
        self.assertEqual(luta_4.stage, self.stage)
        self.assertEqual(luta_4.data, desafio_ladder.data_hora.date())
        self.assertEqual(luta_4.jogadorluta_set.all().count(), 2)
        self.assertIn((self.sena.id, self.marth.id), luta_4.jogadorluta_set.all().values_list('jogador', 'personagem'))
        self.assertIn((self.teets.id, self.marth.id), luta_4.jogadorluta_set.all().values_list('jogador', 'personagem'))
        
        # Luta 5
        luta_5 = lutas.get(indice_desafio_ladder=5).luta
        self.assertEqual(luta_5.ganhador, self.sena)
        self.assertEqual(luta_5.stage, self.stage)
        self.assertEqual(luta_5.data, desafio_ladder.data_hora.date())
        self.assertEqual(luta_5.jogadorluta_set.all().count(), 2)
        self.assertIn((self.sena.id, self.marth.id), luta_5.jogadorluta_set.all().values_list('jogador', 'personagem'))
        self.assertIn((self.teets.id, self.fox.id), luta_5.jogadorluta_set.all().values_list('jogador', 'personagem'))
        
    def test_adicionar_desafio_sucesso_preenchendo_algumas_lutas(self):
        """Testa adicionar desafio de ladder com sucesso preenchendo algumas lutas"""
        # Garantir que não existe desafio de ladder nem lutas
        self.assertEqual(DesafioLadder.objects.count(), 0)
        self.assertEqual(Luta.objects.count(), 0)
        
        horario_atual = datetime.datetime.now()
        self.client.login(username=self.sena.user.username, password=SENHA_TESTE)
        
        form = {'desafiante': self.sena.id, 'desafiado': self.teets.id, 'score_desafiante': 3, 'score_desafiado': 2, 
                                      'desafio_coringa': False, 'data_hora': horario_atual}
        
        formset_lutas = gerar_campos_formset([{'ganhador': self.sena.id, 'stage': self.stage.id, 
                                     'personagem_desafiante': self.fox.id, 'personagem_desafiado': self.fox.id},
                                    {'ganhador': self.sena.id, 'stage': self.stage.id, 
                                     'personagem_desafiante': self.marth.id, 'personagem_desafiado': self.fox.id},
                                    {'ganhador': '', 'stage': '', 
                                     'personagem_desafiante': '', 'personagem_desafiado': ''},
                                    {'ganhador': self.teets.id, 'stage': self.stage.id, 
                                     'personagem_desafiante': self.marth.id, 'personagem_desafiado': self.marth.id},
                                    {'ganhador': '', 'stage': '', 
                                     'personagem_desafiante': '', 'personagem_desafiado': ''}], 'desafio_ladder_luta')
        
        dados_post = {**form, **formset_lutas}
        
        response = self.client.post(reverse('ladder:adicionar_desafio_ladder'), 
                                    dados_post)
        self.assertEqual(response.status_code, 302)
        
        desafio_criado_id = DesafioLadder.objects.get(desafiante=self.sena, desafiado=self.teets).id
        url_esperada = reverse('ladder:detalhar_desafio_ladder', kwargs={'desafio_id': desafio_criado_id})
        self.assertRedirects(response, url_esperada)
        
        # Verificar mensagens
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), MENSAGEM_SUCESSO_ADD_DESAFIO_LADDER)
        
        # Testar valores para desafio de ladder criado
        self.assertEqual(DesafioLadder.objects.count(), 1)
        desafio_ladder = DesafioLadder.objects.get(desafiante=self.sena, desafiado=self.teets)
        self.assertEqual(desafio_ladder.data_hora, timezone.make_aware(horario_atual))
        self.assertEqual(desafio_ladder.score_desafiante, 3)
        self.assertEqual(desafio_ladder.score_desafiado, 2)
        self.assertEqual(desafio_ladder.desafio_coringa, False)
        self.assertEqual(desafio_ladder.adicionado_por, self.sena)
        
        # Testar desafios de lutas criados
        self.assertEqual(Luta.objects.count(), 3)
        self.assertEqual(JogadorLuta.objects.count(), 6)
        self.assertEqual(LutaLadder.objects.count(), 3)
        
        lutas = desafio_ladder.lutaladder_set.all()
        self.assertEqual(lutas.count(), 3)
        
        # Luta 1
        luta_1 = lutas.get(indice_desafio_ladder=1).luta
        self.assertEqual(luta_1.ganhador, self.sena)
        self.assertEqual(luta_1.stage, self.stage)
        self.assertEqual(luta_1.data, desafio_ladder.data_hora.date())
        self.assertEqual(luta_1.jogadorluta_set.all().count(), 2)
        self.assertIn((self.sena.id, self.fox.id), luta_1.jogadorluta_set.all().values_list('jogador', 'personagem'))
        self.assertIn((self.teets.id, self.fox.id), luta_1.jogadorluta_set.all().values_list('jogador', 'personagem'))
        
        # Luta 2
        luta_2 = lutas.get(indice_desafio_ladder=2).luta
        self.assertEqual(luta_2.ganhador, self.sena)
        self.assertEqual(luta_2.stage, self.stage)
        self.assertEqual(luta_2.data, desafio_ladder.data_hora.date())
        self.assertEqual(luta_2.jogadorluta_set.all().count(), 2)
        self.assertIn((self.sena.id, self.marth.id), luta_2.jogadorluta_set.all().values_list('jogador', 'personagem'))
        self.assertIn((self.teets.id, self.fox.id), luta_2.jogadorluta_set.all().values_list('jogador', 'personagem'))
        
        # Luta 3
        self.assertFalse(lutas.filter(indice_desafio_ladder=3).exists())
        
        # Luta 4
        luta_4 = lutas.get(indice_desafio_ladder=4).luta
        self.assertEqual(luta_4.ganhador, self.teets)
        self.assertEqual(luta_4.stage, self.stage)
        self.assertEqual(luta_4.data, desafio_ladder.data_hora.date())
        self.assertEqual(luta_4.jogadorluta_set.all().count(), 2)
        self.assertIn((self.sena.id, self.marth.id), luta_4.jogadorluta_set.all().values_list('jogador', 'personagem'))
        self.assertIn((self.teets.id, self.marth.id), luta_4.jogadorluta_set.all().values_list('jogador', 'personagem'))
        
        # Luta 5
        self.assertFalse(lutas.filter(indice_desafio_ladder=5).exists())
        
        # Verificar que ao editar índice das lutas no desafio de ladder é respeitado
        response = self.client.get(reverse('ladder:editar_desafio_ladder', kwargs={'desafio_id': desafio_criado_id}))
        
        valores_iniciais_formset = response.context['formset_lutas'].initial
        self.assertIn('id', valores_iniciais_formset[0])
        self.assertIn('id', valores_iniciais_formset[1])
        self.assertEqual(valores_iniciais_formset[2], {})
        self.assertIn('id', valores_iniciais_formset[3])
        self.assertEqual(valores_iniciais_formset[4], {})
        
        
    def test_add_desafio_nao_altera_ladder_atual(self):
        """Testa se adicionar desafio de ladder não altera posições atuais"""
        posicoes_antes = PosicaoLadder.objects.all().order_by('posicao')
        
        self.client.login(username=self.sena.user.username, password=SENHA_TESTE)
        
        form = {'desafiante': self.sena.id, 'desafiado': self.teets.id, 'score_desafiante': 3, 'score_desafiado': 2, 
                                     'desafio_coringa': False, 'data_hora': datetime.datetime.now()}
        
        formset_lutas = gerar_campos_formset([{'ganhador': self.sena.id, 'stage': self.stage.id, 
                                     'personagem_desafiante': self.fox.id, 'personagem_desafiado': self.fox.id},
                                    {'ganhador': self.sena.id, 'stage': self.stage.id, 
                                     'personagem_desafiante': self.marth.id, 'personagem_desafiado': self.fox.id},
                                    {'ganhador': self.teets.id, 'stage': self.stage.id, 
                                     'personagem_desafiante': self.fox.id, 'personagem_desafiado': self.marth.id},
                                    {'ganhador': self.teets.id, 'stage': self.stage.id, 
                                     'personagem_desafiante': self.marth.id, 'personagem_desafiado': self.marth.id},
                                    {'ganhador': self.sena.id, 'stage': self.stage.id, 
                                     'personagem_desafiante': self.marth.id, 'personagem_desafiado': self.fox.id}], 'desafio_ladder_luta')
        
        response = self.client.post(reverse('ladder:adicionar_desafio_ladder'), 
                                    {**form, **formset_lutas})
        self.assertEqual(response.status_code, 302)
        
        posicoes_depois = PosicaoLadder.objects.all().order_by('posicao')
        
        self.assertEqual(len(posicoes_antes), len(posicoes_depois))
        for posicao_antes, posicao_depois in zip(posicoes_antes, posicoes_depois):
            self.assertEqual(posicao_antes, posicao_depois)
    
    def test_add_desafio_nao_altera_ladder_historica(self):
        """Testa se adicionar desafio de ladder não altera posições históricas"""
        posicoes_antes = HistoricoLadder.objects.filter(ano=self.ano, mes=self.mes).order_by('posicao')
        
        self.client.login(username=self.sena.user.username, password=SENHA_TESTE)
        
        form = {'desafiante': self.sena.id, 'desafiado': self.teets.id, 'score_desafiante': 3, 'score_desafiado': 2, 
                                     'desafio_coringa': False, 'data_hora': datetime.datetime.now().replace(year=self.ano, month=self.mes)}
        
        formset_lutas = gerar_campos_formset([{'ganhador': self.sena.id, 'stage': self.stage.id, 
                                     'personagem_desafiante': self.fox.id, 'personagem_desafiado': self.fox.id},
                                    {'ganhador': self.sena.id, 'stage': self.stage.id, 
                                     'personagem_desafiante': self.marth.id, 'personagem_desafiado': self.fox.id},
                                    {'ganhador': self.teets.id, 'stage': self.stage.id, 
                                     'personagem_desafiante': self.fox.id, 'personagem_desafiado': self.marth.id},
                                    {'ganhador': self.teets.id, 'stage': self.stage.id, 
                                     'personagem_desafiante': self.marth.id, 'personagem_desafiado': self.marth.id},
                                    {'ganhador': self.sena.id, 'stage': self.stage.id, 
                                     'personagem_desafiante': self.marth.id, 'personagem_desafiado': self.fox.id}], 'desafio_ladder_luta')
        
        response = self.client.post(reverse('ladder:adicionar_desafio_ladder'), 
                                    {**form, **formset_lutas})
        self.assertEqual(response.status_code, 302)
        
        posicoes_depois = HistoricoLadder.objects.filter(ano=self.ano, mes=self.mes).order_by('posicao')
        
        self.assertEqual(len(posicoes_antes), len(posicoes_depois))
        for posicao_antes, posicao_depois in zip(posicoes_antes, posicoes_depois):
            self.assertEqual(posicao_antes, posicao_depois)
            
    def test_sucesso_mesmo_com_stage_personagem_vazios(self):
        """Testa se houve sucesso na adição mesmo não preenchendo campos de personagem e stage"""
        # Garantir que não existe desafio de ladder nem lutas
        self.assertEqual(DesafioLadder.objects.count(), 0)
        self.assertEqual(Luta.objects.count(), 0)
        
        horario_atual = datetime.datetime.now()
        self.client.login(username=self.sena.user.username, password=SENHA_TESTE)
        
        form = {'desafiante': self.sena.id, 'desafiado': self.teets.id, 'score_desafiante': 3, 'score_desafiado': 2, 
                                      'desafio_coringa': False, 'data_hora': horario_atual}
        
        formset_lutas = gerar_campos_formset([{'ganhador': self.sena.id, 'stage': self.stage.id, 
                                     'personagem_desafiante': '', 'personagem_desafiado': ''},
                                    {'ganhador': self.sena.id, 'stage': self.stage.id, 
                                     'personagem_desafiante': self.marth.id, 'personagem_desafiado': self.fox.id},
                                    {'ganhador': self.teets.id, 'stage': '', 
                                     'personagem_desafiante': self.fox.id, 'personagem_desafiado': ''},
                                    {'ganhador': self.teets.id, 'stage': self.stage.id, 
                                     'personagem_desafiante': '', 'personagem_desafiado': self.marth.id},
                                    {'ganhador': self.sena.id, 'stage': '', 
                                     'personagem_desafiante': self.marth.id, 'personagem_desafiado': self.fox.id}], 'desafio_ladder_luta')
        
        response = self.client.post(reverse('ladder:adicionar_desafio_ladder'), 
                                    {**form, **formset_lutas})
        self.assertEqual(response.status_code, 302)
        
        desafio_criado_id = DesafioLadder.objects.get(desafiante=self.sena, desafiado=self.teets).id
        url_esperada = reverse('ladder:detalhar_desafio_ladder', kwargs={'desafio_id': desafio_criado_id})
        self.assertRedirects(response, url_esperada)
        
        # Verificar mensagens
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), MENSAGEM_SUCESSO_ADD_DESAFIO_LADDER)
        
        # Testar valores para desafio de ladder criado
        self.assertEqual(DesafioLadder.objects.count(), 1)
        desafio_ladder = DesafioLadder.objects.get(desafiante=self.sena, desafiado=self.teets)
        self.assertEqual(desafio_ladder.data_hora, timezone.make_aware(horario_atual))
        self.assertEqual(desafio_ladder.score_desafiante, 3)
        self.assertEqual(desafio_ladder.score_desafiado, 2)
        self.assertEqual(desafio_ladder.desafio_coringa, False)
        self.assertEqual(desafio_ladder.adicionado_por, self.sena)
        
        # Testar desafios de lutas criados
        self.assertEqual(Luta.objects.count(), 5)
        self.assertEqual(JogadorLuta.objects.count(), 10)
        self.assertEqual(LutaLadder.objects.count(), 5)
        
        lutas = desafio_ladder.lutaladder_set.all()
        self.assertEqual(lutas.count(), 5)
        
        # Luta 1
        luta_1 = lutas.get(indice_desafio_ladder=1).luta
        self.assertEqual(luta_1.ganhador, self.sena)
        self.assertEqual(luta_1.stage, self.stage)
        self.assertEqual(luta_1.data, desafio_ladder.data_hora.date())
        self.assertEqual(luta_1.jogadorluta_set.all().count(), 2)
        self.assertIn((self.sena.id, None), luta_1.jogadorluta_set.all().values_list('jogador', 'personagem'))
        self.assertIn((self.teets.id, None), luta_1.jogadorluta_set.all().values_list('jogador', 'personagem'))
        
        # Luta 2
        luta_2 = lutas.get(indice_desafio_ladder=2).luta
        self.assertEqual(luta_2.ganhador, self.sena)
        self.assertEqual(luta_2.stage, self.stage)
        self.assertEqual(luta_2.data, desafio_ladder.data_hora.date())
        self.assertEqual(luta_2.jogadorluta_set.all().count(), 2)
        self.assertIn((self.sena.id, self.marth.id), luta_2.jogadorluta_set.all().values_list('jogador', 'personagem'))
        self.assertIn((self.teets.id, self.fox.id), luta_2.jogadorluta_set.all().values_list('jogador', 'personagem'))
        
        # Luta 3
        luta_3 = lutas.get(indice_desafio_ladder=3).luta
        self.assertEqual(luta_3.ganhador, self.teets)
        self.assertEqual(luta_3.stage, None)
        self.assertEqual(luta_3.data, desafio_ladder.data_hora.date())
        self.assertEqual(luta_3.jogadorluta_set.all().count(), 2)
        self.assertIn((self.sena.id, self.fox.id), luta_3.jogadorluta_set.all().values_list('jogador', 'personagem'))
        self.assertIn((self.teets.id, None), luta_3.jogadorluta_set.all().values_list('jogador', 'personagem'))
        
        # Luta 4
        luta_4 = lutas.get(indice_desafio_ladder=4).luta
        self.assertEqual(luta_4.ganhador, self.teets)
        self.assertEqual(luta_4.stage, self.stage)
        self.assertEqual(luta_4.data, desafio_ladder.data_hora.date())
        self.assertEqual(luta_4.jogadorluta_set.all().count(), 2)
        self.assertIn((self.sena.id, None), luta_4.jogadorluta_set.all().values_list('jogador', 'personagem'))
        self.assertIn((self.teets.id, self.marth.id), luta_4.jogadorluta_set.all().values_list('jogador', 'personagem'))
        
        # Luta 5
        luta_5 = lutas.get(indice_desafio_ladder=5).luta
        self.assertEqual(luta_5.ganhador, self.sena)
        self.assertEqual(luta_5.stage, None)
        self.assertEqual(luta_5.data, desafio_ladder.data_hora.date())
        self.assertEqual(luta_5.jogadorluta_set.all().count(), 2)
        self.assertIn((self.sena.id, self.marth.id), luta_5.jogadorluta_set.all().values_list('jogador', 'personagem'))
        self.assertIn((self.teets.id, self.fox.id), luta_5.jogadorluta_set.all().values_list('jogador', 'personagem'))
        
    def test_erro_na_adicao_informado_pelo_messages(self):
        """Testa se aparece mensagem no contexto messages caso haja erro na adição"""
        self.client.login(username=self.sena.user.username, password=SENHA_TESTE)
        
        form = {'desafiante': self.sena.id, 'desafiado': self.teets.id, 'score_desafiante': 2, 'score_desafiado': 1, 
                                     'desafio_coringa': False, 'data_hora': datetime.datetime.now()}
        
        formset_lutas = gerar_campos_formset([{'ganhador': self.sena.id, 'stage': self.stage.id, 
                                     'personagem_desafiante': self.fox.id, 'personagem_desafiado': self.fox.id},
                                    {'ganhador': self.sena.id, 'stage': self.stage.id, 
                                     'personagem_desafiante': self.marth.id, 'personagem_desafiado': self.fox.id},
                                    {'ganhador': self.teets.id, 'stage': self.stage.id, 
                                     'personagem_desafiante': self.fox.id, 'personagem_desafiado': self.marth.id},
                                    {'ganhador': self.teets.id, 'stage': self.stage.id, 
                                     'personagem_desafiante': self.marth.id, 'personagem_desafiado': self.marth.id},
                                    {'ganhador': self.sena.id, 'stage': self.stage.id, 
                                     'personagem_desafiante': self.marth.id, 'personagem_desafiado': self.fox.id}], 'desafio_ladder_luta')
        
        response = self.client.post(reverse('ladder:adicionar_desafio_ladder'), 
                                    {**form, **formset_lutas})
        self.assertEqual(response.status_code, 200)
        
        # Verificar erros
        self.assertContains(response, 'Resultado impossível para melhor de 5')
        
    def test_erro_luta_ganhador_nao_participante(self):
        """Testar erro para ganhador em uma luta não estar entre participantes"""
        horario_atual = datetime.datetime.now()
        self.client.login(username=self.sena.user.username, password=SENHA_TESTE)
        
        form = {'desafiante': self.sena.id, 'desafiado': self.teets.id, 'score_desafiante': 3, 'score_desafiado': 2, 
                                      'desafio_coringa': False, 'data_hora': horario_atual}
        
        formset_lutas = gerar_campos_formset([{'ganhador': self.sena.id, 'stage': self.stage.id, 
                                     'personagem_desafiante': self.fox.id, 'personagem_desafiado': self.fox.id},
                                    {'ganhador': self.sena.id, 'stage': self.stage.id, 
                                     'personagem_desafiante': self.marth.id, 'personagem_desafiado': self.fox.id},
                                    {'ganhador': self.teets.id, 'stage': self.stage.id, 
                                     'personagem_desafiante': self.fox.id, 'personagem_desafiado': self.marth.id},
                                    {'ganhador': self.mad.id, 'stage': self.stage.id, 
                                     'personagem_desafiante': self.marth.id, 'personagem_desafiado': self.marth.id},
                                    {'ganhador': self.sena.id, 'stage': self.stage.id, 
                                     'personagem_desafiante': self.marth.id, 'personagem_desafiado': self.fox.id}], 'desafio_ladder_luta')
        
        response = self.client.post(reverse('ladder:adicionar_desafio_ladder'), 
                                    {**form, **formset_lutas})
        self.assertEqual(response.status_code, 200)
        
        # Verificar erro na mensagem
        messages = list(response.context['messages'])
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), 'Luta 4 indica ganhador que não está entre os participantes')
        
    def test_erro_ganhadores_por_luta_nao_reflete_resultado(self):
        """Testar erro para ganhadores apontados por luta não bater com resultado da partida"""
        horario_atual = datetime.datetime.now()
        self.client.login(username=self.sena.user.username, password=SENHA_TESTE)
        
        form = {'desafiante': self.sena.id, 'desafiado': self.teets.id, 'score_desafiante': 3, 'score_desafiado': 2, 
                                      'desafio_coringa': False, 'data_hora': horario_atual}
        
        formset_lutas = gerar_campos_formset([{'ganhador': self.sena.id, 'stage': self.stage.id, 
                                     'personagem_desafiante': self.fox.id, 'personagem_desafiado': self.fox.id},
                                    {'ganhador': self.sena.id, 'stage': self.stage.id, 
                                     'personagem_desafiante': self.marth.id, 'personagem_desafiado': self.fox.id},
                                    {'ganhador': self.sena.id, 'stage': self.stage.id, 
                                     'personagem_desafiante': self.fox.id, 'personagem_desafiado': self.marth.id},
                                    {'ganhador': self.teets.id, 'stage': self.stage.id, 
                                     'personagem_desafiante': self.marth.id, 'personagem_desafiado': self.marth.id},
                                    {'ganhador': self.sena.id, 'stage': self.stage.id, 
                                     'personagem_desafiante': self.marth.id, 'personagem_desafiado': self.fox.id}], 'desafio_ladder_luta')
        
        response = self.client.post(reverse('ladder:adicionar_desafio_ladder'), 
                                    {**form, **formset_lutas})
        self.assertEqual(response.status_code, 200)
        
        # Verificar erro na mensagem
        messages = list(response.context['messages'])
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), 'Resultado geral informado é incompatível com resultados das lutas')
        
    def test_adicionar_desafio_todos_fora_ladder(self):
        """Testa adicionar desafio de ladder para 2 jogadores não participantes da ladder, com sucesso"""
        # Garantir que não existe desafio de ladder
        self.assertEqual(DesafioLadder.objects.count(), 0)
         
        horario_atual = datetime.datetime.now()
        self.client.login(username=self.new_1.user.username, password=SENHA_TESTE)
        
        # Preencher form e formset para enviar no POST
        form = {'desafiante': self.new_1.id, 'desafiado': self.new_2.id, 'score_desafiante': 3, 'score_desafiado': 2, 
                                      'desafio_coringa': False, 'data_hora': horario_atual}
        
        formset_lutas = gerar_campos_formset([{'ganhador': '', 'stage': '', 
                                     'personagem_desafiante': '', 'personagem_desafiado': ''},
                                    {'ganhador': '', 'stage': '', 
                                     'personagem_desafiante': '', 'personagem_desafiado': ''},
                                    {'ganhador': '', 'stage': '', 
                                     'personagem_desafiante': '', 'personagem_desafiado': ''},
                                    {'ganhador': '', 'stage': '', 
                                     'personagem_desafiante': '', 'personagem_desafiado': ''},
                                    {'ganhador': '', 'stage': '', 
                                     'personagem_desafiante': '', 'personagem_desafiado': ''}], 'desafio_ladder_luta')
        
        dados_post = {**form, **formset_lutas}
        
        response = self.client.post(reverse('ladder:adicionar_desafio_ladder'), 
                                    dados_post)
        self.assertEqual(response.status_code, 302)
         
        desafio_criado_id = DesafioLadder.objects.get(desafiante=self.new_1, desafiado=self.new_2).id
        url_esperada = reverse('ladder:detalhar_desafio_ladder', kwargs={'desafio_id': desafio_criado_id})
        self.assertRedirects(response, url_esperada)
         
        # Verificar mensagens
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), MENSAGEM_SUCESSO_ADD_DESAFIO_LADDER)
         
        # Testar valores para desafio de ladder criado
        self.assertEqual(DesafioLadder.objects.count(), 1)
        desafio_ladder = DesafioLadder.objects.get(desafiante=self.new_1, desafiado=self.new_2)
        self.assertEqual(desafio_ladder.data_hora, timezone.make_aware(horario_atual))
        self.assertEqual(desafio_ladder.score_desafiante, 3)
        self.assertEqual(desafio_ladder.score_desafiado, 2)
        self.assertEqual(desafio_ladder.desafio_coringa, False)
        self.assertEqual(desafio_ladder.adicionado_por, self.new_1)
        
        self.assertEqual(Luta.objects.count(), 0)
    
        