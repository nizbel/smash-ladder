# -*- coding: utf-8 -*-
import datetime

from django.test import TestCase
from django.utils import timezone

from jogadores.models import Jogador, Personagem, StageValidaLadder
from jogadores.tests.utils_teste import criar_jogadores_teste, \
    criar_jogador_teste, criar_stage_teste, criar_personagens_teste
from ladder.forms import DesafioLadderForm, DesafioLadderLutaForm, \
    RemocaoJogadorForm
from ladder.models import DesafioLadder, HistoricoLadder, Luta, RemocaoJogador, \
    PermissaoAumentoRange
from ladder.tests.utils_teste import criar_ladder_teste, \
    criar_ladder_historico_teste, criar_desafio_ladder_simples_teste, \
    validar_desafio_ladder_teste
from ladder.utils import remover_jogador
from smashLadder.utils import mes_ano_ant


class DesafioLadderFormTestCase(TestCase):
    """Testar form de adicionar desafio da ladder"""
    @classmethod
    def setUpTestData(cls):
        super(DesafioLadderFormTestCase, cls).setUpTestData()
         
        # Configurar jogador
        criar_jogadores_teste()
        
        criar_ladder_teste()
        
         
        cls.jogador_pos_5 = Jogador.objects.get(user__username='blower') # 5 na ladder
        cls.jogador_pos_4 = Jogador.objects.get(user__username='mad') # 4 na ladder
        cls.jogador_pos_7 = Jogador.objects.get(user__username='dan') # 7 na ladder
        cls.jogador_pos_8 = Jogador.objects.get(user__username='phils') # 8 na ladder
        cls.teets = Jogador.objects.get(user__username='teets') # 1 na ladder
        cls.new = criar_jogador_teste('new') # Novo entrande na ladder
        
        # Preparar mês anterior para histórico
        data_atual = timezone.localtime().date()
        cls.mes, cls.ano = mes_ano_ant(data_atual.month, data_atual.year)
            
        criar_ladder_historico_teste(cls.ano, cls.mes)
         
         
    def test_form_adicionar_desafio_com_sucesso(self):
        """Testa adicionar desafio com sucesso"""
        self.assertFalse(DesafioLadder.objects.filter(desafiante=self.jogador_pos_4).exists())
        
        hora_atual = timezone.localtime()
        
        form = DesafioLadderForm({'desafiante': self.jogador_pos_4.id, 'desafiado': self.teets.id, 'score_desafiante': 3, 'score_desafiado': 2, 
                                      'desafio_coringa': False, 'data_hora': hora_atual, 'adicionado_por': self.jogador_pos_4.id})
        self.assertTrue(form.is_valid())
        # Usar commit=False como nas views
        desafio_ladder = form.save(commit=False)
        desafio_ladder.save()
         
        # Buscar desafio
        desafio_ladder = DesafioLadder.objects.get(desafiante=self.jogador_pos_4)
        self.assertEqual(desafio_ladder.desafiante, self.jogador_pos_4)
        self.assertEqual(desafio_ladder.desafiado, self.teets)
        self.assertEqual(desafio_ladder.score_desafiante, 3)
        self.assertEqual(desafio_ladder.score_desafiado, 2)
        self.assertEqual(desafio_ladder.desafio_coringa, False)
        self.assertEqual(desafio_ladder.data_hora, hora_atual)
        self.assertEqual(desafio_ladder.adicionado_por, self.jogador_pos_4)
        self.assertEqual(desafio_ladder.admin_validador, None)
        
    def test_form_adicionar_desafio_historico_com_sucesso(self):
        """Testa adicionar desafio com sucesso em ladder no histórico"""
        self.assertFalse(DesafioLadder.objects.filter(desafiante=self.jogador_pos_4).exists())
        
        hora_mes_passado = timezone.localtime().replace(month=self.mes, year=self.ano)
        
        form = DesafioLadderForm({'desafiante': self.jogador_pos_4.id, 'desafiado': self.teets.id, 'score_desafiante': 3, 'score_desafiado': 2, 
                                      'desafio_coringa': False, 'data_hora': hora_mes_passado, 'adicionado_por': self.jogador_pos_4.id})
        self.assertTrue(form.is_valid())
        # Usar commit=False como nas views
        desafio_ladder = form.save(commit=False)
        desafio_ladder.save()
         
        # Buscar desafio
        desafio_ladder = DesafioLadder.objects.get(desafiante=self.jogador_pos_4)
        self.assertEqual(desafio_ladder.desafiante, self.jogador_pos_4)
        self.assertEqual(desafio_ladder.desafiado, self.teets)
        self.assertEqual(desafio_ladder.score_desafiante, 3)
        self.assertEqual(desafio_ladder.score_desafiado, 2)
        self.assertEqual(desafio_ladder.desafio_coringa, False)
        self.assertEqual(desafio_ladder.data_hora, hora_mes_passado)
        self.assertEqual(desafio_ladder.adicionado_por, self.jogador_pos_4)
        self.assertEqual(desafio_ladder.admin_validador, None)
        
    def test_form_adicionar_desafio_coringa_com_sucesso(self):
        """Testa adicionar desafio usando coringa com sucesso"""
        self.assertFalse(DesafioLadder.objects.filter(desafiante=self.jogador_pos_5).exists())
        
        hora_atual = timezone.localtime()
        
        form = DesafioLadderForm({'desafiante': self.jogador_pos_5.id, 'desafiado': self.teets.id, 'score_desafiante': 3, 'score_desafiado': 2, 
                                      'desafio_coringa': True, 'data_hora': hora_atual, 'adicionado_por': self.jogador_pos_5.id})
        self.assertTrue(form.is_valid())
        # Usar commit=False como nas views
        desafio_ladder = form.save(commit=False)
        desafio_ladder.save()
         
        # Buscar desafio
        desafio_ladder = DesafioLadder.objects.get(desafiante=self.jogador_pos_5)
        self.assertEqual(desafio_ladder.desafiante, self.jogador_pos_5)
        self.assertEqual(desafio_ladder.desafiado, self.teets)
        self.assertEqual(desafio_ladder.score_desafiante, 3)
        self.assertEqual(desafio_ladder.score_desafiado, 2)
        self.assertEqual(desafio_ladder.desafio_coringa, True)
        self.assertEqual(desafio_ladder.data_hora, hora_atual)
        self.assertEqual(desafio_ladder.adicionado_por, self.jogador_pos_5)
        self.assertEqual(desafio_ladder.admin_validador, None)
        
    def test_form_adicionar_desafio_coringa_novo_entrante_com_sucesso(self):
        """Testa adicionar desafio usando coringa para desafiante novo entrante, com sucesso"""
        self.assertFalse(DesafioLadder.objects.filter(desafiante=self.new).exists())
        
        hora_atual = timezone.localtime()
        
        form = DesafioLadderForm({'desafiante': self.new.id, 'desafiado': self.teets.id, 'score_desafiante': 3, 'score_desafiado': 2, 
                                      'desafio_coringa': True, 'data_hora': hora_atual, 'adicionado_por': self.new.id})
        self.assertTrue(form.is_valid())
        # Usar commit=False como nas views
        desafio_ladder = form.save(commit=False)
        desafio_ladder.save()
         
        # Buscar desafio
        desafio_ladder = DesafioLadder.objects.get(desafiante=self.new)
        self.assertEqual(desafio_ladder.desafiante, self.new)
        self.assertEqual(desafio_ladder.desafiado, self.teets)
        self.assertEqual(desafio_ladder.score_desafiante, 3)
        self.assertEqual(desafio_ladder.score_desafiado, 2)
        self.assertEqual(desafio_ladder.desafio_coringa, True)
        self.assertEqual(desafio_ladder.data_hora, hora_atual)
        self.assertEqual(desafio_ladder.adicionado_por, self.new)
        self.assertEqual(desafio_ladder.admin_validador, None)
        
 
    def test_form_erro_desafiante_mais_que_qtd_abaixo(self):
        """Testa adição de desafio feito por um desafiante mais de LIMITE_POSICOES_DESAFIO posições abaixo do desafiado"""
        form = DesafioLadderForm({'desafiante': self.jogador_pos_5.id, 'desafiado': self.teets.id, 'score_desafiante': 3, 'score_desafiado': 2, 
                                      'desafio_coringa': False, 'data_hora': timezone.localtime(), 'adicionado_por': self.jogador_pos_4.id})
        self.assertFalse(form.is_valid())
        
        self.assertIn(f'Desafiante está mais de {DesafioLadder.LIMITE_POSICOES_DESAFIO} posições abaixo do desafiado', form.errors['__all__'])
        self.assertTrue(len(form.errors) == 1)
        
    def test_form_sucesso_desafiante_mais_que_qtd_abaixo_coringa(self):
        """Testa adição de desafio feito por um desafiante mais de LIMITE_POSICOES_DESAFIO posições abaixo com coringa"""
        hora_atual = timezone.localtime()
        
        form = DesafioLadderForm({'desafiante': self.jogador_pos_5.id, 'desafiado': self.teets.id, 'score_desafiante': 3, 'score_desafiado': 2, 
                                      'desafio_coringa': True, 'data_hora': hora_atual, 'adicionado_por': self.teets.id})
        self.assertTrue(form.is_valid())
        # Usar commit=False como nas views
        desafio_ladder = form.save(commit=False)
        desafio_ladder.save()
         
        # Buscar desafio
        desafio_ladder = DesafioLadder.objects.get(desafiante=self.jogador_pos_5)
        self.assertEqual(desafio_ladder.desafiante, self.jogador_pos_5)
        self.assertEqual(desafio_ladder.desafiado, self.teets)
        self.assertEqual(desafio_ladder.score_desafiante, 3)
        self.assertEqual(desafio_ladder.score_desafiado, 2)
        self.assertEqual(desafio_ladder.desafio_coringa, True)
        self.assertEqual(desafio_ladder.data_hora, hora_atual)
        self.assertEqual(desafio_ladder.adicionado_por, self.teets)
        self.assertEqual(desafio_ladder.admin_validador, None)
        
    def test_form_sucesso_desafiante_mais_que_qtd_abaixo_dentro_aumento_range(self):
        """Testa adição de desafio feito por um desafiante mais de LIMITE_POSICOES_DESAFIO, mas menor que LIMITE_POSICOES_DESAFIO + AUMENTO_RANGE posições abaixo"""
        hora_atual = timezone.localtime()
        
        # Adicionando aumento de range
        PermissaoAumentoRange.objects.create(jogador=self.jogador_pos_7, admin_permissor=self.teets, data_hora=(hora_atual - datetime.timedelta(hours=1)))
        
        form = DesafioLadderForm({'desafiante': self.jogador_pos_7.id, 'desafiado': self.teets.id, 'score_desafiante': 3, 'score_desafiado': 2, 
                                      'desafio_coringa': False, 'data_hora': hora_atual, 'adicionado_por': self.teets.id})
        self.assertTrue(form.is_valid())
        # Usar commit=False como nas views
        desafio_ladder = form.save(commit=False)
        desafio_ladder.save()
         
        # Buscar desafio
        desafio_ladder = DesafioLadder.objects.get(desafiante=self.jogador_pos_7)
        self.assertEqual(desafio_ladder.desafiante, self.jogador_pos_7)
        self.assertEqual(desafio_ladder.desafiado, self.teets)
        self.assertEqual(desafio_ladder.score_desafiante, 3)
        self.assertEqual(desafio_ladder.score_desafiado, 2)
        self.assertEqual(desafio_ladder.desafio_coringa, False)
        self.assertEqual(desafio_ladder.data_hora, hora_atual)
        self.assertEqual(desafio_ladder.adicionado_por, self.teets)
        self.assertEqual(desafio_ladder.admin_validador, None)
        
    def test_form_sucesso_desafiante_mais_que_qtd_abaixo_fora_aumento_range(self):
        """Testa adição de desafio feito por um desafiante mais de LIMITE_POSICOES_DESAFIO + AUMENTO_RANGE posições abaixo"""
        hora_atual = timezone.localtime()
        
        # Adicionando aumento de range
        PermissaoAumentoRange.objects.create(jogador=self.jogador_pos_8, admin_permissor=self.teets, data_hora=(hora_atual - datetime.timedelta(hours=1)))
        
        form = DesafioLadderForm({'desafiante': self.jogador_pos_8.id, 'desafiado': self.teets.id, 'score_desafiante': 3, 'score_desafiado': 2, 
                                      'desafio_coringa': False, 'data_hora': hora_atual, 'adicionado_por': self.teets.id})
        self.assertFalse(form.is_valid())
        self.assertIn(PermissaoAumentoRange.MENSAGEM_ERRO_DESAFIANTE_MUITO_ABAIXO_DESAFIADO, form.errors['__all__'])
        self.assertTrue(len(form.errors) == 1)
        
    def test_form_sucesso_desafiante_mais_que_qtd_abaixo_aumento_range_invalido(self):
        """Testa adição de desafio feito por um desafiante mais de LIMITE_POSICOES_DESAFIO posições abaixo, com aumento de range já inválido"""
        hora_atual = timezone.localtime()
        
        # Adicionando aumento de range
        PermissaoAumentoRange.objects.create(jogador=self.jogador_pos_7, admin_permissor=self.teets, 
            data_hora=(hora_atual - datetime.timedelta(hours=(PermissaoAumentoRange.PERIODO_VALIDADE + 1))))
        
        form = DesafioLadderForm({'desafiante': self.jogador_pos_7.id, 'desafiado': self.teets.id, 'score_desafiante': 3, 'score_desafiado': 2, 
                                      'desafio_coringa': False, 'data_hora': hora_atual, 'adicionado_por': self.teets.id})
        self.assertFalse(form.is_valid())
        self.assertIn(f'Desafiante está mais de {DesafioLadder.LIMITE_POSICOES_DESAFIO} posições abaixo do desafiado', form.errors['__all__'])
        self.assertTrue(len(form.errors) == 1)
        
    def test_form_erro_adicionado_terceiro_nao_admin(self):
        """Testa adição de desafio feita por um terceiro não admin"""
        form = DesafioLadderForm({'desafiante': self.jogador_pos_4.id, 'desafiado': self.teets.id, 'score_desafiante': 3, 'score_desafiado': 2, 
                                      'desafio_coringa': False, 'data_hora': timezone.localtime(), 'adicionado_por': self.jogador_pos_5.id})
          
        self.assertFalse(form.is_valid())
        self.assertIn('Jogador não pode criar desafios para ladder para terceiros', form.errors['__all__'])
        self.assertTrue(len(form.errors) == 1)
        
    def test_form_sucesso_adicionado_terceiro_admin(self):
        """Testa adição de desafio feita por um admin não participante"""
        hora_atual = timezone.localtime()
        
        form = DesafioLadderForm({'desafiante': self.jogador_pos_5.id, 'desafiado': self.jogador_pos_4.id, 'score_desafiante': 3, 'score_desafiado': 2, 
                                      'desafio_coringa': False, 'data_hora': hora_atual, 'adicionado_por': self.teets.id}, admin=self.teets.admin)
        self.assertTrue(form.is_valid())
        # Usar commit=False como nas views
        desafio_ladder = form.save(commit=False)
        desafio_ladder.save()
         
        # Buscar desafio
        desafio_ladder = DesafioLadder.objects.get(desafiante=self.jogador_pos_5)
        self.assertEqual(desafio_ladder.desafiante, self.jogador_pos_5)
        self.assertEqual(desafio_ladder.desafiado, self.jogador_pos_4)
        self.assertEqual(desafio_ladder.score_desafiante, 3)
        self.assertEqual(desafio_ladder.score_desafiado, 2)
        self.assertEqual(desafio_ladder.desafio_coringa, False)
        self.assertEqual(desafio_ladder.data_hora, hora_atual)
        self.assertEqual(desafio_ladder.adicionado_por, self.teets)
        self.assertEqual(desafio_ladder.admin_validador, None)
        
    def test_form_erro_data_hora_futura(self):
        """Testa adição de desafio feita em horário futuro"""
        hora_futura = timezone.localtime() + datetime.timedelta(hours=1)
        form = DesafioLadderForm({'desafiante': self.jogador_pos_4.id, 'desafiado': self.teets.id, 'score_desafiante': 3, 'score_desafiado': 2, 
                                      'desafio_coringa': False, 'data_hora': hora_futura, 'adicionado_por': self.jogador_pos_4.id})
          
        self.assertFalse(form.is_valid())
        self.assertIn('data_hora', form.errors)
        self.assertTrue(len(form.errors) == 1)
        
    def test_form_erro_score_menor_que_3(self):
        """Testa adição de desafio com resultado em que ambos não alcançaram 3 pontos"""
        form = DesafioLadderForm({'desafiante': self.jogador_pos_4.id, 'desafiado': self.teets.id, 'score_desafiante': 2, 'score_desafiado': 1, 
                                      'desafio_coringa': False, 'data_hora': timezone.localtime(), 'adicionado_por': self.jogador_pos_4.id})
          
        self.assertFalse(form.is_valid())
        self.assertIn('Resultado impossível para melhor de 5', form.errors['__all__'])
        self.assertTrue(len(form.errors) == 1)
    
    def test_form_erro_periodo_espera_insuficiente(self):
        """Testa adição de desafio sem respeitar período de espera entre mesmos jogadores"""
        # Gerar desafio passado
        DesafioLadder.objects.create(desafiante=self.jogador_pos_4, desafiado=self.teets, score_desafiante=1, score_desafiado=3,
                                      desafio_coringa=False, 
                                      data_hora=(timezone.localtime() - datetime.timedelta(days=DesafioLadder.PERIODO_ESPERA_MESMOS_JOGADORES-1)), 
                                      adicionado_por=self.teets)
        
        form = DesafioLadderForm({'desafiante': self.jogador_pos_4.id, 'desafiado': self.teets.id, 'score_desafiante': 3, 'score_desafiado': 1, 
                                      'desafio_coringa': False, 'data_hora': timezone.localtime(), 'adicionado_por': self.jogador_pos_4.id})
        self.assertFalse(form.is_valid())

        self.assertIn(DesafioLadder.MENSAGEM_ERRO_PERIODO_ESPERA_MESMOS_JOGADORES, form.errors['__all__'])
        self.assertTrue(len(form.errors) == 1)
        
    def test_form_erro_add_para_ladder_historico_inexistente(self):
        """Testa adição de desafio em um mês no passado em que não existia ladder"""
        data_ano_anterior = timezone.localtime().replace(year=timezone.localtime().year-1)
        form = DesafioLadderForm({'desafiante': self.jogador_pos_4.id, 'desafiado': self.teets.id, 'score_desafiante': 3, 'score_desafiado': 2, 
                                      'desafio_coringa': False, 'data_hora': data_ano_anterior, 'adicionado_por': self.jogador_pos_4.id})
        self.assertFalse(form.is_valid())
        
        self.assertIn(HistoricoLadder.MENSAGEM_LADDER_MES_ANO_INEXISTENTE, form.errors['__all__'])
        self.assertTrue(len(form.errors) == 1)
        
    def test_form_erro_desafiante_igual_desafiado(self):
        """Testa adição de desafio no qual desafiante e desafiado são o mesmo jogador"""
        form = DesafioLadderForm({'desafiante': self.jogador_pos_4.id, 'desafiado': self.jogador_pos_4.id, 'score_desafiante': 3, 'score_desafiado': 2, 
                                      'desafio_coringa': False, 'data_hora': timezone.localtime(), 'adicionado_por': self.jogador_pos_4.id})
        self.assertFalse(form.is_valid())
        
        self.assertIn(DesafioLadder.MENSAGEM_ERRO_MESMO_JOGADOR, form.errors['__all__'])
        self.assertTrue(len(form.errors) == 1)
        
    def test_form_erro_desafiante_usou_coringa_periodo_menor_limite(self):
        """Testa adição de desafio coringa para desafiante que o usou há um período inferior ao mínimo"""
        hora_atual = timezone.localtime()
        # Adicionar uso de coringa para desafiante há 1 dia a menos que o período de espera
        self.jogador_pos_5.ultimo_uso_coringa = hora_atual - datetime.timedelta(days=DesafioLadder.PERIODO_ESPERA_DESAFIO_CORINGA - 1)
        self.jogador_pos_5.save()
        
        form = DesafioLadderForm({'desafiante': self.jogador_pos_5.id, 'desafiado': self.teets.id, 'score_desafiante': 3, 'score_desafiado': 2, 
                                      'desafio_coringa': True, 'data_hora': hora_atual, 'adicionado_por': self.teets.id}, admin=self.teets.admin)
        self.assertFalse(form.is_valid())
        
        self.assertIn(DesafioLadder.MENSAGEM_ERRO_PERIODO_ESPERA_CORINGA, form.errors['__all__'])
        self.assertTrue(len(form.errors) == 1)
        
    def test_form_erro_desafiante_usou_coringa_periodo_igual_limite(self):
        """Testa adição de desafio coringa para desafiante que o usou há um período igual ao mínimo"""
        hora_atual = timezone.localtime()
        # Adicionar uso de coringa para desafiante há 1 dia a menos que o período de espera
        self.jogador_pos_5.ultimo_uso_coringa = hora_atual - datetime.timedelta(days=DesafioLadder.PERIODO_ESPERA_DESAFIO_CORINGA)
        self.jogador_pos_5.save()
        
        form = DesafioLadderForm({'desafiante': self.jogador_pos_5.id, 'desafiado': self.teets.id, 'score_desafiante': 3, 'score_desafiado': 2, 
                                      'desafio_coringa': True, 'data_hora': hora_atual, 'adicionado_por': self.teets.id})
        form.is_valid()
        self.assertTrue(form.is_valid())
        
    def test_form_erro_desafiante_usou_coringa_periodo_maior_limite(self):
        """Testa adição de desafio coringa para desafiante que o usou há um período superior ao mínimo"""
        hora_atual = timezone.localtime()
        # Adicionar uso de coringa para desafiante há 1 dia a menos que o período de espera
        self.jogador_pos_5.ultimo_uso_coringa = hora_atual - datetime.timedelta(days=DesafioLadder.PERIODO_ESPERA_DESAFIO_CORINGA + 1)
        self.jogador_pos_5.save()
        
        form = DesafioLadderForm({'desafiante': self.jogador_pos_5.id, 'desafiado': self.teets.id, 'score_desafiante': 3, 'score_desafiado': 2, 
                                      'desafio_coringa': True, 'data_hora': hora_atual, 'adicionado_por': self.teets.id})
        self.assertTrue(form.is_valid())
        
    def test_form_erro_remocao_participante_mesma_data(self):
        """Testa erro ao cadastrar desafio em data que um dos participantes esteja sendo removido"""
        hora_atual = timezone.localtime()
        # Gerar remoção
        remover_jogador(RemocaoJogador.objects.create(jogador=self.jogador_pos_4, data=hora_atual, 
                                      admin_removedor=self.teets, 
                                      posicao_jogador=self.jogador_pos_4.posicao_em(hora_atual)))
        
        # Tentar gerar desafio
        form = DesafioLadderForm({'desafiante': self.jogador_pos_4.id, 'desafiado': self.teets.id, 'score_desafiante': 3, 'score_desafiado': 2, 
                                      'desafio_coringa': False, 'data_hora': hora_atual, 'adicionado_por': self.teets.id})
        self.assertFalse(form.is_valid())
        
        self.assertIn(f'{self.jogador_pos_4} é removido da ladder na data especificada', form.errors['__all__'])
        
class DesafioLadderLutaFormTestCase(TestCase):
    """Testar form de adicionar desafio da ladder"""
    @classmethod
    def setUpTestData(cls):
        super(DesafioLadderLutaFormTestCase, cls).setUpTestData()
         
        # Configurar jogador
        criar_jogadores_teste()
        cls.sena = Jogador.objects.get(user__username='sena') 
        cls.teets = Jogador.objects.get(user__username='teets') 
                
        # Stage
        cls.stage = criar_stage_teste()
        # Configurar stage como válida
        StageValidaLadder.objects.create(stage=cls.stage)
        
        # Personagens
        criar_personagens_teste()   
        cls.marth = Personagem.objects.get(nome='Marth')
        cls.fox = Personagem.objects.get(nome='Fox')     
        
        cls.horario_atual = timezone.localtime()
        cls.desafio_ladder = criar_desafio_ladder_simples_teste(cls.sena, cls.teets, 3, 1, cls.horario_atual, False, cls.sena)
         
    def test_form_adicionar_luta_com_sucesso(self):
        """Testa adicionar luta de desafio de ladder com sucesso"""
        self.assertFalse(Luta.objects.all().exists())
        
        form = DesafioLadderLutaForm({'ganhador': self.sena.id, 'stage': self.stage.id, 'personagem_desafiante': self.marth.id,
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
        """Testa adicionar luta de desafio de ladder sem stage e personagem, com sucesso"""
        self.assertFalse(Luta.objects.all().exists())
        
        form = DesafioLadderLutaForm({'ganhador': self.sena.id, 'stage': None, 'personagem_desafiante': None, 
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
        
class RemocaoJogadorFormTestCase(TestCase):
    """Testar form de adicionar desafio da ladder"""
    @classmethod
    def setUpTestData(cls):
        super(RemocaoJogadorFormTestCase, cls).setUpTestData()
         
        # Configurar jogador
        criar_jogadores_teste()
        
        criar_ladder_teste()
        
         
        cls.mad = Jogador.objects.get(user__username='mad') # 4 na ladder
        cls.sena = Jogador.objects.get(user__username='sena') # 3 na ladder
        cls.teets = Jogador.objects.get(user__username='teets') # 1 na ladder
        cls.tiovsky = Jogador.objects.get(user__username='tiovsky') # 10 na ladder
        cls.new = criar_jogador_teste('new') # Novo entrande na ladder
        
        # Preparar mês anterior para histórico
        cls.horario_atual = timezone.localtime()
        cls.mes, cls.ano = mes_ano_ant(cls.horario_atual.month, cls.horario_atual.year)
            
        criar_ladder_historico_teste(cls.ano, cls.mes)
         
         
    def test_form_remover_jogador_meio_ladder_com_sucesso(self):
        """Testa remover um jogador no meio da ladder com sucesso"""
        self.assertFalse(RemocaoJogador.objects.filter(jogador=self.mad).exists())
        
        form = RemocaoJogadorForm({'jogador': self.mad.id, 'data': self.horario_atual, 'admin_removedor': self.teets.id})
        self.assertTrue(form.is_valid())
        # Usar commit=False como nas views
        remocao_jogador = form.save(commit=False)
        remocao_jogador.save()
         
        # Buscar desafio
        remocao_jogador = RemocaoJogador.objects.get(jogador=self.mad)
        self.assertEqual(remocao_jogador.jogador, self.mad)
        self.assertEqual(remocao_jogador.data, self.horario_atual)
        self.assertEqual(remocao_jogador.admin_removedor, self.teets)
        self.assertEqual(remocao_jogador.posicao_jogador, 4)
        
    def test_form_remover_jogador_fim_ladder_com_sucesso(self):
        """Testa remover um jogador no final da ladder com sucesso"""
        self.assertFalse(RemocaoJogador.objects.filter(jogador=self.teets).exists())
        
        form = RemocaoJogadorForm({'jogador': self.teets.id, 'data': self.horario_atual, 'admin_removedor': self.teets.id})
        self.assertTrue(form.is_valid())
        # Usar commit=False como nas views
        remocao_jogador = form.save(commit=False)
        remocao_jogador.save()
         
        # Buscar desafio
        remocao_jogador = RemocaoJogador.objects.get(jogador=self.teets)
        self.assertEqual(remocao_jogador.jogador, self.teets)
        self.assertEqual(remocao_jogador.data, self.horario_atual)
        self.assertEqual(remocao_jogador.admin_removedor, self.teets)
        self.assertEqual(remocao_jogador.posicao_jogador, 1)
        
    def test_form_remover_jogador_topo_ladder_com_sucesso(self):
        """Testa remover um jogador do topo da ladder com sucesso"""
        self.assertFalse(RemocaoJogador.objects.filter(jogador=self.tiovsky).exists())
        
        form = RemocaoJogadorForm({'jogador': self.tiovsky.id, 'data': self.horario_atual, 'admin_removedor': self.teets.id})
        self.assertTrue(form.is_valid())
        # Usar commit=False como nas views
        remocao_jogador = form.save(commit=False)
        remocao_jogador.save()
         
        # Buscar desafio
        remocao_jogador = RemocaoJogador.objects.get(jogador=self.tiovsky)
        self.assertEqual(remocao_jogador.jogador, self.tiovsky)
        self.assertEqual(remocao_jogador.data, self.horario_atual)
        self.assertEqual(remocao_jogador.admin_removedor, self.teets)
        self.assertEqual(remocao_jogador.posicao_jogador, 10)
        
    def test_erro_remover_jogador_com_desafio_no_mesmo_dia(self):
        """Testa erro ao remover jogador que tenha um desafio no mesmo dia"""
        # Gerar desafio e validar
        desafio_ladder = criar_desafio_ladder_simples_teste(self.sena, self.teets, 3, 1, self.horario_atual, False, self.teets)
        validar_desafio_ladder_teste(desafio_ladder, self.teets)
        
        form = RemocaoJogadorForm({'jogador': self.tiovsky.id, 'data': self.horario_atual, 'admin_removedor': self.teets.id})
        self.assertFalse(form.is_valid())
        
        self.assertIn('Jogador possui desafio na data apontada para remoção', form.errors['__all__'])
        
    def test_erro_remover_jogador_fora_da_ladder(self):
        """Testa erro ao tentar remover novo entrante"""
        form = RemocaoJogadorForm({'jogador': self.new.id, 'data': self.horario_atual, 'admin_removedor': self.teets.id})
        self.assertFalse(form.is_valid())
        
        self.assertIn('Jogador não estava presente na ladder na data especificada', form.errors['__all__'])
        
    def test_erro__remover_jogador_sem_ser_admin(self):
        """Testa erro ao tentar remover jogador sem ser admin"""
        form = RemocaoJogadorForm({'jogador': self.tiovsky.id, 'data': self.horario_atual, 'admin_removedor': self.sena.id})
        self.assertFalse(form.is_valid())
        
        self.assertIn('Responsável pela remoção deve ser admin', form.errors['__all__'])
        
    def test_remover_jogador_ladder_historica(self):
        """Testa remover jogador de ladde histórico com sucesso"""
        self.assertFalse(RemocaoJogador.objects.filter(jogador=self.mad).exists())
        
        form = RemocaoJogadorForm({'jogador': self.mad.id, 'data': self.horario_atual.replace(month=self.mes, year=self.ano), 
                                   'admin_removedor': self.teets.id})
        self.assertTrue(form.is_valid())
        # Usar commit=False como nas views
        remocao_jogador = form.save(commit=False)
        remocao_jogador.save()
         
        # Buscar desafio
        remocao_jogador = RemocaoJogador.objects.get(jogador=self.mad)
        self.assertEqual(remocao_jogador.jogador, self.mad)
        self.assertEqual(remocao_jogador.data, self.horario_atual.replace(month=self.mes, year=self.ano))
        self.assertEqual(remocao_jogador.admin_removedor, self.teets)
        self.assertEqual(remocao_jogador.posicao_jogador, 4)
