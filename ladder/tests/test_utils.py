# -*- coding: utf-8 -*-
import datetime
import re

from django.test.testcases import TestCase
from django.utils import timezone

from jogadores.models import Jogador, RegistroFerias
from jogadores.tests.utils_teste import criar_jogadores_teste, \
    criar_jogador_teste
from ladder.models import PosicaoLadder, HistoricoLadder, RegistroLadder, \
    CancelamentoRegistroLadder
from ladder.tests.utils_teste import criar_ladder_teste, \
    criar_ladder_historico_teste, criar_registro_ladder_simples_teste, \
    validar_registro_ladder_teste, criar_ladder_inicial_teste
from ladder.utils import verificar_posicoes_desafiante_desafiado, alterar_ladder, \
    recalcular_ladder


class AlterarLadderTestCase(TestCase):
    """Testes para a função de alterar posições na ladder"""
    @classmethod
    def setUpTestData(cls):
        super(AlterarLadderTestCase, cls).setUpTestData()
        
        criar_jogadores_teste()
        
        # Pegar objetos de jogador de acordo com sua posição
        cls.jogador_pos_1 = Jogador.objects.get(nick='teets')
        cls.jogador_pos_2 = Jogador.objects.get(nick='saraiva')
        cls.jogador_pos_3 = Jogador.objects.get(nick='sena')
        cls.jogador_pos_4 = Jogador.objects.get(nick='mad')
        cls.jogador_pos_5 = Jogador.objects.get(nick='blöwer')
        cls.jogador_pos_6 = Jogador.objects.get(nick='frodo')
        cls.jogador_pos_7 = Jogador.objects.get(nick='dan')
        cls.jogador_pos_10 = Jogador.objects.get(nick='tiovsky')
        
        # Jogadores para validar alterações no ranking
        cls.jogadores = [cls.jogador_pos_1, cls.jogador_pos_2,
                         cls.jogador_pos_3, cls.jogador_pos_4,
                         cls.jogador_pos_5, cls.jogador_pos_6,
                         cls.jogador_pos_7]
        
        # Criar ladders para verificar que adicionar registro não as afeta
        criar_ladder_teste()
        
        # Preparar mês anterior para histórico
        data_atual = timezone.now().date()
        cls.ano = data_atual.year
        cls.mes = data_atual.month - 1
        if cls.mes == 0:
            cls.mes = 12
            cls.ano -= 1
        
        criar_ladder_historico_teste(cls.ano, cls.mes)
        
        # Criar novo entrante
        cls.new = criar_jogador_teste('new')
        
        horario_atual = timezone.now()
        horario_historico = horario_atual.replace(month=cls.mes, year=cls.ano)
        
        cls.registro_ladder = criar_registro_ladder_simples_teste(cls.jogador_pos_3, cls.jogador_pos_1, 3, 1, 
                                                                          horario_atual, False, cls.jogador_pos_1)
        cls.registro_ladder_derrota = criar_registro_ladder_simples_teste(cls.jogador_pos_7, cls.jogador_pos_6, 0, 3, 
                                                                          horario_atual, False, cls.jogador_pos_1)
        cls.registro_ladder_historico = criar_registro_ladder_simples_teste(cls.jogador_pos_3, cls.jogador_pos_2, 3, 1, 
                                                                          horario_historico, True, cls.jogador_pos_1)
        cls.registro_ladder_historico_derrota = criar_registro_ladder_simples_teste(cls.jogador_pos_6, cls.jogador_pos_5, 0, 3, 
                                                                          horario_historico, True, cls.jogador_pos_1)
        
        # Desafios coringa
        cls.registro_ladder_coringa = criar_registro_ladder_simples_teste(cls.jogador_pos_7, cls.jogador_pos_1, 3, 1, 
                                                                          horario_atual, False, cls.jogador_pos_1)
        cls.registro_ladder_historico_coringa = criar_registro_ladder_simples_teste(cls.jogador_pos_6, cls.jogador_pos_2, 3, 1, 
                                                                          horario_historico, True, cls.jogador_pos_1)
        
        # Desafios de novo entrante
        cls.registro_ladder_novo_entrante_vitoria = criar_registro_ladder_simples_teste(cls.new, cls.jogador_pos_10, 3, 1, 
                                                                          horario_atual.replace(day=15), False, cls.jogador_pos_1)
        cls.registro_ladder_novo_entrante_derrota = criar_registro_ladder_simples_teste(cls.new, cls.jogador_pos_10, 0, 3, 
                                                                          horario_atual.replace(day=5), False, cls.jogador_pos_1)
        
    def test_alterar_ladder_atual_vitoria(self):
        """Testa alterar ladder atual por um registro de vitória"""
        # Pegar situação da ladder antes
        ladder_antes = list(PosicaoLadder.objects.all().order_by('posicao').values_list('jogador', 'posicao'))
        
        # Jogador 3 ganhou de jogador 1
        alterar_ladder(self.registro_ladder)
        
        # Pegar situação da ladder após
        ladder_apos = list(PosicaoLadder.objects.all().order_by('posicao').values_list('jogador', 'posicao'))
        
        # Tamanho da ladder deve ser o mesmo
        self.assertEqual(len(ladder_antes), len(ladder_apos))
        
        # 3 primeiras posições devem ter mudado
        self.assertIn((self.jogador_pos_3.id, 1), ladder_apos)
        self.assertIn((self.jogador_pos_1.id, 2), ladder_apos)
        self.assertIn((self.jogador_pos_2.id, 3), ladder_apos)
        
        # Outras permanecem
        for situacao_antes, situacao_apos in zip(ladder_antes[3:], ladder_apos[3:]):
            self.assertEqual(situacao_antes, situacao_apos)
        
    def test_alterar_ladder_historico_vitoria(self):
        """Testa alterar ladder histórico por um registro de vitória"""
        # Pegar situação da ladder antes
        ladder_antes = list(HistoricoLadder.objects.filter(ano=self.ano, mes=self.mes).order_by('posicao').values_list('jogador', 'posicao'))
        
        # Jogador 3 ganhou de jogador 2
        alterar_ladder(self.registro_ladder_historico)
        
        # Pegar situação da ladder após
        ladder_apos = list(HistoricoLadder.objects.filter(ano=self.ano, mes=self.mes).order_by('posicao').values_list('jogador', 'posicao'))
        
        # Tamanho da ladder deve ser o mesmo
        self.assertEqual(len(ladder_antes), len(ladder_apos))
        
        # 2 primeiras posições devem ter mudado
        self.assertIn((self.jogador_pos_3.id, 2), ladder_apos)
        self.assertIn((self.jogador_pos_2.id, 3), ladder_apos)
        
        # Outras permanecem
        for situacao_antes, situacao_apos in zip(ladder_antes[3:], ladder_apos[3:]):
            self.assertEqual(situacao_antes, situacao_apos)
    
    def test_nao_alterar_ladder_atual_derrota(self):
        """Testa não alterar ladder atual por um registro de derrota"""
        # Pegar situação da ladder antes
        ladder_antes = list(PosicaoLadder.objects.all().order_by('posicao').values_list('jogador', 'posicao'))
        
        alterar_ladder(self.registro_ladder_derrota)
        
        # Pegar situação da ladder após
        ladder_apos = list(PosicaoLadder.objects.all().order_by('posicao').values_list('jogador', 'posicao'))
        
        for situacao_antes, situacao_apos in zip(ladder_antes, ladder_apos):
            self.assertEqual(situacao_antes, situacao_apos)
    
    def test_nao_alterar_ladder_historico_derrota(self):
        """Testa não alterar ladder histórico por um registro de derrota"""
        # Pegar situação da ladder antes
        ladder_antes = list(HistoricoLadder.objects.filter(ano=self.ano, mes=self.mes).order_by('posicao').values_list('jogador', 'posicao'))
        
        alterar_ladder(self.registro_ladder_historico_derrota)
        
        # Pegar situação da ladder após
        ladder_apos = list(HistoricoLadder.objects.filter(ano=self.ano, mes=self.mes).order_by('posicao').values_list('jogador', 'posicao'))
        
        for situacao_antes, situacao_apos in zip(ladder_antes, ladder_apos):
            self.assertEqual(situacao_antes, situacao_apos)
    
    def test_alterar_ladder_atual_vitoria_coringa(self):
        """Testa alterar ladder atual por um registro de vitória de desafio coringa"""
        # Pegar situação da ladder antes
        ladder_antes = list(PosicaoLadder.objects.all().order_by('posicao').values_list('jogador', 'posicao'))
        
        # Jogador 7 ganhou de jogador 1
        alterar_ladder(self.registro_ladder_coringa)
        
        # Pegar situação da ladder após
        ladder_apos = list(PosicaoLadder.objects.all().order_by('posicao').values_list('jogador', 'posicao'))
        
        # Tamanho da ladder deve ser o mesmo
        self.assertEqual(len(ladder_antes), len(ladder_apos))
        
        # 7 primeiras posições devem ter mudado
        self.assertIn((self.jogador_pos_7.id, 1), ladder_apos)
        self.assertIn((self.jogador_pos_1.id, 2), ladder_apos)
        self.assertIn((self.jogador_pos_2.id, 3), ladder_apos)
        self.assertIn((self.jogador_pos_3.id, 4), ladder_apos)
        self.assertIn((self.jogador_pos_4.id, 5), ladder_apos)
        self.assertIn((self.jogador_pos_5.id, 6), ladder_apos)
        self.assertIn((self.jogador_pos_6.id, 7), ladder_apos)
        
        # Outras permanecem
        for situacao_antes, situacao_apos in zip(ladder_antes[7:], ladder_apos[7:]):
            self.assertEqual(situacao_antes, situacao_apos)
    
    def test_alterar_ladder_historico_vitoria_coringa(self):
        """Testa alterar ladder histórico por um registro de vitória de desafio coringa"""
        # Pegar situação da ladder antes
        ladder_antes = list(HistoricoLadder.objects.filter(ano=self.ano, mes=self.mes).order_by('posicao').values_list('jogador', 'posicao'))
        
        # Jogador 6 ganhou de jogador 2
        alterar_ladder(self.registro_ladder_historico_coringa)
        
        # Pegar situação da ladder após
        ladder_apos = list(HistoricoLadder.objects.filter(ano=self.ano, mes=self.mes).order_by('posicao').values_list('jogador', 'posicao'))
        
        # Tamanho da ladder deve ser o mesmo
        self.assertEqual(len(ladder_antes), len(ladder_apos))
        
        # Posição 1 não mudou
        self.assertIn((self.jogador_pos_1.id, 1), ladder_apos)
        
        # Posições do 2 ao 6 devem ter mudado
        self.assertIn((self.jogador_pos_6.id, 2), ladder_apos)
        self.assertIn((self.jogador_pos_2.id, 3), ladder_apos)
        self.assertIn((self.jogador_pos_3.id, 4), ladder_apos)
        self.assertIn((self.jogador_pos_4.id, 5), ladder_apos)
        self.assertIn((self.jogador_pos_5.id, 6), ladder_apos)
        
        # Outras permanecem
        for situacao_antes, situacao_apos in zip(ladder_antes[6:], ladder_apos[6:]):
            self.assertEqual(situacao_antes, situacao_apos)
    
    def test_alterar_ladder_vitoria_novo_entrante(self):
        """Testa alterar ladder por vitória de novo entrante, deve entrar na posição do desafiado"""
        # Pegar situação da ladder antes
        ladder_antes = list(PosicaoLadder.objects.all().order_by('posicao').values_list('jogador', 'posicao'))
        
        # Novo jogador ganhou de jogador 10
        alterar_ladder(self.registro_ladder_novo_entrante_vitoria)
        
        # Pegar situação da ladder após
        ladder_apos = list(PosicaoLadder.objects.all().order_by('posicao').values_list('jogador', 'posicao'))
        
        # Tamanho da ladder deve aumentar 1 posição
        self.assertEqual(len(ladder_antes) + 1, len(ladder_apos))
        
        # Posições do 1 ao 9 permanecem
        for situacao_antes, situacao_apos in zip(ladder_antes[:9], ladder_apos[:9]):
            self.assertEqual(situacao_antes, situacao_apos)
            
        # Novo entrante deve estar na 10
        self.assertIn((self.new.id, 10), ladder_apos)
        self.assertIn((self.jogador_pos_10.id, 11), ladder_apos)
        
    def test_alterar_ladder_derrota_novo_entrante(self):
        """Testa alterar ladder por derrota de novo entrante, deve entrar em último"""
        # Pegar situação da ladder antes
        ladder_antes = list(PosicaoLadder.objects.all().order_by('posicao').values_list('jogador', 'posicao'))
        
        # Novo jogador ganhou de jogador 10
        alterar_ladder(self.registro_ladder_novo_entrante_derrota)
        
        # Pegar situação da ladder após
        ladder_apos = list(PosicaoLadder.objects.all().order_by('posicao').values_list('jogador', 'posicao'))
        
        # Tamanho da ladder deve aumentar 1 posição
        self.assertEqual(len(ladder_antes) + 1, len(ladder_apos))
        
        # Posições do 1 ao 10 permanecem
        for situacao_antes, situacao_apos in zip(ladder_antes[:10], ladder_apos[:10]):
            self.assertEqual(situacao_antes, situacao_apos)
            
        # Novo entrante deve estar na 11
        self.assertIn((self.new.id, 11), ladder_apos)

class RecalcularLadderTestCase(TestCase):
    """Testes para a função de recalcular ladder"""
    @classmethod
    def setUpTestData(cls):
        super(RecalcularLadderTestCase, cls).setUpTestData()
        
        criar_jogadores_teste()
        
        # Pegar objetos de jogador de acordo com sua posição
        cls.jogador_pos_1 = Jogador.objects.get(nick='teets')
        cls.jogador_pos_2 = Jogador.objects.get(nick='saraiva')
        cls.jogador_pos_3 = Jogador.objects.get(nick='sena')
        cls.jogador_pos_4 = Jogador.objects.get(nick='mad')
        cls.jogador_pos_5 = Jogador.objects.get(nick='blöwer')
        cls.jogador_pos_6 = Jogador.objects.get(nick='frodo')
        cls.jogador_pos_7 = Jogador.objects.get(nick='dan')
        cls.jogador_pos_10 = Jogador.objects.get(nick='tiovsky')
        
        # Jogadores para validar alterações no ranking
        cls.jogadores = [cls.jogador_pos_1, cls.jogador_pos_2,
                         cls.jogador_pos_3, cls.jogador_pos_4,
                         cls.jogador_pos_5, cls.jogador_pos_6,
                         cls.jogador_pos_7]
        
        # Criar ladder inicial
        criar_ladder_inicial_teste()
        
        # Criar ladder atual
        criar_ladder_teste()
        
        # Preparar mês anterior para histórico
        horario_atual = timezone.now()
        cls.ano = horario_atual.date().year
        cls.mes = horario_atual.date().month - 1
        if cls.mes == 0:
            cls.mes = 12
            cls.ano -= 1
        
        criar_ladder_historico_teste(cls.ano, cls.mes)
        
        # Criar novo entrante
        cls.new = criar_jogador_teste('new')
        
        horario_historico = horario_atual.replace(month=cls.mes, year=cls.ano)
        
        cls.registro_ladder = criar_registro_ladder_simples_teste(cls.jogador_pos_3, cls.jogador_pos_1, 3, 1, 
                                                                          horario_atual.replace(hour=5), False, cls.jogador_pos_1)
        cls.registro_ladder_derrota = criar_registro_ladder_simples_teste(cls.jogador_pos_7, cls.jogador_pos_6, 0, 3, 
                                                                          horario_atual.replace(hour=6), False, cls.jogador_pos_1)
        cls.registro_ladder_historico = criar_registro_ladder_simples_teste(cls.jogador_pos_3, cls.jogador_pos_2, 3, 1, 
                                                                          horario_historico.replace(hour=5), True, cls.jogador_pos_1)
        cls.registro_ladder_historico_derrota = criar_registro_ladder_simples_teste(cls.jogador_pos_6, cls.jogador_pos_5, 0, 3, 
                                                                          horario_historico.replace(hour=6), True, cls.jogador_pos_1)
        
        # Desafios coringa
        cls.registro_ladder_coringa = criar_registro_ladder_simples_teste(cls.jogador_pos_7, cls.jogador_pos_1, 3, 1, 
                                                                          horario_atual.replace(hour=7), False, cls.jogador_pos_1)
        cls.registro_ladder_historico_coringa = criar_registro_ladder_simples_teste(cls.jogador_pos_6, cls.jogador_pos_3, 3, 1, 
                                                                          horario_historico.replace(hour=7), True, cls.jogador_pos_1)
        
        # Desafios de novo entrante
        cls.registro_ladder_novo_entrante_vitoria = criar_registro_ladder_simples_teste(cls.new, cls.jogador_pos_10, 3, 1, 
                                                                          horario_atual.replace(day=15, hour=8), False, cls.jogador_pos_1)
        cls.registro_ladder_novo_entrante_derrota = criar_registro_ladder_simples_teste(cls.new, cls.jogador_pos_10, 0, 3, 
                                                                          horario_atual.replace(day=5, hour=9), False, cls.jogador_pos_1)
        
        
    def test_erro_recalcular_ladder_apenas_mes(self):
        """Testa erro por chamar função sem especificar ano"""
        with self.assertRaisesMessage(ValueError, 'Informe um ano'):
            recalcular_ladder(self.mes)
        
    def test_erro_recalcular_ladder_apenas_ano(self):
        """Testa erro por chamar função sem especificar mês"""
        with self.assertRaisesMessage(ValueError, 'Informe um mês'):
            recalcular_ladder(ano=self.ano)
        
        
    def test_recalcular_ladder_atual_com_historico(self):
        """Testa recalcular posições de ladder atual partindo de histórico anterior"""
        # Validar registros
        # Jogador 3 ganhou de 1
        validar_registro_ladder_teste(self.registro_ladder, self.jogador_pos_1)
        # Novo entrante ganhou de 10
        validar_registro_ladder_teste(self.registro_ladder_novo_entrante_vitoria, self.jogador_pos_1)
        # Jogador 7 ganhou de 1 com coringa, mas teve registro de ladder cancelado
        validar_registro_ladder_teste(self.registro_ladder_coringa, self.jogador_pos_1)
        CancelamentoRegistroLadder.objects.create(registro_ladder=self.registro_ladder_coringa, jogador=self.jogador_pos_1)
        
        # Simular sumiço de ladder atual
        PosicaoLadder.objects.all().delete()
        
        # Recalcula ladder atual
        recalcular_ladder()
        
        # Buscar ladder atual
        ladder = list(PosicaoLadder.objects.all().order_by('posicao').values_list('jogador', 'posicao'))
        
        # Ladder deve ter 11 posições
        self.assertEqual(len(ladder), 11)
        
        # Jogador 3 deve estar na posição 1
        self.assertIn((self.jogador_pos_3.id, 1), ladder)
        
        # Jogador 1 deve estar na posição 2
        self.assertIn((self.jogador_pos_1.id, 2), ladder)
        
        # Jogador 2 deve estar na posição 3
        self.assertIn((self.jogador_pos_2.id, 3), ladder)
        
        # Novo entrante deve estar na posição 10
        self.assertIn((self.new.id, 10), ladder)
        
        # Jogador 10 deve estar em 11
        self.assertIn((self.jogador_pos_10.id, 11), ladder)
        
    def test_recalcular_ladder_atual_sem_historico(self):
        """Testa recalcular posições de ladder atual partindo da posição inicial"""
        # Validar registros
        # Jogador 7 ganhou de 1
        validar_registro_ladder_teste(self.registro_ladder_coringa, self.jogador_pos_1)
        # Novo entrante perdeu de 10
        validar_registro_ladder_teste(self.registro_ladder_novo_entrante_derrota, self.jogador_pos_1)
        
        # Apagar ladder histórico
        HistoricoLadder.objects.all().delete()
        
        # Simular sumiço de ladder atual
        PosicaoLadder.objects.all().delete()
        
        # Recalcula ladder atual
        recalcular_ladder()
        
        # Buscar ladder atual
        ladder = list(PosicaoLadder.objects.all().order_by('posicao').values_list('jogador', 'posicao'))
        
        # Ladder deve ter 11 posições
        self.assertEqual(len(ladder), 11)
        
        # Jogador 7 deve estar na posição 1
        self.assertIn((self.jogador_pos_7.id, 1), ladder)
        
        # Jogador 1 deve estar na posição 2
        self.assertIn((self.jogador_pos_1.id, 2), ladder)
        
        # Jogador 2 deve estar na posição 3
        self.assertIn((self.jogador_pos_2.id, 3), ladder)
        
        # Novo entrante deve estar na posição 11
        self.assertIn((self.new.id, 11), ladder)
        
        # Jogador 10 deve estar em 10
        self.assertIn((self.jogador_pos_10.id, 10), ladder)
        
    def test_recalcular_ladder_historico_com_historico(self):
        """Testa recalcular posições de ladder histórica partindo de histórico anterior"""
        # Validar registros
        # Jogador 3 ganhou de 2
        validar_registro_ladder_teste(self.registro_ladder_historico, self.jogador_pos_1)
        # Jogador 6 ganhou de 3
        validar_registro_ladder_teste(self.registro_ladder_historico_coringa, self.jogador_pos_1)
        
        # Simular sumiço de ladder histórico
        HistoricoLadder.objects.all().delete()
        
        # Criar ladder histórico de mês anterior a ladder histórico
        ano_hist_anterior = self.ano
        mes_hist_anterior = self.mes - 1 
        if mes_hist_anterior == 0:
            mes_hist_anterior = 12
            ano_hist_anterior -= 1
        criar_ladder_historico_teste(ano_hist_anterior, mes_hist_anterior)
        
        # Recalcula ladder histórico
        recalcular_ladder(self.mes, self.ano)
        
        # Buscar ladder atual
        ladder = list(HistoricoLadder.objects.filter(mes=self.mes, ano=self.ano).order_by('posicao').values_list('jogador', 'posicao'))
        
        # Jogador 3 deve estar na posição 3
        self.assertIn((self.jogador_pos_3.id, 3), ladder)
        
        # Jogador 2 deve estar na posição 4
        self.assertIn((self.jogador_pos_2.id, 4), ladder)
        
        # Jogador 6 deve estar na posição 2
        self.assertIn((self.jogador_pos_6.id, 2), ladder)
        
        # Jogador 4 deve estar em 5
        self.assertIn((self.jogador_pos_4.id, 5), ladder)
        
        # Jogador 5 deve estar em 6
        self.assertIn((self.jogador_pos_5.id, 6), ladder)
        
    def test_recalcular_ladder_historico_sem_historico(self):
        """Testa recalcular posições de ladder histórica partindo da posição inicial"""
        # Validar registros
        # Jogador 3 ganhou de 2
        validar_registro_ladder_teste(self.registro_ladder_historico, self.jogador_pos_1)
        # Jogador 6 ganhou de 3
        validar_registro_ladder_teste(self.registro_ladder_historico_coringa, self.jogador_pos_1)
        
        # Simular sumiço de ladder histórico
        HistoricoLadder.objects.all().delete()
        
        # Recalcula ladder atual
        recalcular_ladder(self.mes, self.ano)
        
        # Buscar ladder atual
        ladder = list(HistoricoLadder.objects.filter(mes=self.mes, ano=self.ano).order_by('posicao').values_list('jogador', 'posicao'))
        
        # Jogador 3 deve estar na posição 3
        self.assertIn((self.jogador_pos_3.id, 3), ladder)
        
        # Jogador 2 deve estar na posição 4
        self.assertIn((self.jogador_pos_2.id, 4), ladder)
        
        # Jogador 6 deve estar na posição 2
        self.assertIn((self.jogador_pos_6.id, 2), ladder)
        
        # Jogador 4 deve estar em 5
        self.assertIn((self.jogador_pos_4.id, 5), ladder)
        
        # Jogador 5 deve estar em 6
        self.assertIn((self.jogador_pos_5.id, 6), ladder)
        
    def test_erro_recalcular_atual_com_alteracao_historico_impossivel(self):
        """Testar recálculo de posição atual com alteração no histórico que impossibilita posições"""
        # Validar registros
        # Jogador 3 derrotou o 1 esse mês
        validar_registro_ladder_teste(self.registro_ladder, self.jogador_pos_1)
        # Jogador 6 derrotou o 3 mês passado
        validar_registro_ladder_teste(self.registro_ladder_historico_coringa, self.jogador_pos_1)
        
        # Simular sumiço de ladder atual
        PosicaoLadder.objects.all().delete()
        
        # Recalcula ladder atual, deve dar erro na validação de registro para jogador 3 derrotando jogador 1
        regex = re.escape(f'Registro Ladder {self.registro_ladder.id}: ') + r'.+'
        with self.assertRaisesRegex(ValueError, regex):
            recalcular_ladder()

class VerificarSeDesafiantePodeDesafiarTestCase(TestCase):
    """Testes para a função que verifica se desafiante está abaixo do desafiado na ladder"""
    @classmethod
    def setUpTestData(cls):
        super(VerificarSeDesafiantePodeDesafiarTestCase, cls).setUpTestData()
        
        criar_jogadores_teste()
        
        # Pegar objetos de jogador de acordo com sua posição
        cls.jogador_pos_1 = Jogador.objects.get(nick='teets')
        cls.jogador_pos_2 = Jogador.objects.get(nick='saraiva')
        cls.jogador_pos_3 = Jogador.objects.get(nick='sena')
        cls.jogador_pos_4 = Jogador.objects.get(nick='mad')
        cls.jogador_pos_5 = Jogador.objects.get(nick='blöwer')
        cls.jogador_pos_6 = Jogador.objects.get(nick='frodo')
        cls.jogador_pos_7 = Jogador.objects.get(nick='dan')
        
        cls.jogadores = [cls.jogador_pos_1, cls.jogador_pos_2,
                         cls.jogador_pos_3, cls.jogador_pos_4,
                         cls.jogador_pos_5, cls.jogador_pos_6,
                         cls.jogador_pos_7]
        
        # Criar ladders para verificar que adicionar registro não as afeta
        criar_ladder_teste()
        
        # Preparar mês anterior para histórico
        data_atual = timezone.now().date()
        cls.ano = data_atual.year
        cls.mes = data_atual.month - 1
        if cls.mes == 0:
            cls.mes = 12
            cls.ano -= 1
        
        criar_ladder_historico_teste(cls.ano, cls.mes)
        
    def test_desafiante_desafiado_mesmo_jogador(self):
        """Desafiante e desafiado são o mesmo jogador"""
        with self.assertRaisesMessage(ValueError, RegistroLadder.MENSAGEM_ERRO_MESMO_JOGADOR):
            verificar_posicoes_desafiante_desafiado(PosicaoLadder.objects, self.jogador_pos_3, self.jogador_pos_3, timezone.now(), False)
        
    def test_desafiante_abaixo_1_posicao_desafiado_ladder_atual(self):
        """Desafiante está abaixo 1 posição portanto pode desafiar, ladder atual"""
        verificar_posicoes_desafiante_desafiado(PosicaoLadder.objects, self.jogador_pos_4, self.jogador_pos_3, timezone.now(), False)
        
    def test_desafiante_abaixo_2_posicao_desafiado_ladder_atual(self):
        """Desafiante está abaixo 2 posições portanto pode desafiar, ladder atual"""
        verificar_posicoes_desafiante_desafiado(PosicaoLadder.objects, self.jogador_pos_5, self.jogador_pos_3, timezone.now(), False)
        
    def test_desafiante_abaixo_3_posicao_desafiado_ladder_atual(self):
        """Desafiante está abaixo 3 posições portanto não pode desafiar, ladder atual"""
        with self.assertRaisesMessage(ValueError, RegistroLadder.MENSAGEM_ERRO_DESAFIANTE_MUITO_ABAIXO_DESAFIADO):
            verificar_posicoes_desafiante_desafiado(PosicaoLadder.objects, self.jogador_pos_6, self.jogador_pos_3, timezone.now(), False)
    
    def test_desafiante_abaixo_1_posicao_desafiado_ladder_historico(self):
        """Desafiante está abaixo 1 posição portanto pode desafiar, ladder histórico"""
        verificar_posicoes_desafiante_desafiado(HistoricoLadder.objects.filter(ano=self.ano, mes=self.mes), 
                                                              self.jogador_pos_4, self.jogador_pos_3, timezone.now(), False)
        
    def test_desafiante_abaixo_2_posicao_desafiado_ladder_historico(self):
        """Desafiante está abaixo 2 posições portanto pode desafiar, ladder histórico"""
        verificar_posicoes_desafiante_desafiado(HistoricoLadder.objects.filter(ano=self.ano, mes=self.mes), 
                                                              self.jogador_pos_5, self.jogador_pos_3, timezone.now(), False)
        
    def test_desafiante_abaixo_3_posicao_desafiado_ladder_historico(self):
        """Desafiante está abaixo 3 posições portanto não pode desafiar, ladder histórico"""
        with self.assertRaisesMessage(ValueError, RegistroLadder.MENSAGEM_ERRO_DESAFIANTE_MUITO_ABAIXO_DESAFIADO):
            verificar_posicoes_desafiante_desafiado(HistoricoLadder.objects.filter(ano=self.ano, mes=self.mes), 
                                                                  self.jogador_pos_6, self.jogador_pos_3, timezone.now(), False)
    
    def test_desafiante_acima_desafiado_ladder_atual(self):
        """Desafiante está acima de desafiado no ranking portanto não pode desafiar, ladder atual"""
        with self.assertRaisesMessage(ValueError, RegistroLadder.MENSAGEM_ERRO_DESAFIANTE_ACIMA_DESAFIADO):
            verificar_posicoes_desafiante_desafiado(PosicaoLadder.objects, self.jogador_pos_5, self.jogador_pos_6, timezone.now(), False)
    
    def test_desafiante_acima_desafiado_ladder_historico(self):
        """Desafiante está acima de desafiado no ranking portanto não pode desafiar, ladder histórico"""
        with self.assertRaisesMessage(ValueError, RegistroLadder.MENSAGEM_ERRO_DESAFIANTE_ACIMA_DESAFIADO):
            verificar_posicoes_desafiante_desafiado(HistoricoLadder.objects.filter(ano=self.ano, mes=self.mes), 
                                                              self.jogador_pos_5, self.jogador_pos_6, timezone.now(), False)
    
    def test_desafiante_ferias(self):
        """Desafiante está de férias portanto não pode desafiar ninguém"""
        # Criar registro férias
        RegistroFerias.objects.create(jogador=self.jogador_pos_6, data_inicio=(timezone.now() - datetime.timedelta(days=10)),
                                      data_fim=(timezone.now() + datetime.timedelta(days=10)))
        
        with self.assertRaisesMessage(ValueError, RegistroLadder.MENSAGEM_ERRO_DESAFIANTE_FERIAS):
            verificar_posicoes_desafiante_desafiado(PosicaoLadder.objects, self.jogador_pos_6, self.jogador_pos_5, timezone.now(), False)
    
    def test_desafiado_ferias(self):
        """Jogador desafiado está de férias portanto não pode ser desafiado"""
        # Criar registro férias
        RegistroFerias.objects.create(jogador=self.jogador_pos_5, data_inicio=(timezone.now() - datetime.timedelta(days=10)),
                                      data_fim=(timezone.now() + datetime.timedelta(days=10)))
        
        with self.assertRaisesMessage(ValueError, RegistroLadder.MENSAGEM_ERRO_DESAFIADO_FERIAS):
            verificar_posicoes_desafiante_desafiado(PosicaoLadder.objects, self.jogador_pos_6, self.jogador_pos_5, timezone.now(), False)
    
    def test_desafiante_3_posicoes_abaixo_proximo_com_ferias(self):
        """Desafiante está 3 posições abaixo, mas o jogador logo acima está de férias, pode desafiar"""
        # Criar registro férias
        RegistroFerias.objects.create(jogador=self.jogador_pos_5, data_inicio=(timezone.now() - datetime.timedelta(days=10)),
                                      data_fim=(timezone.now() + datetime.timedelta(days=10)))
        
        verificar_posicoes_desafiante_desafiado(PosicaoLadder.objects, self.jogador_pos_6, self.jogador_pos_3, timezone.now(), False)
    
    def test_desafiante_4_posicoes_abaixo_proximo_com_ferias(self):
        """Desafiante está 4 abaixo e o próximo acima está de férias, portanto não pode desafiar"""
        # Criar registro férias
        RegistroFerias.objects.create(jogador=self.jogador_pos_5, data_inicio=(timezone.now() - datetime.timedelta(days=10)),
                                      data_fim=(timezone.now() + datetime.timedelta(days=10)))
        
        with self.assertRaisesMessage(ValueError, RegistroLadder.MENSAGEM_ERRO_DESAFIANTE_MUITO_ABAIXO_DESAFIADO):
            verificar_posicoes_desafiante_desafiado(PosicaoLadder.objects, self.jogador_pos_6, self.jogador_pos_2, timezone.now(), False)
    
    def test_desafiante_4_posicoes_abaixo_2_proximos_com_ferias(self):
        """Desafiante está 4 abaixo mas os 2 próximos jogadores estão de férias, portanto pode desafiar"""
        # Criar registros férias
        RegistroFerias.objects.create(jogador=self.jogador_pos_5, data_inicio=(timezone.now() - datetime.timedelta(days=10)),
                                      data_fim=(timezone.now() + datetime.timedelta(days=10)))
        RegistroFerias.objects.create(jogador=self.jogador_pos_4, data_inicio=(timezone.now() - datetime.timedelta(days=10)),
                                      data_fim=(timezone.now() + datetime.timedelta(days=10)))
        
        verificar_posicoes_desafiante_desafiado(PosicaoLadder.objects, self.jogador_pos_6, self.jogador_pos_2, timezone.now(), False)
        
    def test_desafio_coringa_ladder_atual(self):
        """Desafiante usa desafio coringa na ladder atual, basta desafiado não estar de férias"""
        # Criar registro férias
        RegistroFerias.objects.create(jogador=self.jogador_pos_3, data_inicio=(timezone.now() - datetime.timedelta(days=10)),
                                      data_fim=(timezone.now() + datetime.timedelta(days=10)))
        
        for jogador in self.jogadores:
            # Desafiante não pode desafiar a si mesmo
            if jogador == self.jogador_pos_7:
                pass
            elif jogador == self.jogador_pos_3:
                with self.assertRaisesMessage(ValueError, RegistroLadder.MENSAGEM_ERRO_DESAFIADO_FERIAS):
                    verificar_posicoes_desafiante_desafiado(PosicaoLadder.objects, self.jogador_pos_7, jogador, timezone.now(), True)
            else:
                verificar_posicoes_desafiante_desafiado(PosicaoLadder.objects, self.jogador_pos_7, jogador, timezone.now(), True)
