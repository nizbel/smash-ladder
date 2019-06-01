# -*- coding: utf-8 -*-
import calendar
import datetime

from django.contrib.auth.models import User
from django.contrib.messages.api import get_messages
from django.test.testcases import TestCase
from django.urls.base import reverse
from django.utils import timezone

from jogadores.models import Jogador, Personagem, RegistroFerias
from jogadores.tests.utils_teste import criar_jogadores_teste, SENHA_TESTE, \
    criar_personagens_teste, criar_stage_teste
from ladder.models import PosicaoLadder, HistoricoLadder, JogadorLuta, \
    DesafioLadder, CancelamentoDesafioLadder, Luta, LutaLadder
from ladder.tests.utils_teste import criar_ladder_teste, \
    criar_ladder_historico_teste, criar_luta_teste, criar_luta_completa_teste, \
    criar_desafio_ladder_simples_teste, criar_desafio_ladder_completo_teste, \
    validar_desafio_ladder_teste, gerar_campos_formset
from ladder.views import MENSAGEM_ERRO_EDITAR_DESAFIO_CANCELADO, \
    MENSAGEM_SUCESSO_EDITAR_DESAFIO_LADDER
from smashLadder import settings


class ViewEditarDesafioLadderTestCase(TestCase):
    """Testes para a view de editar desafio para ladder"""
    @classmethod
    def setUpTestData(cls):
        super(ViewEditarDesafioLadderTestCase, cls).setUpTestData()
        
        # Jogadores
        criar_jogadores_teste()
        
        cls.teets = Jogador.objects.get(nick='teets') # Admin, com desafios
        cls.saraiva = Jogador.objects.get(nick='saraiva') # Admin, sem desafios
        cls.sena = Jogador.objects.get(nick='sena') # Não-admin, com desafios
        cls.mad = Jogador.objects.get(nick='mad') # Não-admin, sem desafios
        cls.tiovsky = Jogador.objects.get(nick='tiovsky') # Não-admin, sem desafios
        
        # Personagens
        criar_personagens_teste()
        
        cls.fox = Personagem.objects.get(nome='Fox')
        cls.marth = Personagem.objects.get(nome='Marth')
        
        # Stage
        cls.stage = criar_stage_teste()
        
        # Criar ladders para verificar que adicionar desafio não as afeta
        criar_ladder_teste()
        
        # Preparar mês anterior para histórico
        cls.horario_atual = timezone.now()
        data_atual = cls.horario_atual.date()
        cls.ano = data_atual.year
        cls.mes = data_atual.month - 1
        if cls.mes == 0:
            cls.mes = 12
            cls.ano -= 1
        
        criar_ladder_historico_teste(cls.ano, cls.mes)
        
        # Criar desafios para ladder
        cls.horario_historico = cls.horario_atual.replace(year=cls.ano, month=cls.mes)
        cls.desafio_ladder = criar_desafio_ladder_simples_teste(cls.sena, cls.teets, 3, 1, 
                                                                          cls.horario_atual, False, cls.teets)
        cls.desafio_ladder_historico = criar_desafio_ladder_simples_teste(cls.sena, cls.teets, 3, 1, 
                                                                                    cls.horario_historico.replace(day=1) - datetime.timedelta(days=15), 
                                                                                    False, cls.sena)
        
        cls.desafio_ladder_add_por_nao_admin = criar_desafio_ladder_simples_teste(cls.sena, cls.teets, 3, 1, 
                                                                          cls.horario_atual - datetime.timedelta(days=4), False, cls.sena)
        
        cls.desafio_ladder_completo = criar_desafio_ladder_completo_teste(cls.sena, cls.saraiva, 1, 3, 
                                                                          cls.horario_atual - datetime.timedelta(days=8), False, cls.sena)
        
    def test_acesso_deslogado(self):
        """Testa acesso a tela de editar desafio de ladder sem logar"""
        response = self.client.get(reverse('ladder:editar_desafio_ladder', kwargs={'desafio_id': self.desafio_ladder.id}))
        self.assertEqual(response.status_code, 302)
        
        url_esperada = settings.LOGIN_URL + '?next=' + reverse('ladder:editar_desafio_ladder', 
                                                               kwargs={'desafio_id': self.desafio_ladder.id})
        self.assertRedirects(response, url_esperada)
        
    def test_acesso_logado_criador_desafio_nao_validado(self):
        """Testa acesso a tela de editar desafio de ladder logado como criador do desafio não validado"""
        self.client.login(username=self.sena.user.username, password=SENHA_TESTE)
        response = self.client.get(reverse('ladder:editar_desafio_ladder', kwargs={'desafio_id': self.desafio_ladder_add_por_nao_admin.id}))
        self.assertEqual(response.status_code, 200)
        self.assertIn('form_desafio_ladder', response.context)
        
    def test_acesso_logado_terceiro_desafio_nao_validado(self):
        """Testa acesso a tela de editar desafio de ladder logado como não criador do desafio não validado"""
        self.client.login(username=self.mad.user.username, password=SENHA_TESTE)
        response = self.client.get(reverse('ladder:editar_desafio_ladder', kwargs={'desafio_id': self.desafio_ladder.id}))
        self.assertEqual(response.status_code, 403)
        
    def test_acesso_logado_criador_desafio_validado(self):
        """Testa acesso a tela de editar desafio de ladder logado como criador do desafio validado"""
        # Definir desafio como validado
        self.desafio_ladder.admin_validador = self.teets
        self.desafio_ladder.save()
        
        self.client.login(username=self.sena.user.username, password=SENHA_TESTE)
        response = self.client.get(reverse('ladder:editar_desafio_ladder', kwargs={'desafio_id': self.desafio_ladder.id}))
        self.assertEqual(response.status_code, 403)
        
    def test_acesso_logado_terceiro_desafio_validado(self):
        """Testa acesso a tela de editar desafio de ladder logado como não criador do desafio validado"""
        # Definir desafio como validado
        self.desafio_ladder.admin_validador = self.teets
        self.desafio_ladder.save()
        
        self.client.login(username=self.mad.user.username, password=SENHA_TESTE)
        response = self.client.get(reverse('ladder:editar_desafio_ladder', kwargs={'desafio_id': self.desafio_ladder.id}))
        self.assertEqual(response.status_code, 403)
        
    def test_acesso_logado_admin_desafio_nao_validado(self):
        """Testa acesso a tela de editar desafio de ladder não validado, logado como admin"""
        self.client.login(username=self.teets.user.username, password=SENHA_TESTE)
        response = self.client.get(reverse('ladder:editar_desafio_ladder', kwargs={'desafio_id': self.desafio_ladder.id}))
        self.assertEqual(response.status_code, 200)
        self.assertIn('form_desafio_ladder', response.context)
        
    def test_acesso_logado_admin_desafio_validado(self):
        """Testa acesso a tela de editar desafio de ladder validado, logado como admin"""
        # Definir desafio como validado
        self.desafio_ladder.admin_validador = self.teets
        self.desafio_ladder.save()
        
        self.client.login(username=self.teets.user.username, password=SENHA_TESTE)
        response = self.client.get(reverse('ladder:editar_desafio_ladder', kwargs={'desafio_id': self.desafio_ladder.id}))
        self.assertEqual(response.status_code, 403)
        
    def test_acesso_logado_desafio_cancelado(self):
        """Testa acesso a tela de editar desafio de ladder que já foi cancelado"""
        # Definir desafio como cancelado
        CancelamentoDesafioLadder.objects.create(desafio_ladder=self.desafio_ladder, jogador=self.teets)
        
        self.client.login(username=self.saraiva.user.username, password=SENHA_TESTE)
        response = self.client.get(reverse('ladder:editar_desafio_ladder', kwargs={'desafio_id': self.desafio_ladder.id}))
        self.assertEqual(response.status_code, 302)
        
        url_esperada = reverse('ladder:detalhar_desafio_ladder', kwargs={'desafio_id': self.desafio_ladder.id})
        self.assertRedirects(response, url_esperada)
        
        # Verificar mensagens
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), MENSAGEM_ERRO_EDITAR_DESAFIO_CANCELADO)
        
    def test_editar_desafio_ja_cancelado(self):
        """Testa editar desafio de ladder que já foi cancelado"""
        # Definir desafio como cancelado
        CancelamentoDesafioLadder.objects.create(desafio_ladder=self.desafio_ladder, jogador=self.teets)
        
        # Preparar dados POST
        dados_post = {}
        # Preparar informações para validação do formset
        formset = gerar_campos_formset([], 'desafio_ladder_luta')
        
        dados_post = {**dados_post, **formset}
        
        self.client.login(username=self.saraiva.user.username, password=SENHA_TESTE)
        response = self.client.post(reverse('ladder:editar_desafio_ladder', kwargs={'desafio_id': self.desafio_ladder.id}),
                                    dados_post)
        self.assertEqual(response.status_code, 302)
        
        url_esperada = reverse('ladder:detalhar_desafio_ladder', kwargs={'desafio_id': self.desafio_ladder.id})
        self.assertRedirects(response, url_esperada)
        
        # Verificar mensagens
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), MENSAGEM_ERRO_EDITAR_DESAFIO_CANCELADO)
        
    def test_form_edicao_desafio_simples_nao_validado(self):
        """Testa os campos para o formulário de edição de desafio de ladder simples não validado"""
        self.client.login(username=self.sena.user.username, password=SENHA_TESTE)
        response = self.client.get(reverse('ladder:editar_desafio_ladder', kwargs={'desafio_id': self.desafio_ladder_add_por_nao_admin.id}))
        self.assertEqual(response.status_code, 200)
        
        # Verificar form
        form = response.context['form_desafio_ladder']
        # Apenas criador do desafio deve estar desabilitado
        self.assertFalse(form.fields['desafiante'].disabled)
        self.assertFalse(form.fields['desafiado'].disabled)
        self.assertFalse(form.fields['score_desafiante'].disabled)
        self.assertFalse(form.fields['score_desafiado'].disabled)
        self.assertFalse(form.fields['desafio_coringa'].disabled)
        self.assertFalse(form.fields['data_hora'].disabled)
        self.assertTrue(form.fields['adicionado_por'].disabled)
        
        # Todos os campos devem ter valores iniciais
        self.assertNotEqual(form.initial['desafiante'], None)
        self.assertNotEqual(form.initial['desafiado'], None)
        self.assertNotEqual(form.initial['score_desafiante'], None)
        self.assertNotEqual(form.initial['score_desafiado'], None)
        self.assertNotEqual(form.initial['desafio_coringa'], None)
        self.assertNotEqual(form.initial['data_hora'], None)
        self.assertNotEqual(form.initial['adicionado_por'], None)
        
    
    def test_form_edicao_desafio_simples_validado(self):
        """Testa os campos para o formulário de edição de desafio de ladder simples validado"""
        # TODO implementar
        pass
    
    def test_form_edicao_desafio_completo_nao_validado(self):
        """Testa os campos para o formulário de edição de desafio de ladder completo não validado"""
        self.client.login(username=self.sena.user.username, password=SENHA_TESTE)
        response = self.client.get(reverse('ladder:editar_desafio_ladder', kwargs={'desafio_id': self.desafio_ladder_completo.id}))
        self.assertEqual(response.status_code, 200)
        
        # Verificar form e formset
        form = response.context['form_desafio_ladder']
        formset = response.context['formset_lutas']
        
        # Apenas criador do desafio deve estar desabilitado
        # Form
        self.assertFalse(form.fields['desafiante'].disabled)
        self.assertFalse(form.fields['desafiado'].disabled)
        self.assertFalse(form.fields['score_desafiante'].disabled)
        self.assertFalse(form.fields['score_desafiado'].disabled)
        self.assertFalse(form.fields['desafio_coringa'].disabled)
        self.assertFalse(form.fields['data_hora'].disabled)
        self.assertTrue(form.fields['adicionado_por'].disabled)
        # Formset
        for form_luta in formset:
            self.assertFalse(form_luta.fields['ganhador'].disabled)
            self.assertFalse(form_luta.fields['stage'].disabled)
            self.assertFalse(form_luta.fields['personagem_desafiante'].disabled)
            self.assertFalse(form_luta.fields['personagem_desafiado'].disabled)
        
        # Todos os campos devem ter valores iniciais
        self.assertNotEqual(form.initial['desafiante'], None)
        self.assertNotEqual(form.initial['desafiado'], None)
        self.assertNotEqual(form.initial['score_desafiante'], None)
        self.assertNotEqual(form.initial['score_desafiado'], None)
        self.assertNotEqual(form.initial['desafio_coringa'], None)
        self.assertNotEqual(form.initial['data_hora'], None)
        self.assertNotEqual(form.initial['adicionado_por'], None)
        # Formset
        for form_luta in formset[:4]:
            # Como desafio completo lista 4 lutas (3x1), apenas as 4 primeiras estão preenchidas
            self.assertNotEqual(form_luta.initial['ganhador'], None)
            self.assertNotEqual(form_luta.initial['stage'], None)
            self.assertNotEqual(form_luta.initial['personagem_desafiante'], None)
            self.assertNotEqual(form_luta.initial['personagem_desafiado'], None)
            
        self.assertEqual(formset[4].initial, {})
    
    def test_form_edicao_desafio_completo_validado(self):
        """Testa os campos para o formulário de edição de desafio de ladder completo validado"""
        # TODO implementar
        pass
        
    def test_editar_desafio_nao_validado_atual_sucesso(self):
        """Testa editar desafio de ladder atual não validado com sucesso"""
        horario_atual = datetime.datetime.now()
        
        # Preparar informações do form
        form = {'desafiante': self.tiovsky.id, 'desafiado': self.mad.id, 'score_desafiante': 0, 'score_desafiado': 3, 
                                      'desafio_coringa': True, 'data_hora': horario_atual}
        
        # Preparar informações para validação do formset
        formset = gerar_campos_formset([], 'desafio_ladder_luta')
        
        # Preparar dados POST
        dados_post = {**form, **formset}
        
        self.client.login(username=self.teets.user.username, password=SENHA_TESTE)
        response = self.client.post(reverse('ladder:editar_desafio_ladder', kwargs={'desafio_id': self.desafio_ladder.id}),
                                   dados_post)
        self.assertEqual(response.status_code, 302)
        
        url_esperada = reverse('ladder:detalhar_desafio_ladder', kwargs={'desafio_id': self.desafio_ladder.id})
        self.assertRedirects(response, url_esperada)
                             
        # Verificar mensagens
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), MENSAGEM_SUCESSO_EDITAR_DESAFIO_LADDER)
        
        # Verificar alterações em desafio
        self.desafio_ladder = DesafioLadder.objects.get(id=self.desafio_ladder.id)
        self.assertEqual(self.desafio_ladder.desafiante, self.tiovsky)
        self.assertEqual(self.desafio_ladder.desafiado, self.mad)
        self.assertEqual(self.desafio_ladder.score_desafiante, 0)
        self.assertEqual(self.desafio_ladder.score_desafiado, 3)
        self.assertEqual(self.desafio_ladder.desafio_coringa, True)
        self.assertEqual(self.desafio_ladder.data_hora, timezone.make_aware(horario_atual))
        self.assertEqual(self.desafio_ladder.adicionado_por, self.teets)
        
    def test_editar_desafio_nao_validado_atual_sucesso_mesmo_horario(self):
        """Testa editar desafio de ladder atual não validado com sucesso, sem alterar horário"""
        # Preparar informações do form
        form = {'desafiante': self.sena.id, 'desafiado': self.teets.id, 'score_desafiante': 3, 'score_desafiado': 2, 
                                      'desafio_coringa': False, 'data_hora': timezone.make_naive(self.desafio_ladder.data_hora)}
        
        # Preparar informações para validação do formset
        formset = gerar_campos_formset([], 'desafio_ladder_luta')
        
        # Preparar dados POST
        dados_post = {**form, **formset}
        
        self.client.login(username=self.teets.user.username, password=SENHA_TESTE)
        response = self.client.post(reverse('ladder:editar_desafio_ladder', kwargs={'desafio_id': self.desafio_ladder.id}),
                                   dados_post)
        self.assertEqual(response.status_code, 302)
        
        url_esperada = reverse('ladder:detalhar_desafio_ladder', kwargs={'desafio_id': self.desafio_ladder.id})
        self.assertRedirects(response, url_esperada)
                             
        # Verificar mensagens
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), MENSAGEM_SUCESSO_EDITAR_DESAFIO_LADDER)
        
        # Verificar alterações em desafio
        self.desafio_ladder = DesafioLadder.objects.get(id=self.desafio_ladder.id)
        self.assertEqual(self.desafio_ladder.score_desafiante, 3)
        self.assertEqual(self.desafio_ladder.score_desafiado, 2)
        
    def test_editar_desafio_nao_validado_historico_sucesso(self):
        """Testa editar desafio de ladder histórico não validado com sucesso"""
        horario_historico = datetime.datetime.now().replace(month=self.horario_historico.month, 
                                                            year=self.horario_historico.year)
        
        # Preparar informações do form
        form = {'desafiante': self.tiovsky.id, 'desafiado': self.mad.id, 'score_desafiante': 0, 'score_desafiado': 3, 
                                      'desafio_coringa': True, 'data_hora': horario_historico}
        
        # Preparar informações para validação do formset
        formset = gerar_campos_formset([], 'desafio_ladder_luta')
        
        # Preparar dados POST
        dados_post = {**form, **formset}
        
        self.client.login(username=self.teets.user.username, password=SENHA_TESTE)
        response = self.client.post(reverse('ladder:editar_desafio_ladder', kwargs={'desafio_id': self.desafio_ladder_historico.id}),
                                   dados_post)
        self.assertEqual(response.status_code, 302)
        
        url_esperada = reverse('ladder:detalhar_desafio_ladder', kwargs={'desafio_id': self.desafio_ladder_historico.id})
        self.assertRedirects(response, url_esperada)
                             
        # Verificar mensagens
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), MENSAGEM_SUCESSO_EDITAR_DESAFIO_LADDER)
        
        # Verificar alterações em desafio
        self.desafio_ladder_historico = DesafioLadder.objects.get(id=self.desafio_ladder_historico.id)
        self.assertEqual(self.desafio_ladder_historico.desafiante, self.tiovsky)
        self.assertEqual(self.desafio_ladder_historico.desafiado, self.mad)
        self.assertEqual(self.desafio_ladder_historico.score_desafiante, 0)
        self.assertEqual(self.desafio_ladder_historico.score_desafiado, 3)
        self.assertEqual(self.desafio_ladder_historico.desafio_coringa, True)
        self.assertEqual(self.desafio_ladder_historico.data_hora, timezone.make_aware(horario_historico))
        self.assertEqual(self.desafio_ladder_historico.adicionado_por, self.sena)
        
    def test_editar_desafio_validado_atual_sucesso(self):
        """Testa editar desafio de ladder atual validado com sucesso"""
        # TODO implementar
        pass
        
    def test_editar_desafio_validado_historico_sucesso(self):
        """Testa editar desafio de ladder histórico validado com sucesso"""
        # TODO implementar
        pass

    def test_erro_editar_desafio_criador_fora_desafio(self):
        """Testa se editar o desafio de forma que o criador não participe nem seja admin dá erro"""
        horario_atual = datetime.datetime.now()
        
        # Preparar informações do form
        form = {'desafiante': self.mad.id, 'desafiado': self.teets.id, 'score_desafiante': 0, 'score_desafiado': 3, 
                                      'desafio_coringa': True, 'data_hora': horario_atual}
        
        # Preparar informações para validação do formset
        formset = gerar_campos_formset([], 'desafio_ladder_luta')
        
        # Preparar dados POST
        dados_post = {**form, **formset}
        
        self.client.login(username=self.sena.user.username, password=SENHA_TESTE)
        response = self.client.post(reverse('ladder:editar_desafio_ladder', kwargs={'desafio_id': self.desafio_ladder_add_por_nao_admin.id}),
                                   dados_post)
        self.assertEqual(response.status_code, 200)
        
        # Verificar erros
        self.assertContains(response, 'Jogador não pode criar desafios para ladder para terceiros')
        
        # Verificar se desafio não foi alterado
        self.desafio_ladder_add_por_nao_admin = DesafioLadder.objects.get(id=self.desafio_ladder_add_por_nao_admin.id)
        self.assertEqual(self.desafio_ladder.desafiante, self.sena)
        self.assertEqual(self.desafio_ladder_add_por_nao_admin.desafiado, self.teets)
        self.assertEqual(self.desafio_ladder_add_por_nao_admin.score_desafiante, 3)
        self.assertEqual(self.desafio_ladder_add_por_nao_admin.score_desafiado, 1)
        self.assertEqual(self.desafio_ladder_add_por_nao_admin.desafio_coringa, False)
        self.assertEqual(self.desafio_ladder_add_por_nao_admin.data_hora, self.horario_atual - datetime.timedelta(days=4))
        self.assertEqual(self.desafio_ladder_add_por_nao_admin.adicionado_por, self.sena)
        
    def test_editar_desafio_nao_validado_completo_sucesso(self):
        """Testa editar desafio de ladder completo não validado com sucesso"""
        novo_horario = self.desafio_ladder_completo.data_hora - datetime.timedelta(days=1)
        
        # Guardar ids dos modelos relacionados a luta para verificar posteriormente se nenhuma nova foi criada
        lutas_antes = Luta.objects.all().values_list('id')
        jogador_lutas_antes = JogadorLuta.objects.all().values_list('id')
        lutas_ladder_antes = LutaLadder.objects.all().values_list('id')
        
        form = {'desafiante': self.sena.id, 'desafiado': self.teets.id, 'score_desafiante': 3, 'score_desafiado': 1, 
                                      'desafio_coringa': True, 'data_hora': timezone.make_naive(novo_horario)}
        
        lutas = Luta.objects.filter(lutaladder__desafio_ladder=self.desafio_ladder_completo).select_related('lutaladder') \
                .order_by('lutaladder__indice_desafio_ladder')

        formset_lutas = gerar_campos_formset([{'ganhador': self.sena.id, 'stage': self.stage.id, 
                                               'personagem_desafiante': self.fox.id, 'personagem_desafiado': self.fox.id},
                                               {'ganhador': self.sena.id, 'stage': self.stage.id, 
                                                'personagem_desafiante': self.marth.id, 'personagem_desafiado': ''},
                                               {'ganhador': self.teets.id, 'stage': '',  
                                                'personagem_desafiante': '', 'personagem_desafiado': self.marth.id},
                                               {'ganhador': self.sena.id, 'stage': self.stage.id, 
                                                'personagem_desafiante': self.marth.id, 'personagem_desafiado': self.fox.id}], 'desafio_ladder_luta')
#         (cls.sena, cls.saraiva, 1, 3, cls.horario_atual.replace(day=5), False, cls.sena)
    
        # Preparar dados POST
        dados_post = {**form, **formset_lutas}
        
        self.client.login(username=self.teets.user.username, password=SENHA_TESTE)
        response = self.client.post(reverse('ladder:editar_desafio_ladder', kwargs={'desafio_id': self.desafio_ladder_completo.id}),
                                   dados_post)
        self.assertEqual(response.status_code, 302)
        
        url_esperada = reverse('ladder:detalhar_desafio_ladder', kwargs={'desafio_id': self.desafio_ladder_completo.id})
        self.assertRedirects(response, url_esperada)
                             
        # Verificar mensagens
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), MENSAGEM_SUCESSO_EDITAR_DESAFIO_LADDER)
        
        # Verificar alterações em desafio
        self.desafio_ladder_completo = DesafioLadder.objects.get(id=self.desafio_ladder_completo.id)
        self.assertEqual(self.desafio_ladder_completo.desafiante, self.sena)
        self.assertEqual(self.desafio_ladder_completo.desafiado, self.teets)
        self.assertEqual(self.desafio_ladder_completo.score_desafiante, 3)
        self.assertEqual(self.desafio_ladder_completo.score_desafiado, 1)
        self.assertEqual(self.desafio_ladder_completo.desafio_coringa, True)
        self.assertEqual(self.desafio_ladder_completo.data_hora, novo_horario)
        self.assertEqual(self.desafio_ladder_completo.adicionado_por, self.sena)
        
        # Verificar alterações em lutas
        self.assertEqual(Luta.objects.count(), 4)
        self.assertEqual(JogadorLuta.objects.count(), 8)
        self.assertEqual(LutaLadder.objects.count(), 4)
        
        lutas = self.desafio_ladder_completo.lutaladder_set.all()
        self.assertEqual(lutas.count(), 4)
        
        # Luta 1
        luta_1 = lutas.get(indice_desafio_ladder=1).luta
        self.assertEqual(luta_1.ganhador, self.sena)
        self.assertEqual(luta_1.stage, self.stage)
        self.assertEqual(luta_1.data, self.desafio_ladder_completo.data_hora.date())
        self.assertEqual(luta_1.jogadorluta_set.all().count(), 2)
        self.assertIn((self.sena.id, self.fox.id), luta_1.jogadorluta_set.all().values_list('jogador', 'personagem'))
        self.assertIn((self.teets.id, self.fox.id), luta_1.jogadorluta_set.all().values_list('jogador', 'personagem'))
        
        # Luta 2
        luta_2 = lutas.get(indice_desafio_ladder=2).luta
        self.assertEqual(luta_2.ganhador, self.sena)
        self.assertEqual(luta_2.stage, self.stage)
        self.assertEqual(luta_2.data, self.desafio_ladder_completo.data_hora.date())
        self.assertEqual(luta_2.jogadorluta_set.all().count(), 2)
        self.assertIn((self.sena.id, self.marth.id), luta_2.jogadorluta_set.all().values_list('jogador', 'personagem'))
        self.assertIn((self.teets.id, None), luta_2.jogadorluta_set.all().values_list('jogador', 'personagem'))
        
        # Luta 3
        luta_3 = lutas.get(indice_desafio_ladder=3).luta
        self.assertEqual(luta_3.ganhador, self.teets)
        self.assertEqual(luta_3.stage, None)
        self.assertEqual(luta_3.data, self.desafio_ladder_completo.data_hora.date())
        self.assertEqual(luta_3.jogadorluta_set.all().count(), 2)
        self.assertIn((self.sena.id, None), luta_3.jogadorluta_set.all().values_list('jogador', 'personagem'))
        self.assertIn((self.teets.id, self.marth.id), luta_3.jogadorluta_set.all().values_list('jogador', 'personagem'))
        
        # Luta 4
        luta_4 = lutas.get(indice_desafio_ladder=4).luta
        self.assertEqual(luta_4.ganhador, self.sena)
        self.assertEqual(luta_4.stage, self.stage)
        self.assertEqual(luta_4.data, self.desafio_ladder_completo.data_hora.date())
        self.assertEqual(luta_4.jogadorluta_set.all().count(), 2)
        self.assertIn((self.sena.id, self.marth.id), luta_4.jogadorluta_set.all().values_list('jogador', 'personagem'))
        self.assertIn((self.teets.id, self.fox.id), luta_4.jogadorluta_set.all().values_list('jogador', 'personagem'))
        
        # Verificar se nenhum novo modelo relacionado a luta foi criado
        lutas_apos = Luta.objects.all().values_list('id')
        for luta_id in lutas_apos:
            self.assertIn(luta_id, lutas_antes)
            
        jogador_lutas_apos = JogadorLuta.objects.all().values_list('id')
        for jogador_luta_id in jogador_lutas_apos:
            self.assertIn(jogador_luta_id, jogador_lutas_antes)
            
        lutas_ladder_apos = LutaLadder.objects.all().values_list('id')
        for luta_ladder_id in lutas_ladder_apos:
            self.assertIn(luta_ladder_id, lutas_ladder_antes)
        
    def test_editar_desafio_nao_validado_completo_sucesso_adicionando_1_luta(self):
        """Testa editar desafio de ladder completo não validado adicionando 1 luta, com sucesso"""
        novo_horario = self.desafio_ladder_completo.data_hora - datetime.timedelta(days=1)
        # Verificar que existem apenas 4 lutas
        self.assertEqual(Luta.objects.count(), 4)
        self.assertEqual(JogadorLuta.objects.count(), 8)
        self.assertEqual(LutaLadder.objects.count(), 4)
        
        form = {'desafiante': self.sena.id, 'desafiado': self.teets.id, 'score_desafiante': 3, 'score_desafiado': 2, 
                                      'desafio_coringa': True, 'data_hora': timezone.make_naive(novo_horario)}
        
        formset_lutas = gerar_campos_formset([{'ganhador': self.sena.id, 'stage': self.stage.id, 
                                     'personagem_desafiante': self.fox.id, 'personagem_desafiado': self.fox.id},
                                    {'ganhador': self.sena.id, 'stage': self.stage.id, 
                                     'personagem_desafiante': self.marth.id, 'personagem_desafiado': self.fox.id},
                                    {'ganhador': self.teets.id, 'stage': self.stage.id, 
                                     'personagem_desafiante': self.marth.id, 'personagem_desafiado': self.marth.id},
                                    {'ganhador': self.teets.id, 'stage': '', 
                                     'personagem_desafiante': self.marth.id, 'personagem_desafiado': self.marth.id},
                                    {'ganhador': self.sena.id, 'stage': self.stage.id, 
                                     'personagem_desafiante': self.marth.id, 'personagem_desafiado': self.fox.id}], 'desafio_ladder_luta')
#         (cls.sena, cls.saraiva, 1, 3, cls.horario_atual.replace(day=5), False, cls.sena)
        
        # Preparar dados POST
        dados_post = {**form, **formset_lutas}
        
        self.client.login(username=self.teets.user.username, password=SENHA_TESTE)
        response = self.client.post(reverse('ladder:editar_desafio_ladder', kwargs={'desafio_id': self.desafio_ladder_completo.id}),
                                   dados_post)
        self.assertEqual(response.status_code, 302)
        
        url_esperada = reverse('ladder:detalhar_desafio_ladder', kwargs={'desafio_id': self.desafio_ladder_completo.id})
        self.assertRedirects(response, url_esperada)
                             
        # Verificar mensagens
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), MENSAGEM_SUCESSO_EDITAR_DESAFIO_LADDER)
        
        # Verificar alterações em desafio
        self.desafio_ladder_completo = DesafioLadder.objects.get(id=self.desafio_ladder_completo.id)
        self.assertEqual(self.desafio_ladder_completo.desafiante, self.sena)
        self.assertEqual(self.desafio_ladder_completo.desafiado, self.teets)
        self.assertEqual(self.desafio_ladder_completo.score_desafiante, 3)
        self.assertEqual(self.desafio_ladder_completo.score_desafiado, 2)
        self.assertEqual(self.desafio_ladder_completo.desafio_coringa, True)
        self.assertEqual(self.desafio_ladder_completo.data_hora, novo_horario)
        self.assertEqual(self.desafio_ladder_completo.adicionado_por, self.sena)
        
        # Verificar alterações em lutas
        self.assertEqual(Luta.objects.count(), 5)
        self.assertEqual(JogadorLuta.objects.count(), 10)
        self.assertEqual(LutaLadder.objects.count(), 5)
        
        lutas = self.desafio_ladder_completo.lutaladder_set.all()
        self.assertEqual(lutas.count(), 5)
        
        # Luta 1
        luta_1 = lutas.get(indice_desafio_ladder=1).luta
        self.assertEqual(luta_1.ganhador, self.sena)
        self.assertEqual(luta_1.stage, self.stage)
        self.assertEqual(luta_1.data, self.desafio_ladder_completo.data_hora.date())
        self.assertEqual(luta_1.jogadorluta_set.all().count(), 2)
        self.assertIn((self.sena.id, self.fox.id), luta_1.jogadorluta_set.all().values_list('jogador', 'personagem'))
        self.assertIn((self.teets.id, self.fox.id), luta_1.jogadorluta_set.all().values_list('jogador', 'personagem'))
        
        # Luta 2
        luta_2 = lutas.get(indice_desafio_ladder=2).luta
        self.assertEqual(luta_2.ganhador, self.sena)
        self.assertEqual(luta_2.stage, self.stage)
        self.assertEqual(luta_2.data, self.desafio_ladder_completo.data_hora.date())
        self.assertEqual(luta_2.jogadorluta_set.all().count(), 2)
        self.assertIn((self.sena.id, self.marth.id), luta_2.jogadorluta_set.all().values_list('jogador', 'personagem'))
        self.assertIn((self.teets.id, self.fox.id), luta_2.jogadorluta_set.all().values_list('jogador', 'personagem'))
        
        # Luta 3
        luta_3 = lutas.get(indice_desafio_ladder=3).luta
        self.assertEqual(luta_3.ganhador, self.teets)
        self.assertEqual(luta_3.stage, self.stage)
        self.assertEqual(luta_3.data, self.desafio_ladder_completo.data_hora.date())
        self.assertEqual(luta_3.jogadorluta_set.all().count(), 2)
        self.assertIn((self.sena.id, self.marth.id), luta_3.jogadorluta_set.all().values_list('jogador', 'personagem'))
        self.assertIn((self.teets.id, self.marth.id), luta_3.jogadorluta_set.all().values_list('jogador', 'personagem'))
        
        # Luta 4
        luta_4 = lutas.get(indice_desafio_ladder=4).luta
        self.assertEqual(luta_4.ganhador, self.teets)
        self.assertEqual(luta_4.stage, None)
        self.assertEqual(luta_4.data, self.desafio_ladder_completo.data_hora.date())
        self.assertEqual(luta_4.jogadorluta_set.all().count(), 2)
        self.assertIn((self.sena.id, self.marth.id), luta_4.jogadorluta_set.all().values_list('jogador', 'personagem'))
        self.assertIn((self.teets.id, self.marth.id), luta_4.jogadorluta_set.all().values_list('jogador', 'personagem'))
        
        # Luta 5
        luta_5 = lutas.get(indice_desafio_ladder=5).luta
        self.assertEqual(luta_5.ganhador, self.sena)
        self.assertEqual(luta_5.stage, self.stage)
        self.assertEqual(luta_5.data, self.desafio_ladder_completo.data_hora.date())
        self.assertEqual(luta_5.jogadorluta_set.all().count(), 2)
        self.assertIn((self.sena.id, self.marth.id), luta_5.jogadorluta_set.all().values_list('jogador', 'personagem'))
        self.assertIn((self.teets.id, self.fox.id), luta_5.jogadorluta_set.all().values_list('jogador', 'personagem'))
        
    def test_editar_desafio_nao_validado_completo_sucesso_removendo_ultima_luta(self):
        """Testa editar desafio de ladder completo não validado removendo última luta, com sucesso"""
        novo_horario = self.desafio_ladder_completo.data_hora - datetime.timedelta(days=1)
        
        # Verificar que existem apenas 4 lutas
        self.assertEqual(Luta.objects.count(), 4)
        self.assertEqual(JogadorLuta.objects.count(), 8)
        self.assertEqual(LutaLadder.objects.count(), 4)
        
        # Guardar ids dos modelos relacionados a luta para verificar posteriormente se nenhuma nova foi criada
        lutas_antes = Luta.objects.all().values_list('id')
        jogador_lutas_antes = JogadorLuta.objects.all().values_list('id')
        lutas_ladder_antes = LutaLadder.objects.all().values_list('id')
        
        form = {'desafiante': self.sena.id, 'desafiado': self.teets.id, 'score_desafiante': 3, 'score_desafiado': 0, 
                                      'desafio_coringa': True, 'data_hora': timezone.make_naive(novo_horario)}
        
        formset_lutas = gerar_campos_formset([{'ganhador': self.sena.id, 'stage': self.stage.id, 
                                     'personagem_desafiante': self.fox.id, 'personagem_desafiado': self.fox.id},
                                    {'ganhador': self.sena.id, 'stage': self.stage.id, 
                                     'personagem_desafiante': self.marth.id, 'personagem_desafiado': self.fox.id},
                                    {'ganhador': self.sena.id, 'stage': self.stage.id, 
                                     'personagem_desafiante': self.marth.id, 'personagem_desafiado': self.fox.id}], 'desafio_ladder_luta')
#         (cls.sena, cls.saraiva, 1, 3, cls.horario_atual.replace(day=5), False, cls.sena)
        
        # Preparar dados POST
        dados_post = {**form, **formset_lutas}
        
        self.client.login(username=self.teets.user.username, password=SENHA_TESTE)
        response = self.client.post(reverse('ladder:editar_desafio_ladder', kwargs={'desafio_id': self.desafio_ladder_completo.id}),
                                   dados_post)
        self.assertEqual(response.status_code, 302)
        
        url_esperada = reverse('ladder:detalhar_desafio_ladder', kwargs={'desafio_id': self.desafio_ladder_completo.id})
        self.assertRedirects(response, url_esperada)
                             
        # Verificar mensagens
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), MENSAGEM_SUCESSO_EDITAR_DESAFIO_LADDER)
        
        # Verificar alterações em desafio
        self.desafio_ladder_completo = DesafioLadder.objects.get(id=self.desafio_ladder_completo.id)
        self.assertEqual(self.desafio_ladder_completo.desafiante, self.sena)
        self.assertEqual(self.desafio_ladder_completo.desafiado, self.teets)
        self.assertEqual(self.desafio_ladder_completo.score_desafiante, 3)
        self.assertEqual(self.desafio_ladder_completo.score_desafiado, 0)
        self.assertEqual(self.desafio_ladder_completo.desafio_coringa, True)
        self.assertEqual(self.desafio_ladder_completo.data_hora, novo_horario)
        self.assertEqual(self.desafio_ladder_completo.adicionado_por, self.sena)
        
        # Verificar alterações em lutas
        self.assertEqual(Luta.objects.count(), 3)
        self.assertEqual(JogadorLuta.objects.count(), 6)
        self.assertEqual(LutaLadder.objects.count(), 3)
        
        lutas = self.desafio_ladder_completo.lutaladder_set.all()
        self.assertEqual(lutas.count(), 3)
        
        # Luta 1
        luta_1 = lutas.get(indice_desafio_ladder=1).luta
        self.assertEqual(luta_1.ganhador, self.sena)
        self.assertEqual(luta_1.stage, self.stage)
        self.assertEqual(luta_1.data, self.desafio_ladder_completo.data_hora.date())
        self.assertEqual(luta_1.jogadorluta_set.all().count(), 2)
        self.assertIn((self.sena.id, self.fox.id), luta_1.jogadorluta_set.all().values_list('jogador', 'personagem'))
        self.assertIn((self.teets.id, self.fox.id), luta_1.jogadorluta_set.all().values_list('jogador', 'personagem'))
        
        # Luta 2
        luta_2 = lutas.get(indice_desafio_ladder=2).luta
        self.assertEqual(luta_2.ganhador, self.sena)
        self.assertEqual(luta_2.stage, self.stage)
        self.assertEqual(luta_2.data, self.desafio_ladder_completo.data_hora.date())
        self.assertEqual(luta_2.jogadorluta_set.all().count(), 2)
        self.assertIn((self.sena.id, self.marth.id), luta_2.jogadorluta_set.all().values_list('jogador', 'personagem'))
        self.assertIn((self.teets.id, self.fox.id), luta_2.jogadorluta_set.all().values_list('jogador', 'personagem'))
        
        # Luta 3
        luta_3 = lutas.get(indice_desafio_ladder=3).luta
        self.assertEqual(luta_3.ganhador, self.sena)
        self.assertEqual(luta_3.stage, self.stage)
        self.assertEqual(luta_3.data, self.desafio_ladder_completo.data_hora.date())
        self.assertEqual(luta_3.jogadorluta_set.all().count(), 2)
        self.assertIn((self.sena.id, self.marth.id), luta_3.jogadorluta_set.all().values_list('jogador', 'personagem'))
        self.assertIn((self.teets.id, self.fox.id), luta_3.jogadorluta_set.all().values_list('jogador', 'personagem'))
        
        # Verificar se nenhum novo modelo relacionado a luta foi criado
        lutas_apos = Luta.objects.all().values_list('id')
        for luta_id in lutas_apos:
            self.assertIn(luta_id, lutas_antes)
            
        jogador_lutas_apos = JogadorLuta.objects.all().values_list('id')
        for jogador_luta_id in jogador_lutas_apos:
            self.assertIn(jogador_luta_id, jogador_lutas_antes)
            
        lutas_ladder_apos = LutaLadder.objects.all().values_list('id')
        for luta_ladder_id in lutas_ladder_apos:
            self.assertIn(luta_ladder_id, lutas_ladder_antes)
            
    def test_editar_desafio_nao_validado_completo_sucesso_alterando_luta_meio(self):
        """Testa editar desafio de ladder completo não validado removendo luta do meio, com sucesso"""
        novo_horario = self.desafio_ladder_completo.data_hora - datetime.timedelta(days=1)
        
        # Verificar que existem apenas 4 lutas
        self.assertEqual(Luta.objects.count(), 4)
        self.assertEqual(JogadorLuta.objects.count(), 8)
        self.assertEqual(LutaLadder.objects.count(), 4)
        
        # Guardar ids dos modelos relacionados a luta para verificar posteriormente se nenhuma nova foi criada
        lutas_antes = Luta.objects.all().values_list('id')
        jogador_lutas_antes = JogadorLuta.objects.all().values_list('id')
        lutas_ladder_antes = LutaLadder.objects.all().values_list('id')
        
        form = {'desafiante': self.sena.id, 'desafiado': self.teets.id, 'score_desafiante': 3, 'score_desafiado': 0, 
                                      'desafio_coringa': True, 'data_hora': timezone.make_naive(novo_horario)}
        
        formset_lutas = gerar_campos_formset([{'ganhador': self.sena.id, 'stage': self.stage.id, 
                                     'personagem_desafiante': self.fox.id, 'personagem_desafiado': self.fox.id},
                                    {'ganhador': self.sena.id, 'stage': self.stage.id, 
                                     'personagem_desafiante': self.marth.id, 'personagem_desafiado': self.fox.id, 'DELETE': True},
                                    {'ganhador': self.sena.id, 'stage': self.stage.id, 
                                     'personagem_desafiante': self.marth.id, 'personagem_desafiado': self.fox.id}], 'desafio_ladder_luta')
#         (cls.sena, cls.saraiva, 1, 3, cls.horario_atual.replace(day=5), False, cls.sena)
        
        # Preparar dados POST
        dados_post = {**form, **formset_lutas}
        
        self.client.login(username=self.teets.user.username, password=SENHA_TESTE)
        response = self.client.post(reverse('ladder:editar_desafio_ladder', kwargs={'desafio_id': self.desafio_ladder_completo.id}),
                                   dados_post)
        self.assertEqual(response.status_code, 302)
        
        url_esperada = reverse('ladder:detalhar_desafio_ladder', kwargs={'desafio_id': self.desafio_ladder_completo.id})
        self.assertRedirects(response, url_esperada)
                             
        # Verificar mensagens
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), MENSAGEM_SUCESSO_EDITAR_DESAFIO_LADDER)
        
        # Verificar alterações em desafio
        self.desafio_ladder_completo = DesafioLadder.objects.get(id=self.desafio_ladder_completo.id)
        self.assertEqual(self.desafio_ladder_completo.desafiante, self.sena)
        self.assertEqual(self.desafio_ladder_completo.desafiado, self.teets)
        self.assertEqual(self.desafio_ladder_completo.score_desafiante, 3)
        self.assertEqual(self.desafio_ladder_completo.score_desafiado, 0)
        self.assertEqual(self.desafio_ladder_completo.desafio_coringa, True)
        self.assertEqual(self.desafio_ladder_completo.data_hora, novo_horario)
        self.assertEqual(self.desafio_ladder_completo.adicionado_por, self.sena)
        
        # Verificar alterações em lutas
        self.assertEqual(Luta.objects.count(), 2)
        self.assertEqual(JogadorLuta.objects.count(), 4)
        self.assertEqual(LutaLadder.objects.count(), 2)
        
        lutas = self.desafio_ladder_completo.lutaladder_set.all()
        self.assertEqual(lutas.count(), 2)
        
        # Luta 1
        luta_1 = lutas.get(indice_desafio_ladder=1).luta
        self.assertEqual(luta_1.ganhador, self.sena)
        self.assertEqual(luta_1.stage, self.stage)
        self.assertEqual(luta_1.data, self.desafio_ladder_completo.data_hora.date())
        self.assertEqual(luta_1.jogadorluta_set.all().count(), 2)
        self.assertIn((self.sena.id, self.fox.id), luta_1.jogadorluta_set.all().values_list('jogador', 'personagem'))
        self.assertIn((self.teets.id, self.fox.id), luta_1.jogadorluta_set.all().values_list('jogador', 'personagem'))
        
        # Luta 2
        self.assertFalse(lutas.filter(indice_desafio_ladder=2).exists())
        
        # Luta 3
        luta_3 = lutas.get(indice_desafio_ladder=3).luta
        self.assertEqual(luta_3.ganhador, self.sena)
        self.assertEqual(luta_3.stage, self.stage)
        self.assertEqual(luta_3.data, self.desafio_ladder_completo.data_hora.date())
        self.assertEqual(luta_3.jogadorluta_set.all().count(), 2)
        self.assertIn((self.sena.id, self.marth.id), luta_3.jogadorluta_set.all().values_list('jogador', 'personagem'))
        self.assertIn((self.teets.id, self.fox.id), luta_3.jogadorluta_set.all().values_list('jogador', 'personagem'))
        
        # Verificar se nenhum novo modelo relacionado a luta foi criado
        lutas_apos = Luta.objects.all().values_list('id')
        for luta_id in lutas_apos:
            self.assertIn(luta_id, lutas_antes)
            
        jogador_lutas_apos = JogadorLuta.objects.all().values_list('id')
        for jogador_luta_id in jogador_lutas_apos:
            self.assertIn(jogador_luta_id, jogador_lutas_antes)
            
        lutas_ladder_apos = LutaLadder.objects.all().values_list('id')
        for luta_ladder_id in lutas_ladder_apos:
            self.assertIn(luta_ladder_id, lutas_ladder_antes)
            
        
class ViewDetalharLutaTestCase(TestCase):
    """Testes para a view de detalhar uma luta"""
    @classmethod
    def setUpTestData(cls):
        super(ViewDetalharLutaTestCase, cls).setUpTestData()
        
        criar_jogadores_teste(['sena', 'teets'])
        
        cls.sena = Jogador.objects.get(nick='sena')
        cls.teets = Jogador.objects.get(nick='teets')
        
        cls.luta = criar_luta_teste([cls.sena, cls.teets], cls.sena, timezone.now().date(), cls.teets)
        
        # Preparar luta completa
        cls.stage_teste = criar_stage_teste()
        criar_personagens_teste()
        cls.fox = Personagem.objects.get(nome='Fox')
        cls.marth = Personagem.objects.get(nome='Marth')
        cls.luta_completa = criar_luta_completa_teste([cls.sena, cls.teets], [cls.marth, cls.fox], cls.sena, 
                                                      timezone.now().date(), cls.teets, cls.stage_teste)
        
        # Luta depende de um desafio válido para existir
        desafio_ladder = criar_desafio_ladder_simples_teste(cls.sena, cls.teets, 3, 1, timezone.now(), False, cls.teets)
        LutaLadder.objects.create(desafio_ladder=desafio_ladder, indice_desafio_ladder=1, luta=cls.luta)
        LutaLadder.objects.create(desafio_ladder=desafio_ladder, indice_desafio_ladder=2, luta=cls.luta_completa)
        
    def test_acesso_deslogado(self):
        """Testa acesso a tela de listar jogadores sem logar"""
        response = self.client.get(reverse('ladder:detalhar_luta', kwargs={'luta_id': self.luta.id}))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['luta'], self.luta)
        self.assertEqual(len(response.context['participantes']), 2)
        
        jogadores = [participante.jogador for participante in response.context['participantes']]
        self.assertIn(self.sena, jogadores)
        self.assertIn(self.teets, jogadores)
        
    def test_acesso_logado(self):
        """Testa acesso a tela de listar jogadores logado"""
        self.client.login(username=self.sena.user.username, password=SENHA_TESTE)
        response = self.client.get(reverse('ladder:detalhar_luta', kwargs={'luta_id': self.luta.id}))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['luta'], self.luta)
        self.assertEqual(len(response.context['participantes']), 2)
        
        jogadores = [participante.jogador for participante in response.context['participantes']]
        self.assertIn(self.sena, jogadores)
        self.assertIn(self.teets, jogadores)
        
    def test_detalhar_luta_completa(self):
        """Testa detalhamento de uma luta com tudo adicionado"""
        response = self.client.get(reverse('ladder:detalhar_luta', kwargs={'luta_id': self.luta_completa.id}))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['luta'].ganhador, self.sena)
        self.assertEqual(response.context['luta'].data, timezone.now().date())
        self.assertEqual(response.context['luta'].adicionada_por, self.teets)
        
        self.assertEqual(len(response.context['participantes']), 2)
        self.assertIn(JogadorLuta.objects.get(personagem=self.fox, jogador=self.teets, luta=self.luta_completa), 
                         response.context['participantes'])
        self.assertIn(JogadorLuta.objects.get(personagem=self.marth, jogador=self.sena, luta=self.luta_completa), 
                         response.context['participantes'])
        
class ViewDetalharDesafioLadderTestCase(TestCase):
    """Testes para a view de detalhar desafio da ladder"""
    @classmethod
    def setUpTestData(cls):
        super(ViewDetalharDesafioLadderTestCase, cls).setUpTestData()

        criar_jogadores_teste()
        
        criar_personagens_teste()
        
        criar_stage_teste()
        
        cls.sena = Jogador.objects.get(nick='sena')
        cls.teets = Jogador.objects.get(nick='teets')
        
        criar_ladder_teste()
        
        cls.desafio_ladder = criar_desafio_ladder_simples_teste(cls.sena, cls.teets, 3, 1, timezone.now(), False, cls.sena)
        
        cls.desafio_ladder_completo = criar_desafio_ladder_completo_teste(cls.sena, cls.teets, 3, 1, 
                                                                            timezone.now() - datetime.timedelta(minutes=1), False, cls.sena)
        
        # Preparar mês anterior para histórico
        data_atual = timezone.now().date()
        cls.ano = data_atual.year
        cls.mes = data_atual.month - 1
        if cls.mes == 0:
            cls.mes = 12
            cls.ano -= 1
        
        criar_ladder_historico_teste(cls.ano, cls.mes)
        
    def test_acesso_deslogado(self):
        """Testa acesso a tela de detalhar desafio da ladder sem logar"""
        response = self.client.get(reverse('ladder:detalhar_desafio_ladder', kwargs={'desafio_id': self.desafio_ladder.id}))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.desafio_ladder, response.context['desafio_ladder'])
        
        # Deve conter link para ladder
        self.assertContains(response, reverse('ladder:detalhar_ladder_atual'))
        
        # Não deve conter link para validação
        self.assertNotContains(response, reverse('ladder:validar_desafio_ladder', kwargs={'desafio_id': self.desafio_ladder.id}))
        
    def test_acesso_logado(self):
        """Testa acesso a tela de detalhar desafio da ladder logado sem ser admin"""
        self.client.login(username=self.sena.user.username, password=SENHA_TESTE)
        response = self.client.get(reverse('ladder:detalhar_desafio_ladder', kwargs={'desafio_id': self.desafio_ladder.id}))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.desafio_ladder, response.context['desafio_ladder'])
        
        # Deve conter link para ladder
        self.assertContains(response, reverse('ladder:detalhar_ladder_atual'))
        
        # Não deve conter link para validação
        self.assertNotContains(response, reverse('ladder:validar_desafio_ladder', kwargs={'desafio_id': self.desafio_ladder.id}))
        
    def test_acesso_logado_admin(self):
        """Testa acesso a tela de detalhar desafio da ladder logado como admin"""
        self.client.login(username=self.teets.user.username, password=SENHA_TESTE)
        response = self.client.get(reverse('ladder:detalhar_desafio_ladder', kwargs={'desafio_id': self.desafio_ladder.id}))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.desafio_ladder, response.context['desafio_ladder'])
        
        # Deve conter link para ladder
        self.assertContains(response, reverse('ladder:detalhar_ladder_atual'))
        
        # Deve conter link para validação
        self.assertContains(response, reverse('ladder:validar_desafio_ladder', kwargs={'desafio_id': self.desafio_ladder.id}))
        
    def test_desafio_ladder_historico(self):
        """Testa detalhamento de desafio de histórico de ladder"""
        self.desafio_ladder.data_hora = self.desafio_ladder.data_hora.replace(year=self.ano, month=self.mes)
        self.desafio_ladder.save()
        
        response = self.client.get(reverse('ladder:detalhar_desafio_ladder', kwargs={'desafio_id': self.desafio_ladder.id}))
        
        # Deve conter link para histórico de ladder
        self.assertContains(response, reverse('ladder:detalhar_ladder_historico', kwargs={'ano': self.desafio_ladder.data_hora.year,
                                                                                          'mes': self.desafio_ladder.data_hora.month}))
        
        
    def test_desafio_ladder_simples(self):
        """Testa detalhamento ddesafioro de ladder simples"""
        self.client.login(username=self.teets.user.username, password=SENHA_TESTE)
        response = self.client.get(reverse('ladder:detalhar_desafio_ladder', kwargs={'desafio_id': self.desafio_ladder.id}))
        self.assertEqual(response.status_code, 200)
        
        # Desafios simples não permitem detalhar lutas
        self.assertNotContains(response, 'Detalhar luta')
    
    def test_desafio_ladder_completo(self):
        """Testa detalhamento de desafio de ladder completo"""
        self.client.login(username=self.teets.user.username, password=SENHA_TESTE)
        response = self.client.get(reverse('ladder:detalhar_desafio_ladder', kwargs={'desafio_id': self.desafio_ladder_completo.id}))
        self.assertEqual(response.status_code, 200)
        
        # Verificar lutas do desafio
        desafio_ladder = response.context['desafio_ladder']
        lutas = [luta_ladder.luta for luta_ladder in desafio_ladder.lutaladder_set.all()]
        
        # Desafios completos permitem detalhar lutas
        for luta in lutas:
            self.assertContains(response, reverse('ladder:detalhar_luta', kwargs={'luta_id': luta.id}))
            
    def test_desafio_atual_nao_deve_conter_link_ladder_historico(self):
        """Testa acesso a tela de detalhar desafio da ladder sem logar"""
        response = self.client.get(reverse('ladder:detalhar_desafio_ladder', kwargs={'desafio_id': self.desafio_ladder.id}))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.desafio_ladder, response.context['desafio_ladder'])
        
        # Deve conter link para ladder
        self.assertNotContains(response, reverse('ladder:detalhar_ladder_historico', kwargs={'mes': self.desafio_ladder.data_hora.month, 
                                                                                             'ano': self.desafio_ladder.data_hora.year}))
        
        # Não deve conter link para validação
        self.assertNotContains(response, reverse('ladder:validar_desafio_ladder', kwargs={'desafio_id': self.desafio_ladder.id}))

class ViewDetalharLadderAtualTestCase(TestCase):
    """Testes para a view de listar jogadores"""
    # TODO adicionar testes para destaques
    @classmethod
    def setUpTestData(cls):
        super(ViewDetalharLadderAtualTestCase, cls).setUpTestData()
        cls.user = User.objects.create_user('teste', 'teste@teste.com', 'teste')
        
        criar_jogadores_teste()
        
        cls.sena = Jogador.objects.get(nick='sena')
        cls.teets = Jogador.objects.get(nick='teets')
        
        criar_ladder_teste()
        
    def test_acesso_deslogado(self):
        """Testa acesso a tela de listar jogadores sem logar"""
        response = self.client.get(reverse('ladder:detalhar_ladder_atual'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['ladder']), PosicaoLadder.objects.all().count())
        
        # Verificar se os nomes aparecem no html
        for nick in PosicaoLadder.objects.all().values_list('jogador__nick', flat=True):
            self.assertContains(response, nick)
        
    def test_acesso_logado(self):
        """Testa acesso a tela de listar jogadores logado"""
        self.client.login(username=self.user.username, password='teste')
        response = self.client.get(reverse('ladder:detalhar_ladder_atual'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['ladder']), PosicaoLadder.objects.all().count())
        
        # Verificar se os nomes aparecem no html
        for nick in PosicaoLadder.objects.all().values_list('jogador__nick', flat=True):
            self.assertContains(response, nick)
        
    def test_ordem_ladder(self):
        """Testar ordem da lista, as mais recentes devem vir primeiro"""
        response = self.client.get(reverse('ladder:detalhar_ladder_atual'))
        # Testar posição
        posicao = 1
        for jogador in response.context['ladder']:
            self.assertEqual(jogador.posicao, posicao)
            posicao += 1
            
    def test_jogador_de_ferias(self):
        """Testa se jogadores de férias estão com a classe para férias"""
        # Colocar 2 jogadores de férias
        RegistroFerias.objects.create(jogador=self.sena, data_inicio=timezone.now() - datetime.timedelta(days=5), 
                                      data_fim=timezone.now() + datetime.timedelta(days=5))
        RegistroFerias.objects.create(jogador=self.teets, data_inicio=timezone.now() - datetime.timedelta(days=5), 
                                      data_fim=timezone.now() + datetime.timedelta(days=5))
        
        response = self.client.get(reverse('ladder:detalhar_ladder_atual'))
        self.assertContains(response, 'title="Jogador está de férias"', 2)
        for jogador_posicao in response.context['ladder']:
            if jogador_posicao.jogador in [self.teets, self.sena]:
                self.assertTrue(jogador_posicao.jogador.is_de_ferias())
            else:
                self.assertFalse(jogador_posicao.jogador.is_de_ferias())
        
class ViewListarHistoricoLadderTestCase(TestCase):
    """Testes para a view de listar históricos de ladder"""
    @classmethod
    def setUpTestData(cls):
        super(ViewListarHistoricoLadderTestCase, cls).setUpTestData()
        
        criar_jogadores_teste()
        
        cls.sena = Jogador.objects.get(nick='sena')
        
        # Preparar mês anterior para histórico
        data_atual = timezone.now().date()
        cls.ano = data_atual.year
        cls.mes = data_atual.month - 1
        if cls.mes == 0:
            cls.mes = 12
            cls.ano -= 1
        
        criar_ladder_historico_teste(cls.ano, cls.mes)
        
    def test_acesso_deslogado(self):
        """Testa acesso a tela de listar jogadores sem logar"""
        response = self.client.get(reverse('ladder:listar_ladder_historico'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['lista_ladders']), HistoricoLadder.objects.filter(ano=self.ano, mes=self.mes).order_by('-ano', 'mes') \
                         .values('mes', 'ano').distinct().count())
        
    def test_acesso_logado(self):
        """Testa acesso a tela de listar jogadores logado"""
        self.client.login(username=self.sena.user.username, password='teste')
        response = self.client.get(reverse('ladder:listar_ladder_historico'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['lista_ladders']), HistoricoLadder.objects.filter(ano=self.ano, mes=self.mes).order_by('-ano', 'mes') \
                         .values('mes', 'ano').distinct().count())
        
    def test_sem_historicos(self):
        """Testa tela de erro ao verificar um histórico inexistente"""
        # Apagar histórico
        HistoricoLadder.objects.all().delete()
        
        response = self.client.get(reverse('ladder:listar_ladder_historico'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['lista_ladders']), 0)
        
    def test_ordem_ladder(self):
        """Testar ordem da lista, as mais recentes devem vir primeiro"""
        # Criar mais 1 ano de ladders, total de 13 meses
        ano = self.ano
        mes = self.mes
        for _ in range(12):
            mes -= 1
            if mes == 0:
                ano -= 1
                mes = 12
            criar_ladder_historico_teste(ano, mes)
            
        response = self.client.get(reverse('ladder:listar_ladder_historico'))
        
        # Testar ordem
        ano = self.ano
        mes = self.mes
        for ladder in response.context['lista_ladders']:
            self.assertEqual(ladder['ano'], ano)
            self.assertEqual(ladder['mes'], mes)
            
            # Atualizar mes e ano
            mes -= 1
            if mes == 0:
                ano -= 1
                mes = 12


class ViewDetalharHistoricoLadderTestCase(TestCase):
    """Testes para a view de detalhar histórico de ladder"""
    @classmethod
    def setUpTestData(cls):
        super(ViewDetalharHistoricoLadderTestCase, cls).setUpTestData()
        cls.user = User.objects.create_user('teste', 'teste@teste.com', 'teste')
        
        criar_jogadores_teste()
        
        # Preparar mês anterior para histórico
        data_atual = timezone.now().date()
        cls.ano = data_atual.year
        cls.mes = data_atual.month - 1
        if cls.mes == 0:
            cls.mes = 12
            cls.ano -= 1
        
        criar_ladder_historico_teste(cls.ano, cls.mes)
        
    def test_acesso_deslogado(self):
        """Testa acesso a tela de listar jogadores sem logar"""
        response = self.client.get(reverse('ladder:detalhar_ladder_historico', kwargs={'ano': self.ano, 'mes': self.mes}))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['ladder']), HistoricoLadder.objects.filter(ano=self.ano, mes=self.mes).count())
        
    def test_acesso_logado(self):
        """Testa acesso a tela de listar jogadores logado"""
        self.client.login(username=self.user.username, password='teste')
        response = self.client.get(reverse('ladder:detalhar_ladder_historico', kwargs={'ano': self.ano, 'mes': self.mes}))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['ladder']), HistoricoLadder.objects.filter(ano=self.ano, mes=self.mes).count())
        
    def test_historico_inexistente(self):
        """Testa tela de erro ao verificar um histórico inexistente"""
        response = self.client.get(reverse('ladder:detalhar_ladder_historico', kwargs={'ano': self.ano-1, 'mes': self.mes}))
        self.assertEqual(response.status_code, 404)
        
    def test_ordem_ladder(self):
        """Testar ordem da ladder"""
        response = self.client.get(reverse('ladder:detalhar_ladder_historico', kwargs={'ano': self.ano, 'mes': self.mes}))
        # Testar posição
        posicao = 1
        for jogador in response.context['ladder']:
            self.assertEqual(jogador.posicao, posicao)
            posicao += 1
    
class ViewDetalharRegrasTestCase(TestCase):
    """Testes para a view de detalhar regras da ladder"""
    @classmethod
    def setUpTestData(cls):
        super(ViewDetalharRegrasTestCase, cls).setUpTestData()
        cls.user = User.objects.create_user('teste', 'teste@teste.com', 'teste')
        
    def test_acesso_deslogado(self):
        """Testa acesso a tela de regras sem logar"""
        response = self.client.get(reverse('ladder:detalhar_regras_ladder'))
        self.assertEqual(response.status_code, 200)
        
    def test_acesso_logado(self):
        """Testa acesso a tela de regras logado"""
        self.client.login(username=self.user.username, password='teste')
        response = self.client.get(reverse('ladder:detalhar_regras_ladder'))
        self.assertEqual(response.status_code, 200)
        
class ViewListarDesafiosLadderPendentesValidacaoTestCase(TestCase):
    """Testes para a view de listar desafios de ladder pendentes de validar"""
    @classmethod
    def setUpTestData(cls):
        super(ViewListarDesafiosLadderPendentesValidacaoTestCase, cls).setUpTestData()
        
        criar_jogadores_teste()
        criar_personagens_teste()
        criar_stage_teste()
        
        cls.teets = Jogador.objects.get(nick='teets')
        cls.saraiva = Jogador.objects.get(nick='saraiva')
        cls.sena = Jogador.objects.get(nick='sena')
        cls.mad = Jogador.objects.get(nick='mad')
        
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
        
        # Desafios de ladder
        cls.desafio_ladder = criar_desafio_ladder_simples_teste(cls.mad, cls.saraiva, 2, 3, horario_atual, False, cls.sena)
        cls.desafio_ladder_completo = criar_desafio_ladder_completo_teste(cls.sena, cls.teets, 3, 1, horario_atual, False, cls.saraiva)
        
        horario_historico = horario_atual.replace(month=cls.mes, year=cls.ano)
        cls.desafio_ladder_historico = criar_desafio_ladder_simples_teste(cls.sena, cls.teets, 0, 3, horario_historico, False, cls.teets)
        
        cls.desafio_ladder_validado = criar_desafio_ladder_simples_teste(cls.saraiva, cls.teets, 0, 3, horario_atual + datetime.timedelta(minutes=1), False, cls.saraiva)
        validar_desafio_ladder_teste(cls.desafio_ladder_validado, cls.teets)
        
    def test_acesso_deslogado(self):
        """Testa acesso a tela de listar desafios de ladder pendentes sem logar"""
        response = self.client.get(reverse('ladder:listar_desafios_ladder_pendentes_validacao'))
        self.assertEqual(response.status_code, 200)
        
        # 3 desafios devem estar pendentes
        self.assertEqual(len(response.context['desafios_pendentes']), 3)
        self.assertIn(self.desafio_ladder, response.context['desafios_pendentes'])
        self.assertIn(self.desafio_ladder_completo, response.context['desafios_pendentes'])
        self.assertIn(self.desafio_ladder_historico, response.context['desafios_pendentes'])
        
        # Não permitir validar
        self.assertNotContains(response, reverse('ladder:validar_desafio_ladder', kwargs={'desafio_id': self.desafio_ladder.id}))
        self.assertNotContains(response, reverse('ladder:validar_desafio_ladder', kwargs={'desafio_id': self.desafio_ladder_completo.id}))
        self.assertNotContains(response, reverse('ladder:validar_desafio_ladder', kwargs={'desafio_id': self.desafio_ladder_historico.id}))
        
    def test_acesso_logado(self):
        """Testa acesso a tela de listar desafios de ladder pendentes logado"""
        self.client.login(username=self.sena.user.username, password=SENHA_TESTE)
        response = self.client.get(reverse('ladder:listar_desafios_ladder_pendentes_validacao'))
        self.assertEqual(response.status_code, 200)
        
        # 3 desafios devem estar pendentes
        self.assertEqual(len(response.context['desafios_pendentes']), 3)
        self.assertIn(self.desafio_ladder, response.context['desafios_pendentes'])
        self.assertIn(self.desafio_ladder_completo, response.context['desafios_pendentes'])
        self.assertIn(self.desafio_ladder_historico, response.context['desafios_pendentes'])
        
        # Não permitir validar
        self.assertNotContains(response, reverse('ladder:validar_desafio_ladder', kwargs={'desafio_id': self.desafio_ladder.id}))
        self.assertNotContains(response, reverse('ladder:validar_desafio_ladder', kwargs={'desafio_id': self.desafio_ladder_completo.id}))
        self.assertNotContains(response, reverse('ladder:validar_desafio_ladder', kwargs={'desafio_id': self.desafio_ladder_historico.id}))
        
    def test_acesso_logado_admin(self):
        """Testa acesso a tela de listar desafios de ladder pendentes logado como admin"""
        self.client.login(username=self.teets.user.username, password=SENHA_TESTE)
        response = self.client.get(reverse('ladder:listar_desafios_ladder_pendentes_validacao'))
        self.assertEqual(response.status_code, 200)
        
        # 3 desafios devem estar pendentes
        self.assertEqual(len(response.context['desafios_pendentes']), 3)
        self.assertIn(self.desafio_ladder, response.context['desafios_pendentes'])
        self.assertIn(self.desafio_ladder_completo, response.context['desafios_pendentes'])
        self.assertIn(self.desafio_ladder_historico, response.context['desafios_pendentes'])
        
        # Não permitir validar
        self.assertContains(response, reverse('ladder:validar_desafio_ladder', kwargs={'desafio_id': self.desafio_ladder.id}))
        self.assertContains(response, reverse('ladder:validar_desafio_ladder', kwargs={'desafio_id': self.desafio_ladder_completo.id}))
        self.assertContains(response, reverse('ladder:validar_desafio_ladder', kwargs={'desafio_id': self.desafio_ladder_historico.id}))
        
class ViewListarDesafiosLadderEspecificaTestCase(TestCase):
    """Testes para a view de listar desafios de uma ladder específica"""
    @classmethod
    def setUpTestData(cls):
        super(ViewListarDesafiosLadderEspecificaTestCase, cls).setUpTestData()
        
        criar_jogadores_teste()
        criar_personagens_teste()
        criar_stage_teste()
        
        cls.teets = Jogador.objects.get(nick='teets')
        cls.saraiva = Jogador.objects.get(nick='saraiva')
        cls.sena = Jogador.objects.get(nick='sena')
        cls.mad = Jogador.objects.get(nick='mad')
        
        criar_ladder_teste()
        
        # Preparar mês anterior para histórico
        horario_atual = timezone.now()
        cls.data_atual = horario_atual.date()
        cls.ano = cls.data_atual.year
        cls.mes = cls.data_atual.month - 1
        if cls.mes == 0:
            cls.mes = 12
            cls.ano -= 1
        
        criar_ladder_historico_teste(cls.ano, cls.mes)
        
        # Desafios de ladder
        cls.desafio_ladder = criar_desafio_ladder_simples_teste(cls.mad, cls.saraiva, 2, 3, horario_atual, False, cls.sena)
        cls.desafio_ladder_completo = criar_desafio_ladder_completo_teste(cls.sena, cls.teets, 3, 1, horario_atual + datetime.timedelta(minutes=1), False, cls.saraiva)
        
        horario_historico = horario_atual.replace(month=cls.mes, year=cls.ano)
        cls.desafio_ladder_historico = criar_desafio_ladder_simples_teste(cls.sena, cls.teets, 0, 3, horario_historico, False, cls.teets)
        
        cls.desafio_ladder_validado = criar_desafio_ladder_simples_teste(cls.saraiva, cls.teets, 0, 3, horario_atual + datetime.timedelta(minutes=2), False, cls.saraiva)
        validar_desafio_ladder_teste(cls.desafio_ladder_validado, cls.teets)
        
    def test_acesso_deslogado_ladder_atual(self):
        """Testa acesso a tela de listar desafios de ladder atual sem logar"""
        response = self.client.get(reverse('ladder:listar_desafios_ladder_atual'))
        self.assertEqual(response.status_code, 200)
        
        # 3 desafios devem estar na lista
        self.assertEqual(len(response.context['desafios_ladder']), 3)
        self.assertIn(self.desafio_ladder, response.context['desafios_ladder'])
        self.assertIn(self.desafio_ladder_completo, response.context['desafios_ladder'])
        self.assertIn(self.desafio_ladder_validado, response.context['desafios_ladder'])
        
        # Permitir detalhar
        self.assertContains(response, reverse('ladder:detalhar_desafio_ladder', kwargs={'desafio_id': self.desafio_ladder.id}))
        self.assertContains(response, reverse('ladder:detalhar_desafio_ladder', kwargs={'desafio_id': self.desafio_ladder_completo.id}))
        self.assertContains(response, reverse('ladder:detalhar_desafio_ladder', kwargs={'desafio_id': self.desafio_ladder_validado.id}))
        
    def test_acesso_logado_ladder_atual(self):
        """Testa acesso a tela de listar desafios de ladder atual logado"""
        self.client.login(username=self.sena.user.username, password=SENHA_TESTE)
        response = self.client.get(reverse('ladder:listar_desafios_ladder_atual'))
        self.assertEqual(response.status_code, 200)
        
        # 3 desafios devem estar na lista
        self.assertEqual(len(response.context['desafios_ladder']), 3)
        self.assertIn(self.desafio_ladder, response.context['desafios_ladder'])
        self.assertIn(self.desafio_ladder_completo, response.context['desafios_ladder'])
        self.assertIn(self.desafio_ladder_validado, response.context['desafios_ladder'])
        
        # Permitir detalhar
        self.assertContains(response, reverse('ladder:detalhar_desafio_ladder', kwargs={'desafio_id': self.desafio_ladder.id}))
        self.assertContains(response, reverse('ladder:detalhar_desafio_ladder', kwargs={'desafio_id': self.desafio_ladder_completo.id}))
        self.assertContains(response, reverse('ladder:detalhar_desafio_ladder', kwargs={'desafio_id': self.desafio_ladder_validado.id}))
        
    def test_acesso_logado_admin_ladder_atual(self):
        """Testa acesso a tela de listar desafios de ladder atual logado como admin"""
        self.client.login(username=self.teets.user.username, password=SENHA_TESTE)
        response = self.client.get(reverse('ladder:listar_desafios_ladder_atual'))
        self.assertEqual(response.status_code, 200)
        
        # 3 desafios devem estar na lista
        self.assertEqual(len(response.context['desafios_ladder']), 3)
        self.assertIn(self.desafio_ladder, response.context['desafios_ladder'])
        self.assertIn(self.desafio_ladder_completo, response.context['desafios_ladder'])
        self.assertIn(self.desafio_ladder_validado, response.context['desafios_ladder'])
        
        # Permitir detalhar
        self.assertContains(response, reverse('ladder:detalhar_desafio_ladder', kwargs={'desafio_id': self.desafio_ladder.id}))
        self.assertContains(response, reverse('ladder:detalhar_desafio_ladder', kwargs={'desafio_id': self.desafio_ladder_completo.id}))
        self.assertContains(response, reverse('ladder:detalhar_desafio_ladder', kwargs={'desafio_id': self.desafio_ladder_validado.id}))
        
    def test_acesso_deslogado_ladder_historico(self):
        """Testa acesso a tela de listar desafios de ladder histórica sem logar"""
        response = self.client.get(reverse('ladder:listar_desafios_ladder_historico', kwargs={'ano': self.ano, 'mes': self.mes}))
        self.assertEqual(response.status_code, 200)
        
        # 1 desafio devem estar na lista
        self.assertEqual(len(response.context['desafios_ladder']), 1)
        self.assertIn(self.desafio_ladder_historico, response.context['desafios_ladder'])
        
        # Permitir detalhar
        self.assertContains(response, reverse('ladder:detalhar_desafio_ladder', kwargs={'desafio_id': self.desafio_ladder_historico.id}))
        
    def test_acesso_logado_ladder_historico(self):
        """Testa acesso a tela de listar desafios de ladder histórica logado"""
        self.client.login(username=self.sena.user.username, password=SENHA_TESTE)
        response = self.client.get(reverse('ladder:listar_desafios_ladder_historico', kwargs={'ano': self.ano, 'mes': self.mes}))
        self.assertEqual(response.status_code, 200)
        
        # 1 desafio devem estar na lista
        self.assertEqual(len(response.context['desafios_ladder']), 1)
        self.assertIn(self.desafio_ladder_historico, response.context['desafios_ladder'])
        
        # Permitir detalhar
        self.assertContains(response, reverse('ladder:detalhar_desafio_ladder', kwargs={'desafio_id': self.desafio_ladder_historico.id}))
        
    def test_acesso_logado_admin_ladder_historico(self):
        """Testa acesso a tela de listar desafios de ladder histórica logado como admin"""
        self.client.login(username=self.teets.user.username, password=SENHA_TESTE)
        response = self.client.get(reverse('ladder:listar_desafios_ladder_historico', kwargs={'ano': self.ano, 'mes': self.mes}))
        self.assertEqual(response.status_code, 200)
        
        # 1 desafio devem estar na lista
        self.assertEqual(len(response.context['desafios_ladder']), 1)
        self.assertIn(self.desafio_ladder_historico, response.context['desafios_ladder'])
        
        # Permitir detalhar
        self.assertContains(response, reverse('ladder:detalhar_desafio_ladder', kwargs={'desafio_id': self.desafio_ladder_historico.id}))
        
    def test_erro_ano_futuro(self):
        """Testa erro caso seja informado ano futuro"""
        prox_mes = timezone.now().replace(day=calendar.monthrange(self.data_atual.year, self.data_atual.month)[1]) + datetime.timedelta(days=1)
        response = self.client.get(reverse('ladder:listar_desafios_ladder_historico', kwargs={'mes': prox_mes.month, 'ano':prox_mes.year}))
        self.assertEqual(response.status_code, 404)
        
    def test_erro_mes_invalido(self):
        """Testa erro caso apenas ano esteja preenchido"""
        response = self.client.get(reverse('ladder:listar_desafios_ladder_historico', kwargs={'ano': self.ano, 'mes': 0}))
        self.assertEqual(response.status_code, 404)
        
        response = self.client.get(reverse('ladder:listar_desafios_ladder_historico', kwargs={'ano': self.ano, 'mes': 13}))
        self.assertEqual(response.status_code, 404)
        