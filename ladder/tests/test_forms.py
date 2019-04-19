# -*- coding: utf-8 -*-
import datetime

from django.test import TestCase
from django.utils import timezone

from jogadores.models import Jogador, Personagem
from jogadores.tests.utils_teste import criar_jogadores_teste, \
    criar_jogador_teste, criar_stage_teste, criar_personagens_teste
from ladder.forms import RegistroLadderForm, RegistroLadderLutaForm
from ladder.models import RegistroLadder, HistoricoLadder, Luta
from ladder.tests.utils_teste import criar_ladder_teste, \
    criar_ladder_historico_teste, criar_registro_ladder_simples_teste
from django.db.utils import IntegrityError


class RegistroLadderFormTestCase(TestCase):
    """Testar form de adicionar registro da ladder"""
    @classmethod
    def setUpTestData(cls):
        super(RegistroLadderFormTestCase, cls).setUpTestData()
         
        # Configurar jogador
        criar_jogadores_teste()
        
        criar_ladder_teste()
        
         
        cls.mad = Jogador.objects.get(user__username='mad') # 4 na ladder
        cls.sena = Jogador.objects.get(user__username='sena') # 3 na ladder
        cls.teets = Jogador.objects.get(user__username='teets') # 1 na ladder
        cls.new = criar_jogador_teste('new') # Novo entrande na ladder
        
        # Preparar mês anterior para histórico
        data_atual = timezone.now().date()
        cls.ano = data_atual.year
        cls.mes = data_atual.month - 1
        if cls.mes == 0:
            cls.mes = 12
            cls.ano -= 1
            
        criar_ladder_historico_teste(cls.ano, cls.mes)
         
         
    def test_form_adicionar_registro_com_sucesso(self):
        """Testa adicionar registro com sucesso"""
        self.assertFalse(RegistroLadder.objects.filter(desafiante=self.sena).exists())
        
        hora_atual = timezone.now()
        
        form = RegistroLadderForm({'desafiante': self.sena.id, 'desafiado': self.teets.id, 'score_desafiante': 3, 'score_desafiado': 2, 
                                      'desafio_coringa': False, 'data_hora': hora_atual, 'adicionado_por': self.sena.id})
        self.assertTrue(form.is_valid())
        # Usar commit=False como nas views
        registro_ladder = form.save(commit=False)
        registro_ladder.save()
         
        # Buscar registro
        registro_ladder = RegistroLadder.objects.get(desafiante=self.sena)
        self.assertEqual(registro_ladder.desafiante, self.sena)
        self.assertEqual(registro_ladder.desafiado, self.teets)
        self.assertEqual(registro_ladder.score_desafiante, 3)
        self.assertEqual(registro_ladder.score_desafiado, 2)
        self.assertEqual(registro_ladder.desafio_coringa, False)
        self.assertEqual(registro_ladder.data_hora, hora_atual)
        self.assertEqual(registro_ladder.adicionado_por, self.sena)
        self.assertEqual(registro_ladder.admin_validador, None)
        
    def test_form_adicionar_registro_historico_com_sucesso(self):
        """Testa adicionar registro com sucesso em ladder no histórico"""
        self.assertFalse(RegistroLadder.objects.filter(desafiante=self.sena).exists())
        
        hora_mes_passado = timezone.now().replace(month=self.mes, year=self.ano)
        
        form = RegistroLadderForm({'desafiante': self.sena.id, 'desafiado': self.teets.id, 'score_desafiante': 3, 'score_desafiado': 2, 
                                      'desafio_coringa': False, 'data_hora': hora_mes_passado, 'adicionado_por': self.sena.id})
        self.assertTrue(form.is_valid())
        # Usar commit=False como nas views
        registro_ladder = form.save(commit=False)
        registro_ladder.save()
         
        # Buscar registro
        registro_ladder = RegistroLadder.objects.get(desafiante=self.sena)
        self.assertEqual(registro_ladder.desafiante, self.sena)
        self.assertEqual(registro_ladder.desafiado, self.teets)
        self.assertEqual(registro_ladder.score_desafiante, 3)
        self.assertEqual(registro_ladder.score_desafiado, 2)
        self.assertEqual(registro_ladder.desafio_coringa, False)
        self.assertEqual(registro_ladder.data_hora, hora_mes_passado)
        self.assertEqual(registro_ladder.adicionado_por, self.sena)
        self.assertEqual(registro_ladder.admin_validador, None)
        
    def test_form_adicionar_registro_coringa_com_sucesso(self):
        """Testa adicionar registro usando coringa com sucesso"""
        self.assertFalse(RegistroLadder.objects.filter(desafiante=self.mad).exists())
        
        hora_atual = timezone.now()
        
        form = RegistroLadderForm({'desafiante': self.mad.id, 'desafiado': self.teets.id, 'score_desafiante': 3, 'score_desafiado': 2, 
                                      'desafio_coringa': True, 'data_hora': hora_atual, 'adicionado_por': self.mad.id})
        self.assertTrue(form.is_valid())
        # Usar commit=False como nas views
        registro_ladder = form.save(commit=False)
        registro_ladder.save()
         
        # Buscar registro
        registro_ladder = RegistroLadder.objects.get(desafiante=self.mad)
        self.assertEqual(registro_ladder.desafiante, self.mad)
        self.assertEqual(registro_ladder.desafiado, self.teets)
        self.assertEqual(registro_ladder.score_desafiante, 3)
        self.assertEqual(registro_ladder.score_desafiado, 2)
        self.assertEqual(registro_ladder.desafio_coringa, True)
        self.assertEqual(registro_ladder.data_hora, hora_atual)
        self.assertEqual(registro_ladder.adicionado_por, self.mad)
        self.assertEqual(registro_ladder.admin_validador, None)
        
    def test_form_adicionar_registro_coringa_novo_entrante_com_sucesso(self):
        """Testa adicionar registro usando coringa para desafiante novo entrante, com sucesso"""
        self.assertFalse(RegistroLadder.objects.filter(desafiante=self.new).exists())
        
        hora_atual = timezone.now()
        
        form = RegistroLadderForm({'desafiante': self.new.id, 'desafiado': self.teets.id, 'score_desafiante': 3, 'score_desafiado': 2, 
                                      'desafio_coringa': True, 'data_hora': hora_atual, 'adicionado_por': self.new.id})
        self.assertTrue(form.is_valid())
        # Usar commit=False como nas views
        registro_ladder = form.save(commit=False)
        registro_ladder.save()
         
        # Buscar registro
        registro_ladder = RegistroLadder.objects.get(desafiante=self.new)
        self.assertEqual(registro_ladder.desafiante, self.new)
        self.assertEqual(registro_ladder.desafiado, self.teets)
        self.assertEqual(registro_ladder.score_desafiante, 3)
        self.assertEqual(registro_ladder.score_desafiado, 2)
        self.assertEqual(registro_ladder.desafio_coringa, True)
        self.assertEqual(registro_ladder.data_hora, hora_atual)
        self.assertEqual(registro_ladder.adicionado_por, self.new)
        self.assertEqual(registro_ladder.admin_validador, None)
        
 
    def test_form_erro_desafiante_mais_que_2_abaixo(self):
        """Testa adição de desafio feito por um desafiante mais de 2 posições abaixo do desafiado"""
        form = RegistroLadderForm({'desafiante': self.mad.id, 'desafiado': self.teets.id, 'score_desafiante': 3, 'score_desafiado': 2, 
                                      'desafio_coringa': False, 'data_hora': timezone.now(), 'adicionado_por': self.sena.id})
        self.assertFalse(form.is_valid())
        
        self.assertIn(f'Desafiante está mais de {RegistroLadder.LIMITE_POSICOES_DESAFIO} posições abaixo do desafiado', form.errors['__all__'])
        self.assertTrue(len(form.errors) == 1)
        
    def test_form_sucesso_desafiante_mais_que_2_abaixo_coringa(self):
        """Testa adição de desafio feito por um desafiante mais de 2 posições abaixo com coringa"""
        hora_atual = timezone.now()
        
        form = RegistroLadderForm({'desafiante': self.mad.id, 'desafiado': self.teets.id, 'score_desafiante': 3, 'score_desafiado': 2, 
                                      'desafio_coringa': True, 'data_hora': hora_atual, 'adicionado_por': self.teets.id})
        self.assertTrue(form.is_valid())
        # Usar commit=False como nas views
        registro_ladder = form.save(commit=False)
        registro_ladder.save()
         
        # Buscar registro
        registro_ladder = RegistroLadder.objects.get(desafiante=self.mad)
        self.assertEqual(registro_ladder.desafiante, self.mad)
        self.assertEqual(registro_ladder.desafiado, self.teets)
        self.assertEqual(registro_ladder.score_desafiante, 3)
        self.assertEqual(registro_ladder.score_desafiado, 2)
        self.assertEqual(registro_ladder.desafio_coringa, True)
        self.assertEqual(registro_ladder.data_hora, hora_atual)
        self.assertEqual(registro_ladder.adicionado_por, self.teets)
        self.assertEqual(registro_ladder.admin_validador, None)
        
    def test_form_erro_adicionado_terceiro_nao_admin(self):
        """Testa adição de desafio feita por um terceiro não admin"""
        form = RegistroLadderForm({'desafiante': self.sena.id, 'desafiado': self.teets.id, 'score_desafiante': 3, 'score_desafiado': 2, 
                                      'desafio_coringa': False, 'data_hora': timezone.now(), 'adicionado_por': self.mad.id})
          
        self.assertFalse(form.is_valid())
        self.assertIn('Jogador não pode criar registros para ladder para terceiros', form.errors['__all__'])
        self.assertTrue(len(form.errors) == 1)
        
    def test_form_sucesso_adicionado_terceiro_admin(self):
        """Testa adição de desafio feita por um admin não participante"""
        hora_atual = timezone.now()
        
        form = RegistroLadderForm({'desafiante': self.mad.id, 'desafiado': self.sena.id, 'score_desafiante': 3, 'score_desafiado': 2, 
                                      'desafio_coringa': False, 'data_hora': hora_atual, 'adicionado_por': self.teets.id}, admin=self.teets.admin)
        self.assertTrue(form.is_valid())
        # Usar commit=False como nas views
        registro_ladder = form.save(commit=False)
        registro_ladder.save()
         
        # Buscar registro
        registro_ladder = RegistroLadder.objects.get(desafiante=self.mad)
        self.assertEqual(registro_ladder.desafiante, self.mad)
        self.assertEqual(registro_ladder.desafiado, self.sena)
        self.assertEqual(registro_ladder.score_desafiante, 3)
        self.assertEqual(registro_ladder.score_desafiado, 2)
        self.assertEqual(registro_ladder.desafio_coringa, False)
        self.assertEqual(registro_ladder.data_hora, hora_atual)
        self.assertEqual(registro_ladder.adicionado_por, self.teets)
        self.assertEqual(registro_ladder.admin_validador, None)
        
    def test_form_erro_data_hora_futura(self):
        """Testa adição de desafio feita em horário futuro"""
        hora_futura = timezone.now() + datetime.timedelta(hours=1)
        form = RegistroLadderForm({'desafiante': self.sena.id, 'desafiado': self.teets.id, 'score_desafiante': 3, 'score_desafiado': 2, 
                                      'desafio_coringa': False, 'data_hora': hora_futura, 'adicionado_por': self.sena.id})
          
        self.assertFalse(form.is_valid())
        self.assertIn('data_hora', form.errors)
        self.assertTrue(len(form.errors) == 1)
        
    def test_form_erro_score_menor_que_3(self):
        """Testa adição de desafio com resultado em que ambos não alcançaram 3 pontos"""
        form = RegistroLadderForm({'desafiante': self.sena.id, 'desafiado': self.teets.id, 'score_desafiante': 2, 'score_desafiado': 1, 
                                      'desafio_coringa': False, 'data_hora': timezone.now(), 'adicionado_por': self.sena.id})
          
        self.assertFalse(form.is_valid())
        self.assertIn('Resultado impossível para melhor de 5', form.errors['__all__'])
        self.assertTrue(len(form.errors) == 1)
    
    def test_form_erro_periodo_espera_insuficiente(self):
        """Testa adição de desafio sem respeitar período de espera entre mesmos jogadores"""
        # Gerar desafio passado
        RegistroLadder.objects.create(desafiante=self.sena, desafiado=self.teets, score_desafiante=1, score_desafiado=3,
                                      desafio_coringa=False, data_hora=(timezone.now() - datetime.timedelta(days=3)), adicionado_por=self.teets)
        
        form = RegistroLadderForm({'desafiante': self.sena.id, 'desafiado': self.teets.id, 'score_desafiante': 3, 'score_desafiado': 1, 
                                      'desafio_coringa': False, 'data_hora': timezone.now(), 'adicionado_por': self.sena.id})
        self.assertFalse(form.is_valid())

        self.assertIn(RegistroLadder.MENSAGEM_ERRO_PERIODO_ESPERA_MESMOS_JOGADORES, form.errors['__all__'])
        self.assertTrue(len(form.errors) == 1)
        
    def test_form_erro_add_para_ladder_historico_inexistente(self):
        """Testa adição de desafio em um mês no passado em que não existia ladder"""
        data_ano_anterior = timezone.now().replace(year=timezone.now().year-1)
        form = RegistroLadderForm({'desafiante': self.sena.id, 'desafiado': self.teets.id, 'score_desafiante': 3, 'score_desafiado': 2, 
                                      'desafio_coringa': False, 'data_hora': data_ano_anterior, 'adicionado_por': self.sena.id})
        self.assertFalse(form.is_valid())
        
        self.assertIn(HistoricoLadder.MENSAGEM_LADDER_MES_ANO_INEXISTENTE, form.errors['__all__'])
        self.assertTrue(len(form.errors) == 1)
        
    def test_form_erro_desafiante_igual_desafiado(self):
        """Testa adição de desafio no qual desafiante e desafiado são o mesmo jogador"""
        form = RegistroLadderForm({'desafiante': self.sena.id, 'desafiado': self.sena.id, 'score_desafiante': 3, 'score_desafiado': 2, 
                                      'desafio_coringa': False, 'data_hora': timezone.now(), 'adicionado_por': self.sena.id})
        self.assertFalse(form.is_valid())
        
        self.assertIn(RegistroLadder.MENSAGEM_ERRO_MESMO_JOGADOR, form.errors['__all__'])
        self.assertTrue(len(form.errors) == 1)
        
    def test_form_erro_desafiante_usou_coringa_periodo_menor_limite(self):
        """Testa adição de desafio coringa para desafiante que o usou há um período inferior ao mínimo"""
        hora_atual = timezone.now()
        # Adicionar uso de coringa para desafiante há 1 dia a menos que o período de espera
        self.mad.ultimo_uso_coringa = hora_atual - datetime.timedelta(days=RegistroLadder.PERIODO_ESPERA_DESAFIO_CORINGA - 1)
        self.mad.save()
        
        form = RegistroLadderForm({'desafiante': self.mad.id, 'desafiado': self.teets.id, 'score_desafiante': 3, 'score_desafiado': 2, 
                                      'desafio_coringa': True, 'data_hora': hora_atual, 'adicionado_por': self.teets.id}, admin=self.teets.admin)
        self.assertFalse(form.is_valid())
        
        self.assertIn(RegistroLadder.MENSAGEM_ERRO_PERIODO_ESPERA_CORINGA, form.errors['__all__'])
        self.assertTrue(len(form.errors) == 1)
        
    def test_form_erro_desafiante_usou_coringa_periodo_igual_limite(self):
        """Testa adição de desafio coringa para desafiante que o usou há um período igual ao mínimo"""
        hora_atual = timezone.now()
        # Adicionar uso de coringa para desafiante há 1 dia a menos que o período de espera
        self.mad.ultimo_uso_coringa = hora_atual - datetime.timedelta(days=RegistroLadder.PERIODO_ESPERA_DESAFIO_CORINGA)
        self.mad.save()
        
        form = RegistroLadderForm({'desafiante': self.mad.id, 'desafiado': self.teets.id, 'score_desafiante': 3, 'score_desafiado': 2, 
                                      'desafio_coringa': True, 'data_hora': hora_atual, 'adicionado_por': self.teets.id})
        form.is_valid()
        self.assertTrue(form.is_valid())
        
    def test_form_erro_desafiante_usou_coringa_periodo_maior_limite(self):
        """Testa adição de desafio coringa para desafiante que o usou há um período superior ao mínimo"""
        hora_atual = timezone.now()
        # Adicionar uso de coringa para desafiante há 1 dia a menos que o período de espera
        self.mad.ultimo_uso_coringa = hora_atual - datetime.timedelta(days=RegistroLadder.PERIODO_ESPERA_DESAFIO_CORINGA + 1)
        self.mad.save()
        
        form = RegistroLadderForm({'desafiante': self.mad.id, 'desafiado': self.teets.id, 'score_desafiante': 3, 'score_desafiado': 2, 
                                      'desafio_coringa': True, 'data_hora': hora_atual, 'adicionado_por': self.teets.id})
        self.assertTrue(form.is_valid())
        
class RegistroLadderLutaFormTestCase(TestCase):
    """Testar form de adicionar registro da ladder"""
    @classmethod
    def setUpTestData(cls):
        super(RegistroLadderLutaFormTestCase, cls).setUpTestData()
         
        # Configurar jogador
        criar_jogadores_teste()
        cls.sena = Jogador.objects.get(user__username='sena') 
        cls.teets = Jogador.objects.get(user__username='teets') 
                
        # Stage
        cls.stage = criar_stage_teste()
        
        # Personagens
        criar_personagens_teste()   
        cls.marth = Personagem.objects.get(nome='Marth')
        cls.fox = Personagem.objects.get(nome='Fox')     
        
        cls.horario_atual = timezone.now()
        cls.registro_ladder = criar_registro_ladder_simples_teste(cls.sena, cls.teets, 3, 1, cls.horario_atual, False, cls.sena)
         
    def test_form_adicionar_luta_com_sucesso(self):
        """Testa adicionar luta de registro de ladder com sucesso"""
        self.assertFalse(Luta.objects.all().exists())
        
        form = RegistroLadderLutaForm({'ganhador': self.sena.id, 'stage': self.stage.id, 'personagem_desafiante': self.marth.id,
                                       'personagem_desafiado': self.fox.id})
        self.assertTrue(form.is_valid())
        # Usar commit=False como nas views
        luta = form.save(commit=False)
        
        # Ganhador e stage devem estar definidos
        self.assertEqual(luta.ganhador, self.sena)
        self.assertEqual(luta.stage, self.stage)
        
        # É possível salvar objeto ao adicionar adicionada_por e data
        luta.adicionada_por = self.sena
        luta.data = self.horario_atual.date()
        luta.save()
        
        # Buscar campos personagem
        self.assertEqual(form.cleaned_data['personagem_desafiante'], self.marth)
        self.assertEqual(form.cleaned_data['personagem_desafiado'], self.fox)
        
    def test_form_adicionar_luta_com_sucesso_sem_stage_e_personagem(self):
        """Testa adicionar luta de registro de ladder sem stage e personagem, com sucesso"""
        self.assertFalse(Luta.objects.all().exists())
        
        form = RegistroLadderLutaForm({'ganhador': self.sena.id, 'stage': None, 'personagem_desafiante': None, 
                                       'personagem_desafiado': None})
        self.assertTrue(form.is_valid())
        # Usar commit=False como nas views
        luta = form.save(commit=False)
        
        # Ganhador e stage devem estar definidos
        self.assertEqual(luta.ganhador, self.sena)
        self.assertEqual(luta.stage, None)
        
        # É possível salvar objeto ao adicionar adicionada_por e data
        luta.adicionada_por = self.sena
        luta.data = self.horario_atual.date()
        luta.save()
        
        # Buscar campo personagem
        self.assertEqual(form.cleaned_data['personagem_desafiante'], None)
        self.assertEqual(form.cleaned_data['personagem_desafiado'], None)
