# -*- coding: utf-8 -*-
from django.contrib.messages.api import get_messages
from django.test.testcases import TestCase
from django.urls.base import reverse
from django.utils import timezone

from jogadores.models import Jogador
from jogadores.tests.utils_teste import criar_jogadores_teste, \
    criar_personagens_teste, criar_stage_teste, criar_jogador_teste, SENHA_TESTE
from ladder.models import PosicaoLadder, DesafioLadder, HistoricoLadder
from ladder.tests.utils_teste import criar_ladder_teste, \
    criar_ladder_historico_teste, criar_desafio_ladder_simples_teste
from ladder.views import MENSAGEM_SUCESSO_VALIDAR_DESAFIO_LADDER
from smashLadder import settings


class ViewValidarDesafioLadderTestCase(TestCase):
    """Testes para a view de validar desafio de ladder"""
    @classmethod
    def setUpTestData(cls):
        super(ViewValidarDesafioLadderTestCase, cls).setUpTestData()
        
        # Jogadores
        criar_jogadores_teste()
        
        # Personagens e estágios
        criar_personagens_teste()
        criar_stage_teste()
        
        # Buscar jogadores a serem usados nos testes
        cls.sena = Jogador.objects.get(nick='sena')
        cls.teets = Jogador.objects.get(nick='teets')
        cls.mad = Jogador.objects.get(nick='mad')
        cls.saraiva = Jogador.objects.get(nick='saraiva')
        cls.tiovsky = Jogador.objects.get(nick='tiovsky') # Último lugar da ladder
        
        # Criar ladders
        cls.ladder_atual = criar_ladder_teste()
        
        # Preparar mês anterior para histórico
        data_atual = timezone.now().date()
        cls.ano = data_atual.year
        cls.mes = data_atual.month - 1
        if cls.mes == 0:
            cls.mes = 12
            cls.ano -= 1
        
        criar_ladder_historico_teste(cls.ano, cls.mes)
        
        # Criar desafios para ladder
        horario_atual = timezone.now().replace(day=15)
        horario_historico = horario_atual.replace(year=cls.ano, month=cls.mes)
        cls.desafio_ladder_simples = criar_desafio_ladder_simples_teste(cls.sena, cls.teets, 3, 1, 
                                                                          horario_atual.replace(hour=6), False, cls.sena)
        cls.desafio_ladder_simples_validado = criar_desafio_ladder_simples_teste(cls.sena, cls.teets, 3, 1, 
                                                                          horario_atual.replace(hour=7), False, cls.sena)
        cls.desafio_ladder_simples_validado.admin_validador = cls.saraiva
        cls.desafio_ladder_simples_validado.save()
        
        cls.desafio_ladder_simples_historico = criar_desafio_ladder_simples_teste(cls.sena, cls.teets, 3, 1, 
                                                                                    horario_historico.replace(hour=6), False, cls.sena)
#         cls.desafio_ladder_completo = criar_desafio_ladder_completo_teste(cls.sena, cls.teets, 1, 3, 
#                                                                            horario_atual.replace(day=5), False, cls.sena)
#         cls.desafio_ladder_completo_historico = criar_desafio_ladder_completo_teste(cls.sena, cls.teets, 3, 1, 
#                                                                                      horario_historico.replace(day=5), False, cls.sena)
        cls.desafio_ladder_coringa_derrota = criar_desafio_ladder_simples_teste(cls.mad, cls.teets, 2, 3, 
                                                                          horario_atual.replace(hour=10), True, cls.mad)
        cls.desafio_ladder_coringa_vitoria = criar_desafio_ladder_simples_teste(cls.mad, cls.teets, 3, 1, 
                                                                          horario_atual.replace(hour=11), True, cls.mad)

        # Adicionar novo entrante na ladder
        cls.new = criar_jogador_teste('new')
        cls.desafio_ladder_novo_entrante = criar_desafio_ladder_simples_teste(cls.new, cls.tiovsky, 3, 1, 
                                                                          horario_atual.replace(hour=8), False, cls.sena)
        
        
    def test_acesso_deslogado(self):
        """Testa acesso a tela de validação de desafio de ladder sem logar"""
        response = self.client.get(reverse('ladder:validar_desafio_ladder', kwargs={'desafio_id': self.desafio_ladder_simples.id}))
        self.assertEqual(response.status_code, 302)
        
        url_esperada = settings.LOGIN_URL + '?next=' + reverse('ladder:validar_desafio_ladder', kwargs={'desafio_id': self.desafio_ladder_simples.id})
        self.assertRedirects(response, url_esperada)
        
    def test_acesso_logado(self):
        """Testa acesso a tela de validação de desafio de ladder logado sem admin"""
        self.client.login(username=self.sena.user.username, password=SENHA_TESTE)
        response = self.client.get(reverse('ladder:validar_desafio_ladder', kwargs={'desafio_id': self.desafio_ladder_simples.id}))
        self.assertEqual(response.status_code, 403)
        
    def test_acesso_logado_admin(self):
        """Testa acesso a tela de validação de desafio de ladder sendo admin"""
        self.client.login(username=self.teets.user.username, password=SENHA_TESTE)
        response = self.client.get(reverse('ladder:validar_desafio_ladder', kwargs={'desafio_id': self.desafio_ladder_simples.id}))
        self.assertEqual(response.status_code, 200)
        
    def test_erro_desafio_inexistente(self):
        """Testa acesso a tela de validação de desafio de ladder sendo admin"""
        desafio_inexistente_id = 1
        self.client.login(username=self.teets.user.username, password=SENHA_TESTE)
        response = self.client.get(reverse('ladder:validar_desafio_ladder', kwargs={'desafio_id': desafio_inexistente_id}))
        self.assertEqual(response.status_code, 404)
        
    def test_validar_desafio_sucesso_atual(self):
        """Testa validação de um desafio para ladder atual com sucesso"""
        # Verificar posições na ladder
        situacao_ladder_antes = PosicaoLadder.objects.all().order_by('posicao').values_list('jogador', 'posicao')
        self.assertIn((self.teets.id, 1), situacao_ladder_antes)
        self.assertIn((self.saraiva.id, 2), situacao_ladder_antes)
        self.assertIn((self.sena.id, 3), situacao_ladder_antes)
        self.assertIn((self.mad.id, 4), situacao_ladder_antes)
        
        self.client.login(username=self.saraiva.user.username, password=SENHA_TESTE)
        response = self.client.post(reverse('ladder:validar_desafio_ladder', kwargs={'desafio_id': self.desafio_ladder_simples.id}),
                                   {'salvar': 1})
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('ladder:detalhar_ladder_atual'))
        
        # Ver confirmação no messages
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), MENSAGEM_SUCESSO_VALIDAR_DESAFIO_LADDER)
        
        # Desafio deve ter validador
        self.desafio_ladder_simples = DesafioLadder.objects.get(id=self.desafio_ladder_simples.id)
        self.assertEqual(self.desafio_ladder_simples.admin_validador, self.saraiva)
        
        # Verificar alterações na ladder
        situacao_ladder_apos = PosicaoLadder.objects.all().order_by('posicao').values_list('jogador', 'posicao')
        self.assertIn((self.sena.id, 1), situacao_ladder_apos)
        self.assertIn((self.teets.id, 2), situacao_ladder_apos)
        self.assertIn((self.saraiva.id, 3), situacao_ladder_apos)
        
        # Jogadores abaixo no ranking permanecem inalterados
        for situacao_antes, situacao_apos in zip(situacao_ladder_antes[3:], situacao_ladder_apos[3:]):
            self.assertEqual(situacao_antes, situacao_apos)
        
        # A ladder deve possuir a mesma quantidade de jogadores
        self.assertEqual(len(situacao_ladder_antes), len(situacao_ladder_apos))
        
    
    def test_validar_desafio_sucesso_historico(self):
        """Testa validação de um desafio para ladder histórico com sucesso"""
        # Verificar posições na ladder
        situacao_ladder_antes = HistoricoLadder.objects.filter(ano=self.ano, mes=self.mes).order_by('posicao').values_list('jogador', 'posicao')
        self.assertIn((self.teets.id, 1), situacao_ladder_antes)
        self.assertIn((self.saraiva.id, 2), situacao_ladder_antes)
        self.assertIn((self.sena.id, 3), situacao_ladder_antes)
        self.assertIn((self.mad.id, 4), situacao_ladder_antes)
        
        self.client.login(username=self.teets.user.username, password=SENHA_TESTE)
        response = self.client.post(reverse('ladder:validar_desafio_ladder', kwargs={'desafio_id': self.desafio_ladder_simples_historico.id}),
                                   {'salvar': 1})
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('ladder:detalhar_ladder_historico', kwargs={'ano': self.desafio_ladder_simples_historico.data_hora.year,
                                                                                           'mes': self.desafio_ladder_simples_historico.data_hora.month}))
        
        # Ver confirmação no messages
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), MENSAGEM_SUCESSO_VALIDAR_DESAFIO_LADDER)
        
        # Desafio deve ter validador
        self.desafio_ladder_simples_historico = DesafioLadder.objects.get(id=self.desafio_ladder_simples_historico.id)
        self.assertEqual(self.desafio_ladder_simples_historico.admin_validador, self.teets)
        
        # Verificar alterações na ladder
        situacao_ladder_apos = HistoricoLadder.objects.filter(ano=self.ano, mes=self.mes).order_by('posicao').values_list('jogador', 'posicao')
        self.assertIn((self.sena.id, 1), situacao_ladder_apos)
        self.assertIn((self.teets.id, 2), situacao_ladder_apos)
        self.assertIn((self.saraiva.id, 3), situacao_ladder_apos)
        
        # Jogadores abaixo no ranking permanecem inalterados
        for situacao_antes, situacao_apos in zip(situacao_ladder_antes[3:], situacao_ladder_apos[3:]):
            self.assertEqual(situacao_antes, situacao_apos)
        
        # A ladder deve possuir a mesma quantidade de jogadores
        self.assertEqual(len(situacao_ladder_antes), len(situacao_ladder_apos))
        
    def test_validar_desafio_coringa_sucesso(self):
        """Testa validação de um desafio para ladder com sucesso, usando coringa"""
        # Verificar posições na ladder
        situacao_ladder_antes = PosicaoLadder.objects.all().order_by('posicao').values_list('jogador', 'posicao')
        self.assertIn((self.teets.id, 1), situacao_ladder_antes)
        self.assertIn((self.saraiva.id, 2), situacao_ladder_antes)
        self.assertIn((self.sena.id, 3), situacao_ladder_antes)
        self.assertIn((self.mad.id, 4), situacao_ladder_antes)
        
        self.client.login(username=self.teets.user.username, password=SENHA_TESTE)
        response = self.client.post(reverse('ladder:validar_desafio_ladder', 
                                            kwargs={'desafio_id': self.desafio_ladder_coringa_vitoria.id}),
                                   {'salvar': 1})
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('ladder:detalhar_ladder_atual'))
        
        # Ver confirmação no messages
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), MENSAGEM_SUCESSO_VALIDAR_DESAFIO_LADDER)
        
        # Desafio deve ter validador
        self.desafio_ladder_coringa_vitoria = DesafioLadder.objects.get(id=self.desafio_ladder_coringa_vitoria.id)
        self.assertEqual(self.desafio_ladder_coringa_vitoria.admin_validador, self.teets)
        
        # Desafiante deve apresentar data de último uso de coringa
        self.assertEqual(Jogador.objects.get(nick='mad').ultimo_uso_coringa, self.desafio_ladder_coringa_vitoria.data_hora.date())
        
        # Verificar alterações na ladder
        situacao_ladder_apos = PosicaoLadder.objects.all().order_by('posicao').values_list('jogador', 'posicao')
        self.assertIn((self.mad.id, 1), situacao_ladder_apos)
        self.assertIn((self.teets.id, 2), situacao_ladder_apos)
        self.assertIn((self.saraiva.id, 3), situacao_ladder_apos)
        self.assertIn((self.sena.id, 4), situacao_ladder_apos)
        
        # Jogadores abaixo no ranking permanecem inalterados
        for situacao_antes, situacao_apos in zip(situacao_ladder_antes[4:], situacao_ladder_apos[4:]):
            self.assertEqual(situacao_antes, situacao_apos)
        
        # A ladder deve possuir a mesma quantidade de jogadores
        self.assertEqual(len(situacao_ladder_antes), len(situacao_ladder_apos))
        
#     def test_erro_validar_desafio_ordem_incorreta(self):
#         """Testa validação de um desafio em ordem incorreta"""
#         # Verificar posições na ladder
#         self.desafio_ladder_simples
#         situacao_ladder = PosicaoLadder.objects.all().order_by('posicao').values_list('jogador', 'posicao')
#         self.assertIn((self.teets.id, 1), situacao_ladder)
#         self.assertIn((self.saraiva.id, 2), situacao_ladder)
#         self.assertIn((self.sena.id, 3), situacao_ladder)
#         self.assertIn((self.mad.id, 4), situacao_ladder)
#         
#         # Adicionar desafio de ladder anterior ao desafio_ladder_simples
#         criar_desafio_ladder_simples_teste(self.sena, self.teets, 3, 1, timezone.now() - datetime.timedelta(days=1), False, self.sena)
#         
#         self.client.login(username=self.teets.user.username, password=SENHA_TESTE)
#         response = self.client.post(reverse('ladder:validar_desafio_ladder', kwargs={'desafio_id': self.desafio_ladder_simples.id}),
#                                    {'salvar': 1})
#         self.assertEqual(response.status_code, 200)
#         
#         # Ver erro no messages
#         messages = list(response.context['messages'])
#         self.assertEqual(len(messages), 1)
#         self.assertEqual(str(messages[0]), 'Validação altera a ladder incorretamente, verifique se há outro desafio pendente')
#         
#         # Desafio deve se manter sem validador
#         self.desafio_ladder_simples = DesafioLadder.objects.get(id=self.desafio_ladder_simples.id)
#         self.assertEqual(self.desafio_ladder_simples.admin_validador, None)
#         
#         # Garantir que a ladder não foi alterada
#         self.assertEqual(situacao_ladder, 
#                          PosicaoLadder.objects.all().order_by('posicao').values_list('jogador', 'posicao'))
        
    def test_erro_acesso_validacao_desafio_ja_validado(self):
        """Testa ver a tela de validação para um desafio já validado"""
        self.client.login(username=self.teets.user.username, password=SENHA_TESTE)
        response = self.client.get(reverse('ladder:validar_desafio_ladder', 
                                           kwargs={'desafio_id': self.desafio_ladder_simples_validado.id}))
        self.assertEqual(response.status_code, 302)
        
        url_esperada = reverse('ladder:detalhar_desafio_ladder', kwargs={'desafio_id': self.desafio_ladder_simples_validado.id})
        self.assertRedirects(response, url_esperada)
        
        # Ver erro no messages
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), f'Validação já foi feita por {self.desafio_ladder_simples_validado.admin_validador}')
            
        
    def test_erro_validar_desafio_ja_validado(self):
        """Testa tentativa de validar um desafio que já foi validado"""
        self.client.login(username=self.teets.user.username, password=SENHA_TESTE)
        response = self.client.post(reverse('ladder:validar_desafio_ladder', 
                                            kwargs={'desafio_id': self.desafio_ladder_simples_validado.id}),
                                   {'salvar': 1})
        self.assertEqual(response.status_code, 302)
        
        url_esperada = reverse('ladder:detalhar_desafio_ladder', kwargs={'desafio_id': self.desafio_ladder_simples_validado.id})
        self.assertRedirects(response, url_esperada)
        
        # Ver erro no messages
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), f'Validação já foi feita por {self.desafio_ladder_simples_validado.admin_validador.nick}')
        
    def test_erro_validar_desafio_coringa_no_tempo_espera_coringa(self):
        """Testa validação de desafio de coringa criado antes de outro desafio coringa ser validado"""
        # Logar admin
        self.client.login(username=self.teets.user.username, password=SENHA_TESTE)
        
        # Validar desafio simples pela view
        response = self.client.post(reverse('ladder:validar_desafio_ladder', 
                                            kwargs={'desafio_id': self.desafio_ladder_coringa_derrota.id}),
                                   {'salvar': 1})
        self.assertEqual(response.status_code, 302)
        
        self.assertRedirects(response, reverse('ladder:detalhar_ladder_atual'))
        
        # Ver confirmação no messages
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), MENSAGEM_SUCESSO_VALIDAR_DESAFIO_LADDER)
        
        # Desafio simples deve ter validador
        self.desafio_ladder_coringa_derrota = DesafioLadder.objects.get(id=self.desafio_ladder_coringa_derrota.id)
        self.assertEqual(self.desafio_ladder_coringa_derrota.admin_validador, self.teets)
        
        # Tentar validar desafio coringa, deve dar erro pois usuário já usou um coringa
        response = self.client.post(reverse('ladder:validar_desafio_ladder', 
                                            kwargs={'desafio_id': self.desafio_ladder_coringa_vitoria.id}),
                                   {'salvar': 1})
        self.assertEqual(response.status_code, 200)
        
        # Desafio coringa não deve ter validador
        self.desafio_ladder_coringa = DesafioLadder.objects.get(id=self.desafio_ladder_coringa_vitoria.id)
        self.assertEqual(self.desafio_ladder_coringa_vitoria.admin_validador, None)
        
        # Ver erro no messages
        messages = list(response.context['messages'])
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), DesafioLadder.MENSAGEM_ERRO_PERIODO_ESPERA_CORINGA)
        
    def test_validar_desafio_novo_entrante_vitoria(self):
        """Testa validação de desafio com novo entrante derrotando último da ladder"""
        # Verificar posições na ladder
        situacao_ladder_antes = PosicaoLadder.objects.all().order_by('posicao').values_list('jogador', 'posicao')
        self.assertIn((self.tiovsky.id, 10), situacao_ladder_antes)
        
        self.client.login(username=self.teets.user.username, password=SENHA_TESTE)
        response = self.client.post(reverse('ladder:validar_desafio_ladder', kwargs={'desafio_id': self.desafio_ladder_novo_entrante.id}),
                                   {'salvar': 1})
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('ladder:detalhar_ladder_atual'))
        
        # Ver confirmação no messages
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), MENSAGEM_SUCESSO_VALIDAR_DESAFIO_LADDER)
        
        # Desafio deve ter validador
        self.desafio_ladder_novo_entrante = DesafioLadder.objects.get(id=self.desafio_ladder_novo_entrante.id)
        self.assertEqual(self.desafio_ladder_novo_entrante.admin_validador, self.teets)
        
        # Verificar alterações na ladder
        situacao_ladder_apos = PosicaoLadder.objects.all().order_by('posicao').values_list('jogador', 'posicao')
        self.assertIn((self.new.id, 10), situacao_ladder_apos)
        self.assertIn((self.tiovsky.id, 11), situacao_ladder_apos)
        
        # Jogadores abaixo no ranking permanecem inalterados
        for situacao_antes, situacao_apos in zip(situacao_ladder_antes[:9], situacao_ladder_apos[:9]):
            self.assertEqual(situacao_antes, situacao_apos)
        
        # A ladder deve possuir um jogador a mais
        self.assertTrue(len(situacao_ladder_antes) + 1 == len(situacao_ladder_apos))
        
    def test_validar_desafio_novo_entrante_coringa_vitoria(self):
        """Testa validação de desafio de novo entrante usando coringa"""
        # Verificar posições na ladder
        situacao_ladder_antes = PosicaoLadder.objects.all().order_by('posicao').values_list('jogador', 'posicao')
        self.assertIn((self.tiovsky.id, 10), situacao_ladder_antes)
        
        # Alterar desafio de novo entrante para usar coringa e desafiar primeiro da ladder
        self.desafio_ladder_novo_entrante.desafio_coringa = True
        self.desafio_ladder_novo_entrante.desafiado = self.teets
        self.desafio_ladder_novo_entrante.save()
        
        self.client.login(username=self.teets.user.username, password=SENHA_TESTE)
        response = self.client.post(reverse('ladder:validar_desafio_ladder', kwargs={'desafio_id': self.desafio_ladder_novo_entrante.id}),
                                   {'salvar': 1})
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('ladder:detalhar_ladder_atual'))
        
        # Ver confirmação no messages
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), MENSAGEM_SUCESSO_VALIDAR_DESAFIO_LADDER)
        
        # Desafio deve ter validador
        self.desafio_ladder_novo_entrante = DesafioLadder.objects.get(id=self.desafio_ladder_novo_entrante.id)
        self.assertEqual(self.desafio_ladder_novo_entrante.admin_validador, self.teets)
        
        # Verificar alterações na ladder
        situacao_ladder_apos = PosicaoLadder.objects.all().order_by('posicao').values_list('jogador', 'posicao')
        self.assertIn((self.new.id, 1), situacao_ladder_apos)
        self.assertIn((self.teets.id, 2), situacao_ladder_apos)
        
        # Todos os jogadores são deslocados uma posição
        for situacao_antes, situacao_apos in zip(situacao_ladder_antes[:], situacao_ladder_apos[1:]):
            self.assertEqual(situacao_antes[0], situacao_apos[0])
        
        # A ladder deve possuir um jogador a mais
        self.assertTrue(len(situacao_ladder_antes) + 1 == len(situacao_ladder_apos))
        
    def test_validar_desafio_novo_entrante_derrota(self):
        """Testar validação de desafio com novo entrante derrotado, ladder se mantém e entrante vai para última posição"""
        # Verificar posições na ladder
        situacao_ladder_antes = PosicaoLadder.objects.all().order_by('posicao').values_list('jogador', 'posicao')
        self.assertIn((self.tiovsky.id, 10), situacao_ladder_antes)
        
        # Alterar para vitória do desafiado, novo entrante perdeu
        self.desafio_ladder_novo_entrante.score_desafiado = 3
        self.desafio_ladder_novo_entrante.score_desafiante = 1
        self.desafio_ladder_novo_entrante.save()
        
        self.client.login(username=self.teets.user.username, password=SENHA_TESTE)
        response = self.client.post(reverse('ladder:validar_desafio_ladder', kwargs={'desafio_id': self.desafio_ladder_novo_entrante.id}),
                                   {'salvar': 1})
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('ladder:detalhar_ladder_atual'))
        
        # Ver confirmação no messages
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), MENSAGEM_SUCESSO_VALIDAR_DESAFIO_LADDER)
        
        # Desafio deve ter validador
        self.desafio_ladder_novo_entrante = DesafioLadder.objects.get(id=self.desafio_ladder_novo_entrante.id)
        self.assertEqual(self.desafio_ladder_novo_entrante.admin_validador, self.teets)
        
        # Verificar alterações na ladder
        situacao_ladder_apos = PosicaoLadder.objects.all().order_by('posicao').values_list('jogador', 'posicao')
        self.assertIn((self.tiovsky.id, 10), situacao_ladder_apos)
        self.assertIn((self.new.id, 11), situacao_ladder_apos)
        
        # Jogadores abaixo no ranking permanecem inalterados
        for situacao_antes, situacao_apos in zip(situacao_ladder_antes[:9], situacao_ladder_apos[:9]):
            self.assertEqual(situacao_antes, situacao_apos)
        
        # A ladder deve possuir um jogador a mais
        self.assertTrue(len(situacao_ladder_antes) + 1 == len(situacao_ladder_apos))
        