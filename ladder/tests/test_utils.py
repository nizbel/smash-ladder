# -*- coding: utf-8 -*-
import datetime

from django.test.testcases import TestCase
from django.utils import timezone

from jogadores.models import Jogador, RegistroFerias
from jogadores.tests.utils_teste import criar_jogadores_teste, \
    criar_jogador_teste
from ladder.models import PosicaoLadder, HistoricoLadder, DesafioLadder, \
    CancelamentoDesafioLadder, RemocaoJogador, DecaimentoJogador
from ladder.tests.utils_teste import criar_ladder_teste, \
    criar_ladder_historico_teste, criar_desafio_ladder_simples_teste, \
    validar_desafio_ladder_teste, criar_ladder_inicial_teste
from ladder.utils import verificar_posicoes_desafiante_desafiado, alterar_ladder, \
    recalcular_ladder, copiar_ladder, remover_jogador, decair_jogador, \
    avaliar_decaimento, buscar_desafiaveis
from smashLadder.utils import mes_ano_ant


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
        cls.jogador_pos_8 = Jogador.objects.get(nick='phils')
        cls.jogador_pos_9 = Jogador.objects.get(nick='rata')
        cls.jogador_pos_10 = Jogador.objects.get(nick='tiovsky')
        
        # Jogadores para validar alterações no ranking
        cls.jogadores = [cls.jogador_pos_1, cls.jogador_pos_2,
                         cls.jogador_pos_3, cls.jogador_pos_4,
                         cls.jogador_pos_5, cls.jogador_pos_6,
                         cls.jogador_pos_7]
        
        # Criar ladders para verificar que adicionar desafio não as afeta
        criar_ladder_teste()
        
        # Preparar mês anterior para histórico
        data_atual = timezone.now().date()
        cls.mes, cls.ano = mes_ano_ant(data_atual.month, data_atual.year)
        
        criar_ladder_historico_teste(cls.ano, cls.mes)
        
        # Criar novo entrante
        cls.new = criar_jogador_teste('new')
        
        # Criar outro novo entrante
        cls.new_2 = criar_jogador_teste('new_2')
        
        horario_atual = timezone.localtime()
        horario_historico = horario_atual.replace(month=cls.mes, year=cls.ano)
        
        cls.desafio_ladder = criar_desafio_ladder_simples_teste(cls.jogador_pos_3, cls.jogador_pos_1, 3, 1, 
                                                                          horario_atual, False, cls.jogador_pos_1)
        cls.desafio_ladder_derrota = criar_desafio_ladder_simples_teste(cls.jogador_pos_7, cls.jogador_pos_6, 0, 3, 
                                                                          horario_atual + datetime.timedelta(minutes=1), False, cls.jogador_pos_1)
        cls.desafio_ladder_historico = criar_desafio_ladder_simples_teste(cls.jogador_pos_3, cls.jogador_pos_2, 3, 1, 
                                                                          horario_historico, True, cls.jogador_pos_1)
        cls.desafio_ladder_historico_derrota = criar_desafio_ladder_simples_teste(cls.jogador_pos_6, cls.jogador_pos_5, 0, 3, 
                                                                          horario_historico + datetime.timedelta(minutes=1), True, cls.jogador_pos_1)
        
        # Desafios coringa
        cls.desafio_ladder_coringa = criar_desafio_ladder_simples_teste(cls.jogador_pos_7, cls.jogador_pos_1, 3, 1, 
                                                                          horario_atual + datetime.timedelta(minutes=2), False, cls.jogador_pos_1)
        cls.desafio_ladder_historico_coringa = criar_desafio_ladder_simples_teste(cls.jogador_pos_6, cls.jogador_pos_2, 3, 1, 
                                                                          horario_historico + datetime.timedelta(minutes=2), True, cls.jogador_pos_1)
        
        # Desafios de novo entrante
        cls.desafio_ladder_novo_entrante_vitoria = criar_desafio_ladder_simples_teste(cls.new, cls.jogador_pos_10, 3, 1, 
                                                                          horario_atual.replace(day=15), False, cls.jogador_pos_1)
        cls.desafio_ladder_novo_entrante_derrota = criar_desafio_ladder_simples_teste(cls.new, cls.jogador_pos_10, 0, 3, 
                                                                          horario_atual.replace(day=5), False, cls.jogador_pos_1)
        cls.desafio_ladder_novos_entrantes_derrota = criar_desafio_ladder_simples_teste(cls.new, cls.new_2, 0, 3, 
                                                                          horario_atual.replace(day=3), False, cls.jogador_pos_1)
                                                                          
    def test_alterar_ladder_atual_vitoria(self):
        """Testa alterar ladder atual por um desafio de vitória"""
        # Pegar situação da ladder antes
        ladder_antes = list(PosicaoLadder.objects.all().order_by('posicao').values_list('jogador', 'posicao'))
        
        # Jogador 3 ganhou de jogador 1
        alterar_ladder(self.desafio_ladder)
        
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
        """Testa alterar ladder histórico por um desafio de vitória"""
        # Pegar situação da ladder antes
        ladder_antes = list(HistoricoLadder.objects.filter(ano=self.ano, mes=self.mes).order_by('posicao').values_list('jogador', 'posicao'))
        
        # Jogador 3 ganhou de jogador 2
        alterar_ladder(self.desafio_ladder_historico)
        
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
        """Testa não alterar ladder atual por um desafio de derrota"""
        # Pegar situação da ladder antes
        ladder_antes = list(PosicaoLadder.objects.all().order_by('posicao').values_list('jogador', 'posicao'))
        
        alterar_ladder(self.desafio_ladder_derrota)
        
        # Pegar situação da ladder após
        ladder_apos = list(PosicaoLadder.objects.all().order_by('posicao').values_list('jogador', 'posicao'))
        
        for situacao_antes, situacao_apos in zip(ladder_antes, ladder_apos):
            self.assertEqual(situacao_antes, situacao_apos)
    
    def test_nao_alterar_ladder_historico_derrota(self):
        """Testa não alterar ladder histórico por um desafio de derrota"""
        # Pegar situação da ladder antes
        ladder_antes = list(HistoricoLadder.objects.filter(ano=self.ano, mes=self.mes).order_by('posicao').values_list('jogador', 'posicao'))
        
        alterar_ladder(self.desafio_ladder_historico_derrota)
        
        # Pegar situação da ladder após
        ladder_apos = list(HistoricoLadder.objects.filter(ano=self.ano, mes=self.mes).order_by('posicao').values_list('jogador', 'posicao'))
        
        for situacao_antes, situacao_apos in zip(ladder_antes, ladder_apos):
            self.assertEqual(situacao_antes, situacao_apos)
    
    def test_alterar_ladder_atual_vitoria_coringa(self):
        """Testa alterar ladder atual por um desafio de vitória de desafio coringa"""
        # Pegar situação da ladder antes
        ladder_antes = list(PosicaoLadder.objects.all().order_by('posicao').values_list('jogador', 'posicao'))
        
        # Jogador 7 ganhou de jogador 1
        alterar_ladder(self.desafio_ladder_coringa)
        
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
        """Testa alterar ladder histórico por um desafio de vitória de desafio coringa"""
        # Pegar situação da ladder antes
        ladder_antes = list(HistoricoLadder.objects.filter(ano=self.ano, mes=self.mes).order_by('posicao').values_list('jogador', 'posicao'))
        
        # Jogador 6 ganhou de jogador 2
        alterar_ladder(self.desafio_ladder_historico_coringa)
        
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
        alterar_ladder(self.desafio_ladder_novo_entrante_vitoria)
        
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
        alterar_ladder(self.desafio_ladder_novo_entrante_derrota)
        
        # Pegar situação da ladder após
        ladder_apos = list(PosicaoLadder.objects.all().order_by('posicao').values_list('jogador', 'posicao'))
        
        # Tamanho da ladder deve aumentar 1 posição
        self.assertEqual(len(ladder_antes) + 1, len(ladder_apos))
        
        # Posições do 1 ao 10 permanecem
        for situacao_antes, situacao_apos in zip(ladder_antes[:10], ladder_apos[:10]):
            self.assertEqual(situacao_antes, situacao_apos)
            
        # Novo entrante deve estar na 11
        self.assertIn((self.new.id, 11), ladder_apos)
        
    def test_alterar_ladder_desafio_anterior(self):
        """Testa alteração de ladder com desafio anterior a último validado"""
        # Preparar desafios
        # Jogador posição 3 ganhou de jogador posição 2
        desafio_anterior = self.desafio_ladder_historico
        # Jogador posição 3 ganhou de jogador posição 1
        desafio_posterior = self.desafio_ladder
        
        # Alterar ladder com desafio posterior
        desafio_posterior.admin_validador = self.jogador_pos_1
        desafio_posterior.save()
        alterar_ladder(desafio_posterior)
        
        # Verificar que resultados indicam queda de jogadores 2 e 1
        resultados = desafio_posterior.resultadodesafioladder_set.all().values('jogador', 'alteracao_posicao')
        self.assertEqual(len(resultados), 3)
        self.assertIn({'jogador': self.jogador_pos_1.id, 'alteracao_posicao': 1}, resultados)
        self.assertIn({'jogador': self.jogador_pos_2.id, 'alteracao_posicao': 1}, resultados)
        self.assertIn({'jogador': self.jogador_pos_3.id, 'alteracao_posicao': -2}, resultados)
        
        self.assertEqual(desafio_posterior.posicao_desafiante, 3)
        self.assertEqual(desafio_posterior.posicao_desafiado, 1)
        
        # Pegar situação da ladder antes
        ladder_antes = list(PosicaoLadder.objects.all().order_by('posicao').values_list('jogador', 'posicao'))
        
        # Validar e alterar
        desafio_anterior.admin_validador = self.jogador_pos_1
        desafio_anterior.save()
        alterar_ladder(desafio_anterior)
        
        # Atualizar desafios
        desafio_anterior.refresh_from_db()
        desafio_posterior.refresh_from_db()
        
        # Pegar situação da ladder após
        ladder_apos = list(PosicaoLadder.objects.all().order_by('posicao').values_list('jogador', 'posicao'))
        
        # Posições permanecem
        for situacao_antes, situacao_apos in zip(ladder_antes, ladder_apos):
            self.assertEqual(situacao_antes, situacao_apos)
            
        # Resultados de desafio posterior devem ser alterados
        resultados = desafio_posterior.resultadodesafioladder_set.all().values('jogador', 'alteracao_posicao')
        self.assertEqual(len(resultados), 2)
        self.assertIn({'jogador': self.jogador_pos_1.id, 'alteracao_posicao': 1}, resultados)
        self.assertIn({'jogador': self.jogador_pos_3.id, 'alteracao_posicao': -1}, resultados)
        
        # Verificar posições para desafios
        self.assertEqual(desafio_anterior.posicao_desafiante, 3)
        self.assertEqual(desafio_anterior.posicao_desafiado, 2)
        self.assertEqual(desafio_posterior.posicao_desafiante, 2)
        self.assertEqual(desafio_posterior.posicao_desafiado, 1)
        
    def test_alterar_ladder_desafio_anterior_novo_entrante(self):
        """Testa alteração de ladder com desafio anterior a último validado com novo entrante"""
        # Preparar desafios
        # Garantir que novo entrante desafie antes
        desafio_anterior = DesafioLadder(data_hora=self.desafio_ladder.data_hora - datetime.timedelta(days=5), 
                                          desafiante=self.desafio_ladder_novo_entrante_vitoria.desafiante,
                                          desafiado=self.desafio_ladder_novo_entrante_vitoria.desafiado,
                                          adicionado_por=self.desafio_ladder_novo_entrante_vitoria.adicionado_por,
                                          score_desafiante=3, score_desafiado=1, desafio_coringa=False)
        desafio_anterior.save()
        
        desafio_posterior = DesafioLadder(data_hora=self.desafio_ladder.data_hora, score_desafiante=3, score_desafiado=1,
                                          desafio_coringa=False)
        desafio_posterior.desafiante = self.jogador_pos_10
        desafio_posterior.desafiado = self.jogador_pos_9
        desafio_posterior.adicionado_por = self.jogador_pos_10
        desafio_posterior.admin_validador = self.jogador_pos_1
        desafio_posterior.save()
        
        alterar_ladder(desafio_posterior)
        
        # Verificar resultados
        resultados = desafio_posterior.resultadodesafioladder_set.all().values('jogador', 'alteracao_posicao')
        self.assertEqual(len(resultados), 2)
        self.assertIn({'jogador': self.jogador_pos_10.id, 'alteracao_posicao': -1}, resultados)
        self.assertIn({'jogador': self.jogador_pos_9.id, 'alteracao_posicao': 1}, resultados)
        
        # Verificar posições no desafio
        self.assertEqual(desafio_posterior.posicao_desafiante, 10)
        self.assertEqual(desafio_posterior.posicao_desafiado, 9)
        
        # Pegar situação da ladder antes
        ladder_antes = list(PosicaoLadder.objects.all().order_by('posicao').values_list('jogador', 'posicao'))
        
        # Validar e alterar
        desafio_anterior.admin_validador = self.jogador_pos_1
        desafio_anterior.save()
        alterar_ladder(desafio_anterior)
        
        # Atualizar
        desafio_anterior.refresh_from_db()
        desafio_posterior.refresh_from_db()
        
        # Pegar situação da ladder após
        ladder_apos = list(PosicaoLadder.objects.all().order_by('posicao').values_list('jogador', 'posicao'))
        
        # Tamanho da ladder deve aumentar 1 posição
        self.assertEqual(len(ladder_antes) + 1, len(ladder_apos))
        
        # Novo entrante está em décimo primeiro
        # Outras posições permanecem
        for situacao_antes, situacao_apos in zip(ladder_antes[:10], ladder_apos[:10]):
            self.assertEqual(situacao_antes, situacao_apos)
            
        # Novo entrante deve estar na 11
        self.assertIn((self.new.id, 11), ladder_apos)
            
        # Resultados de desafio posterior devem ser alterados
        resultados = desafio_posterior.resultadodesafioladder_set.all().values('jogador', 'alteracao_posicao')
        self.assertEqual(len(resultados), 3)
        self.assertIn({'jogador': self.jogador_pos_10.id, 'alteracao_posicao': -2}, resultados)
        self.assertIn({'jogador': self.jogador_pos_9.id, 'alteracao_posicao': 1}, resultados)
        self.assertIn({'jogador': self.new.id, 'alteracao_posicao': 1}, resultados)
        
        # Verificar posições para desafios
        self.assertEqual(desafio_anterior.posicao_desafiante, 11)
        self.assertEqual(desafio_anterior.posicao_desafiado, 10)
        self.assertEqual(desafio_posterior.posicao_desafiante, 11)
        self.assertEqual(desafio_posterior.posicao_desafiado, 9)
        
    def test_alterar_ladder_desafio_anterior_alterando_novo_entrante(self):
        """Testa alteração de ladder para marcar entrada anterior para novo entrante"""
        # Preparar desafios
        # Garantir que novo entrante desafie antes
        desafio_anterior = DesafioLadder(data_hora=timezone.localtime() - datetime.timedelta(days=5), 
                                          desafiante=self.desafio_ladder_novo_entrante_vitoria.desafiante,
                                          desafiado=self.desafio_ladder_novo_entrante_vitoria.desafiado,
                                          adicionado_por=self.desafio_ladder_novo_entrante_vitoria.adicionado_por,
                                          score_desafiante=3, score_desafiado=1, desafio_coringa=False)
        desafio_anterior.save()
        
        desafio_posterior = DesafioLadder(data_hora=self.desafio_ladder.data_hora - datetime.timedelta(minutes=5), 
                                          score_desafiante=self.desafio_ladder.score_desafiante, 
                                          score_desafiado=self.desafio_ladder.score_desafiado, desafio_coringa=False)
        desafio_posterior.desafiante = self.new_2
        desafio_posterior.desafiado = self.jogador_pos_10
        desafio_posterior.adicionado_por = self.jogador_pos_10
        desafio_posterior.admin_validador = self.jogador_pos_1
        desafio_posterior.save()
        
        alterar_ladder(desafio_posterior)
        
        # Verificar resultados
        resultados = desafio_posterior.resultadodesafioladder_set.all().values('jogador', 'alteracao_posicao')
        self.assertEqual(len(resultados), 2)
        self.assertIn({'jogador': self.jogador_pos_10.id, 'alteracao_posicao': 1}, resultados)
        self.assertIn({'jogador': self.new_2.id, 'alteracao_posicao': -1}, resultados)
        
        # Verificar posições no desafio
        self.assertEqual(desafio_posterior.posicao_desafiante, 11)
        self.assertEqual(desafio_posterior.posicao_desafiado, 10)
        
        # Pegar situação da ladder antes
        ladder_antes = list(PosicaoLadder.objects.all().order_by('posicao').values_list('jogador', 'posicao'))
        
        # Validar e alterar
        desafio_anterior.admin_validador = self.jogador_pos_1
        desafio_anterior.save()
        alterar_ladder(desafio_anterior)
        
        # Atualizar
        desafio_anterior.refresh_from_db()
        desafio_posterior.refresh_from_db()
        
        # Pegar situação da ladder após
        ladder_apos = list(PosicaoLadder.objects.all().order_by('posicao').values_list('jogador', 'posicao'))
        
        # Tamanho da ladder deve aumentar 1 posição
        self.assertEqual(len(ladder_antes) + 1, len(ladder_apos))
            
        # Outras posições permanecem
        for situacao_antes, situacao_apos in zip(ladder_antes[:9], ladder_apos[:9]):
            self.assertEqual(situacao_antes, situacao_apos)
            
        # Novo entrante 1 deve estar na 10
        self.assertIn((self.new.id, 10), ladder_apos)
        # Novo entrante 2 deve estar na 11
        self.assertIn((self.new_2.id, 11), ladder_apos)
            
        # Resultados de desafio posterior devem ser alterados
        resultados = desafio_posterior.resultadodesafioladder_set.all().values('jogador', 'alteracao_posicao')
        self.assertEqual(len(resultados), 2)
        self.assertIn({'jogador': self.jogador_pos_10.id, 'alteracao_posicao': 1}, resultados)
        self.assertIn({'jogador': self.new_2.id, 'alteracao_posicao': -1}, resultados)
        
        # Verificar posições para desafios
        self.assertEqual(desafio_anterior.posicao_desafiante, 11)
        self.assertEqual(desafio_anterior.posicao_desafiado, 10)
        self.assertEqual(desafio_posterior.posicao_desafiante, 12)
        self.assertEqual(desafio_posterior.posicao_desafiado, 11)
        
    def test_alterar_ladder_adicionando_entrantes_apos_remocao(self):
        """Testa alteração de ladder adicionando novos entrantes após uma remoção"""
        # Preparar desafios
        # Garantir que novo entrante desafie antes
        desafio = self.desafio_ladder_novos_entrantes_derrota
        
        # Remover jogador na posição 5
        remocao = RemocaoJogador.objects.create(admin_removedor=self.jogador_pos_1, data=desafio.data_hora - datetime.timedelta(days=1), 
                                      jogador=self.jogador_pos_5, posicao_jogador=5)
        remover_jogador(remocao)
        
        # Pegar situação da ladder antes
        ladder_antes = list(PosicaoLadder.objects.all().order_by('posicao').values_list('jogador', 'posicao'))
        
        # Validar e alterar
        desafio.admin_validador = self.jogador_pos_1
        desafio.save()
        alterar_ladder(desafio)
        
        # Atualizar
        desafio.refresh_from_db()
        
        # Pegar situação da ladder após
        ladder_apos = list(PosicaoLadder.objects.all().order_by('posicao').values_list('jogador', 'posicao'))
        
        # Tamanho da ladder deve aumentar 2 posições
        self.assertEqual(len(ladder_antes) + 2, len(ladder_apos))
            
        # Outras posições permanecem
        for situacao_antes, situacao_apos in zip(ladder_antes[:9], ladder_apos[:9]):
            self.assertEqual(situacao_antes, situacao_apos)
            
        # Novo entrante 1 deve estar na 11
        self.assertIn((self.new.id, 11), ladder_apos)
        # Novo entrante 2 deve estar na 10
        self.assertIn((self.new_2.id, 10), ladder_apos)
        
        # Verificar posições para desafios
        self.assertEqual(desafio.posicao_desafiante, 11)
        self.assertEqual(desafio.posicao_desafiado, 10)
        
    def test_alterar_ladder_removendo_data_anterior_entrada_novos_entrantes(self):
        """Testa alteração de ladder removendo um jogador antes de desafios que trouxeram novos entrantes"""
        # Preparar desafios
        # Garantir que novo entrante desafie antes
        desafio = self.desafio_ladder_novos_entrantes_derrota
        
        # Validar e alterar
        desafio.admin_validador = self.jogador_pos_1
        desafio.save()
        alterar_ladder(desafio)
        
        # Pegar situação da ladder antes
        ladder_antes = list(PosicaoLadder.objects.all().order_by('posicao').values_list('jogador', 'posicao'))
        
        # Remover jogador na posição 5
        remocao = RemocaoJogador.objects.create(admin_removedor=self.jogador_pos_1, data=desafio.data_hora - datetime.timedelta(days=1), 
                                      jogador=self.jogador_pos_5, posicao_jogador=5)
        remover_jogador(remocao)
        
        # Atualizar
        desafio.refresh_from_db()
        
        # Pegar situação da ladder após
        ladder_apos = list(PosicaoLadder.objects.all().order_by('posicao').values_list('jogador', 'posicao'))
        
        # Tamanho da ladder deve diminuir 1 posição
        self.assertEqual(len(ladder_antes) - 1, len(ladder_apos))
            
        # Posições acima de 5 mantém
        for situacao_antes, situacao_apos in zip(ladder_antes[:4], ladder_apos[:4]):
            self.assertEqual(situacao_antes, situacao_apos)
            
        # 5 para baixo deslocam 1 posição
        for situacao_antes, situacao_apos in zip(ladder_antes[5:10], ladder_apos[4:9]):
            self.assertEqual(situacao_antes[0], situacao_apos[0])
            self.assertEqual(situacao_antes[1]-1, situacao_apos[1])
            
        # Novo entrante 1 deve estar na 11
        self.assertIn((self.new.id, 11), ladder_apos)
        # Novo entrante 2 deve estar na 10
        self.assertIn((self.new_2.id, 10), ladder_apos)
        
        # Verificar posições para desafios
        self.assertEqual(desafio.posicao_desafiante, 11)
        self.assertEqual(desafio.posicao_desafiado, 10)
        
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
        
#         # Jogadores para validar alterações no ranking
#         cls.jogadores = [cls.jogador_pos_1, cls.jogador_pos_2,
#                          cls.jogador_pos_3, cls.jogador_pos_4,
#                          cls.jogador_pos_5, cls.jogador_pos_6,
#                          cls.jogador_pos_7]
        
        # Criar ladder inicial
        criar_ladder_inicial_teste()
        
        # Criar ladder atual
        criar_ladder_teste()
        
        # Preparar mês anterior para histórico
        horario_atual = timezone.localtime()
        cls.mes, cls.ano = mes_ano_ant(horario_atual.month, horario_atual.year)
        
        criar_ladder_historico_teste(cls.ano, cls.mes)
        
        # Criar novo entrante
        cls.new = criar_jogador_teste('new')
        
        horario_historico = horario_atual.replace(month=cls.mes, year=cls.ano)
        
        cls.desafio_ladder = criar_desafio_ladder_simples_teste(cls.jogador_pos_4, cls.jogador_pos_1, 3, 1, 
                                                                          horario_atual.replace(hour=5), False, cls.jogador_pos_1)
        cls.desafio_ladder_derrota = criar_desafio_ladder_simples_teste(cls.jogador_pos_7, cls.jogador_pos_6, 0, 3, 
                                                                          horario_atual.replace(hour=6), False, cls.jogador_pos_1)
        cls.desafio_ladder_historico = criar_desafio_ladder_simples_teste(cls.jogador_pos_3, cls.jogador_pos_2, 3, 1, 
                                                                          horario_historico.replace(hour=5), False, cls.jogador_pos_1)
        cls.desafio_ladder_historico_derrota = criar_desafio_ladder_simples_teste(cls.jogador_pos_6, cls.jogador_pos_5, 0, 3, 
                                                                          horario_historico.replace(hour=6), False, cls.jogador_pos_1)
        
        # Desafios coringa
        cls.desafio_ladder_coringa = criar_desafio_ladder_simples_teste(cls.jogador_pos_7, cls.jogador_pos_1, 3, 1, 
                                                                          horario_atual.replace(hour=7), True, cls.jogador_pos_1)
        cls.desafio_ladder_historico_coringa = criar_desafio_ladder_simples_teste(cls.jogador_pos_7, cls.jogador_pos_3, 3, 1, 
                                                                          horario_historico.replace(hour=7), True, cls.jogador_pos_1)
        
        # Desafios de novo entrante
        cls.desafio_ladder_novo_entrante_vitoria = criar_desafio_ladder_simples_teste(cls.new, cls.jogador_pos_10, 3, 1, 
                                                                          horario_atual.replace(day=15, hour=8), False, cls.jogador_pos_1)
        cls.desafio_ladder_novo_entrante_derrota = criar_desafio_ladder_simples_teste(cls.new, cls.jogador_pos_10, 0, 3, 
                                                                          horario_atual.replace(day=5, hour=9), False, cls.jogador_pos_1)
        
        
    def test_erro_recalcular_ladder_apenas_mes(self):
        """Testa erro por chamar função sem especificar ano"""
        with self.assertRaisesMessage(ValueError, 'Informe um ano'):
            recalcular_ladder(mes=self.mes)
        
    def test_erro_recalcular_ladder_apenas_ano(self):
        """Testa erro por chamar função sem especificar mês"""
        with self.assertRaisesMessage(ValueError, 'Informe um mês'):
            recalcular_ladder(ano=self.ano)
        
    def test_recalcular_ladder_atual_com_historico(self):
        """Testa recalcular posições de ladder atual partindo de histórico anterior"""
        # Validar desafios
        # Jogador 3 ganhou de 1
        validar_desafio_ladder_teste(self.desafio_ladder, self.jogador_pos_1)
        # Novo entrante ganhou de 10
        validar_desafio_ladder_teste(self.desafio_ladder_novo_entrante_vitoria, self.jogador_pos_1)
        # Jogador 7 ganhou de 1 com coringa, mas teve desafio de ladder cancelado
        validar_desafio_ladder_teste(self.desafio_ladder_coringa, self.jogador_pos_1)
        CancelamentoDesafioLadder.objects.create(desafio_ladder=self.desafio_ladder_coringa, jogador=self.jogador_pos_1)
        
        # Simular sumiço de ladder atual
        PosicaoLadder.objects.all().delete()
        
        # Recalcula ladder atual
        recalcular_ladder()
        
        # Buscar ladder atual
        ladder = list(PosicaoLadder.objects.all().order_by('posicao').values_list('jogador', 'posicao'))
        
        # Ladder deve ter 11 posições
        self.assertEqual(len(ladder), 11)
        
        # Jogador 4 deve estar na posição 1
        self.assertIn((self.jogador_pos_4.id, 1), ladder)
        
        # Jogador 1 deve estar na posição 2
        self.assertIn((self.jogador_pos_1.id, 2), ladder)
        
        # Jogador 2 deve estar na posição 3
        self.assertIn((self.jogador_pos_2.id, 3), ladder)
        
        # Jogador 3 deve estar na posição 4
        self.assertIn((self.jogador_pos_3.id, 4), ladder)
        
        # Novo entrante deve estar na posição 10
        self.assertIn((self.new.id, 10), ladder)
        
        # Jogador 10 deve estar em 11
        self.assertIn((self.jogador_pos_10.id, 11), ladder)
        
    def test_recalcular_ladder_atual_sem_historico(self):
        """Testa recalcular posições de ladder atual partindo da posição inicial"""
        # Validar desafios
        # Jogador 7 ganhou de 1
        validar_desafio_ladder_teste(self.desafio_ladder_coringa, self.jogador_pos_1)
        # Novo entrante perdeu de 10
        validar_desafio_ladder_teste(self.desafio_ladder_novo_entrante_derrota, self.jogador_pos_1)
        
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
        # Validar desafios
        # Jogador 3 ganhou de 2
        validar_desafio_ladder_teste(self.desafio_ladder_historico, self.jogador_pos_1)
        # Jogador 7 ganhou de 3
        validar_desafio_ladder_teste(self.desafio_ladder_historico_coringa, self.jogador_pos_1)
        
        # Simular sumiço de ladder histórico
        HistoricoLadder.objects.all().delete()
        
        # Criar ladder histórico de mês anterior a ladder histórico
        mes_hist_anterior, ano_hist_anterior = mes_ano_ant(self.mes, self.ano)
        criar_ladder_historico_teste(ano_hist_anterior, mes_hist_anterior)
        
        # Recalcula ladder histórico
        recalcular_ladder(mes=self.mes, ano=self.ano)
        
        # Buscar ladder atual
        ladder = list(HistoricoLadder.objects.filter(mes=self.mes, ano=self.ano).order_by('posicao').values_list('jogador', 'posicao'))
        
        # Jogador 3 deve estar na posição 3
        self.assertIn((self.jogador_pos_3.id, 3), ladder)
        
        # Jogador 2 deve estar na posição 4
        self.assertIn((self.jogador_pos_2.id, 4), ladder)
        
        # Jogador 7 deve estar na posição 2
        self.assertIn((self.jogador_pos_7.id, 2), ladder)
        
        # Jogador 4 deve estar em 5
        self.assertIn((self.jogador_pos_4.id, 5), ladder)
        
        # Jogador 5 deve estar em 6
        self.assertIn((self.jogador_pos_5.id, 6), ladder)
        
        # Jogador 6 deve estar em 7
        self.assertIn((self.jogador_pos_6.id, 7), ladder)
        
    def test_recalcular_ladder_historico_sem_historico(self):
        """Testa recalcular posições de ladder histórica partindo da posição inicial"""
        # Validar desafios
        # Jogador 3 ganhou de 2
        validar_desafio_ladder_teste(self.desafio_ladder_historico, self.jogador_pos_1)
        # Jogador 7 ganhou de 3
        validar_desafio_ladder_teste(self.desafio_ladder_historico_coringa, self.jogador_pos_1)
        
        # Simular sumiço de ladder histórico
        HistoricoLadder.objects.all().delete()
        
        # Recalcula ladder atual
        recalcular_ladder(mes=self.mes, ano=self.ano)
        
        # Buscar ladder atual
        ladder = list(HistoricoLadder.objects.filter(mes=self.mes, ano=self.ano).order_by('posicao').values_list('jogador', 'posicao'))
        
        # Jogador 3 deve estar na posição 3
        self.assertIn((self.jogador_pos_3.id, 3), ladder)
        
        # Jogador 2 deve estar na posição 4
        self.assertIn((self.jogador_pos_2.id, 4), ladder)
        
        # Jogador 7 deve estar na posição 2
        self.assertIn((self.jogador_pos_7.id, 2), ladder)
        
        # Jogador 4 deve estar em 5
        self.assertIn((self.jogador_pos_4.id, 5), ladder)
        
        # Jogador 5 deve estar em 6
        self.assertIn((self.jogador_pos_5.id, 6), ladder)
        
        # Jogador 6 deve estar em 7
        self.assertIn((self.jogador_pos_6.id, 7), ladder)
        
    def test_erro_recalcular_atual_com_alteracao_historico_impossivel(self):
        """Testar recálculo de posição atual com alteração no histórico que impossibilita posições"""
        # Validar desafios
        # Jogador 4 derrotou o 1 esse mês
        validar_desafio_ladder_teste(self.desafio_ladder, self.jogador_pos_1)
        # Jogador 6 derrotou o 4 mês passado
        with self.assertRaises(ValueError):
            validar_desafio_ladder_teste(self.desafio_ladder_historico_coringa, self.jogador_pos_1)
        
#         # Simular sumiço de ladder atual
#         PosicaoLadder.objects.all().delete()
        
#         # Recalcula ladder atual, deve dar erro na validação de desafio para jogador 3 derrotando jogador 1
#         regex = re.escape(f'Desafio Ladder {self.desafio_ladder.id}: ') + r'.+'
#         with self.assertRaisesRegex(ValueError, regex):
#             recalcular_ladder()

    def test_alterar_ladder_deve_desfazer_decaimento(self):
        """Testa se alteração de ladder desfaz um decaimento para o jogador"""
        # Realizar decaimento
        decaimento = DecaimentoJogador.objects.create(jogador=self.jogador_pos_4, data=timezone.localtime() + datetime.timedelta(days=1), 
                                                      posicao_inicial=4, qtd_periodos_inatividade=1)
        decair_jogador(decaimento)
        
        self.assertTrue(PosicaoLadder.objects.filter(posicao=4, jogador=self.jogador_pos_5).exists())
        self.assertTrue(PosicaoLadder.objects.filter(posicao=5, jogador=self.jogador_pos_6).exists())
        self.assertTrue(PosicaoLadder.objects.filter(posicao=6, jogador=self.jogador_pos_7).exists())
        self.assertTrue(PosicaoLadder.objects.filter(posicao=7, jogador=self.jogador_pos_4).exists())
        
        # Alterar ladder
        validar_desafio_ladder_teste(self.desafio_ladder, self.jogador_pos_1)
        
        # Decaimento deve ser apagado e seus resultados desfeitos
        self.assertFalse(DecaimentoJogador.objects.filter(jogador=self.jogador_pos_4).exists())
        self.assertTrue(PosicaoLadder.objects.filter(posicao=2, jogador=self.jogador_pos_1).exists())
        self.assertTrue(PosicaoLadder.objects.filter(posicao=3, jogador=self.jogador_pos_2).exists())
        self.assertTrue(PosicaoLadder.objects.filter(posicao=4, jogador=self.jogador_pos_3).exists())
        self.assertTrue(PosicaoLadder.objects.filter(posicao=1, jogador=self.jogador_pos_4).exists())
        self.assertTrue(PosicaoLadder.objects.filter(posicao=5, jogador=self.jogador_pos_5).exists())
        self.assertTrue(PosicaoLadder.objects.filter(posicao=6, jogador=self.jogador_pos_6).exists())
        self.assertTrue(PosicaoLadder.objects.filter(posicao=7, jogador=self.jogador_pos_7).exists())

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
        
        # Criar ladders para verificar que adicionar desafio não as afeta
        criar_ladder_teste()
        
        # Preparar mês anterior para histórico
        data_atual = timezone.localdate()
        cls.mes, cls.ano = mes_ano_ant(data_atual.month, data_atual.year)
        
        criar_ladder_historico_teste(cls.ano, cls.mes)
        
    def test_desafiante_desafiado_mesmo_jogador(self):
        """Desafiante e desafiado são o mesmo jogador"""
        desafio = DesafioLadder(desafiante=self.jogador_pos_3, desafiado=self.jogador_pos_3, data_hora=timezone.now(), desafio_coringa=False)
        with self.assertRaisesMessage(ValueError, DesafioLadder.MENSAGEM_ERRO_MESMO_JOGADOR):
#             verificar_posicoes_desafiante_desafiado(PosicaoLadder.objects, self.jogador_pos_3, self.jogador_pos_3, timezone.now(), False)
            verificar_posicoes_desafiante_desafiado(desafio)
        
    def test_desafiante_abaixo_qtd_menos_1_posicao_desafiado_ladder_atual(self):
        """Desafiante está abaixo LIMITE_POSICOES_DESAFIO-1 posição portanto pode desafiar, ladder atual"""
        desafio = DesafioLadder(desafiante=self.jogador_pos_5, desafiado=self.jogador_pos_3, data_hora=timezone.now(), desafio_coringa=False)
#         verificar_posicoes_desafiante_desafiado(PosicaoLadder.objects, self.jogador_pos_4, self.jogador_pos_3, timezone.now(), False)
        verificar_posicoes_desafiante_desafiado(desafio)
        
    def test_desafiante_abaixo_qtd_posicao_desafiado_ladder_atual(self):
        """Desafiante está abaixo LIMITE_POSICOES_DESAFIO posições portanto pode desafiar, ladder atual"""
        desafio = DesafioLadder(desafiante=self.jogador_pos_6, desafiado=self.jogador_pos_3, data_hora=timezone.now(), desafio_coringa=False)
#         verificar_posicoes_desafiante_desafiado(PosicaoLadder.objects, self.jogador_pos_5, self.jogador_pos_3, timezone.now(), False)
        verificar_posicoes_desafiante_desafiado(desafio)
        
    def test_desafiante_abaixo_qtd_mais_1_posicao_desafiado_ladder_atual(self):
        """Desafiante está abaixo LIMITE_POSICOES_DESAFIO+1 posições portanto não pode desafiar, ladder atual"""
        desafio = DesafioLadder(desafiante=self.jogador_pos_7, desafiado=self.jogador_pos_3, data_hora=timezone.now(), desafio_coringa=False)
        with self.assertRaisesMessage(ValueError, DesafioLadder.MENSAGEM_ERRO_DESAFIANTE_MUITO_ABAIXO_DESAFIADO):
#             verificar_posicoes_desafiante_desafiado(PosicaoLadder.objects, self.jogador_pos_6, self.jogador_pos_3, timezone.now(), False)
            verificar_posicoes_desafiante_desafiado(desafio)
    
    def test_desafiante_abaixo_qtd_menos_1_posicao_desafiado_ladder_historico(self):
        """Desafiante está abaixo LIMITE_POSICOES_DESAFIO-1 posição portanto pode desafiar, ladder histórico"""
        desafio = DesafioLadder(desafiante=self.jogador_pos_5, desafiado=self.jogador_pos_3, 
                                data_hora=timezone.now().replace(month=self.mes, year=self.ano), desafio_coringa=False)
#         verificar_posicoes_desafiante_desafiado(HistoricoLadder.objects.filter(ano=self.ano, mes=self.mes), 
#                                                               self.jogador_pos_4, self.jogador_pos_3, timezone.now(), False)
        verificar_posicoes_desafiante_desafiado(desafio)
        
    def test_desafiante_abaixo_qtd_posicao_desafiado_ladder_historico(self):
        """Desafiante está abaixo LIMITE_POSICOES_DESAFIO posições portanto pode desafiar, ladder histórico"""
        desafio = DesafioLadder(desafiante=self.jogador_pos_6, desafiado=self.jogador_pos_3, 
                                data_hora=timezone.now().replace(month=self.mes, year=self.ano), desafio_coringa=False)
#         verificar_posicoes_desafiante_desafiado(HistoricoLadder.objects.filter(ano=self.ano, mes=self.mes), 
#                                                               self.jogador_pos_5, self.jogador_pos_3, timezone.now(), False)
        verificar_posicoes_desafiante_desafiado(desafio)
        
    def test_desafiante_abaixo_qtd_mais_1_posicao_desafiado_ladder_historico(self):
        """Desafiante está abaixo LIMITE_POSICOES_DESAFIO+1 posições portanto não pode desafiar, ladder histórico"""
        desafio = DesafioLadder(desafiante=self.jogador_pos_7, desafiado=self.jogador_pos_3, 
                                data_hora=timezone.now().replace(month=self.mes, year=self.ano), desafio_coringa=False)
        with self.assertRaisesMessage(ValueError, DesafioLadder.MENSAGEM_ERRO_DESAFIANTE_MUITO_ABAIXO_DESAFIADO):
#             verificar_posicoes_desafiante_desafiado(HistoricoLadder.objects.filter(ano=self.ano, mes=self.mes), 
#                                                                   self.jogador_pos_6, self.jogador_pos_3, timezone.now(), False)
            verificar_posicoes_desafiante_desafiado(desafio)
    
    def test_desafiante_acima_desafiado_ladder_atual(self):
        """Desafiante está acima de desafiado no ranking portanto não pode desafiar, ladder atual"""
        desafio = DesafioLadder(desafiante=self.jogador_pos_5, desafiado=self.jogador_pos_6, 
                                data_hora=timezone.now(), desafio_coringa=False)
        with self.assertRaisesMessage(ValueError, DesafioLadder.MENSAGEM_ERRO_DESAFIANTE_ACIMA_DESAFIADO):
#             verificar_posicoes_desafiante_desafiado(PosicaoLadder.objects, self.jogador_pos_5, self.jogador_pos_6, timezone.now(), False)
            verificar_posicoes_desafiante_desafiado(desafio)
    
    def test_desafiante_acima_desafiado_ladder_historico(self):
        """Desafiante está acima de desafiado no ranking portanto não pode desafiar, ladder histórico"""
        desafio = DesafioLadder(desafiante=self.jogador_pos_5, desafiado=self.jogador_pos_6, 
                                data_hora=timezone.now().replace(month=self.mes, year=self.ano), desafio_coringa=False)
        with self.assertRaisesMessage(ValueError, DesafioLadder.MENSAGEM_ERRO_DESAFIANTE_ACIMA_DESAFIADO):
#             verificar_posicoes_desafiante_desafiado(HistoricoLadder.objects.filter(ano=self.ano, mes=self.mes), 
#                                                               self.jogador_pos_5, self.jogador_pos_6, timezone.now(), False)
            verificar_posicoes_desafiante_desafiado(desafio)
    
    def test_desafiante_ferias(self):
        """Desafiante está de férias portanto não pode desafiar ninguém"""
        # Criar desafio férias
        RegistroFerias.objects.create(jogador=self.jogador_pos_6, data_inicio=(timezone.now() - datetime.timedelta(days=10)),
                                      data_fim=(timezone.now() + datetime.timedelta(days=10)))
        
        desafio = DesafioLadder(desafiante=self.jogador_pos_6, desafiado=self.jogador_pos_5, 
                                data_hora=timezone.now(), desafio_coringa=False)
        with self.assertRaisesMessage(ValueError, DesafioLadder.MENSAGEM_ERRO_DESAFIANTE_FERIAS):
#             verificar_posicoes_desafiante_desafiado(PosicaoLadder.objects, self.jogador_pos_6, self.jogador_pos_5, timezone.now(), False)
            verificar_posicoes_desafiante_desafiado(desafio)
    
    def test_desafiado_ferias(self):
        """Jogador desafiado está de férias portanto não pode ser desafiado"""
        # Criar desafio férias
        RegistroFerias.objects.create(jogador=self.jogador_pos_5, data_inicio=(timezone.now() - datetime.timedelta(days=10)),
                                      data_fim=(timezone.now() + datetime.timedelta(days=10)))
        
        desafio = DesafioLadder(desafiante=self.jogador_pos_6, desafiado=self.jogador_pos_5, 
                                data_hora=timezone.now(), desafio_coringa=False)
        with self.assertRaisesMessage(ValueError, DesafioLadder.MENSAGEM_ERRO_DESAFIADO_FERIAS):
#             verificar_posicoes_desafiante_desafiado(PosicaoLadder.objects, self.jogador_pos_6, self.jogador_pos_5, timezone.now(), False)
            verificar_posicoes_desafiante_desafiado(desafio)
    
    def test_desafiante_qtd_mais_1_posicoes_abaixo_proximo_com_ferias(self):
        """Desafiante está LIMITE_POSICOES_DESAFIO+1 posições abaixo, mas o jogador logo acima está de férias, pode desafiar"""
        # Criar desafio férias
        RegistroFerias.objects.create(jogador=self.jogador_pos_5, data_inicio=(timezone.now() - datetime.timedelta(days=10)),
                                      data_fim=(timezone.now() + datetime.timedelta(days=10)))
        
        desafio = DesafioLadder(desafiante=self.jogador_pos_7, desafiado=self.jogador_pos_3, 
                                data_hora=timezone.now(), desafio_coringa=False)
#         verificar_posicoes_desafiante_desafiado(PosicaoLadder.objects, self.jogador_pos_6, self.jogador_pos_3, timezone.now(), False)
        verificar_posicoes_desafiante_desafiado(desafio)
    
    def test_desafiante_qtd_mais_2_posicoes_abaixo_proximo_com_ferias(self):
        """Desafiante está LIMITE_POSICOES_DESAFIO+2 abaixo e o próximo acima está de férias, portanto não pode desafiar"""
        # Criar desafio férias
        RegistroFerias.objects.create(jogador=self.jogador_pos_5, data_inicio=(timezone.now() - datetime.timedelta(days=10)),
                                      data_fim=(timezone.now() + datetime.timedelta(days=10)))
        
        desafio = DesafioLadder(desafiante=self.jogador_pos_7, desafiado=self.jogador_pos_2, 
                                data_hora=timezone.now(), desafio_coringa=False)
        with self.assertRaisesMessage(ValueError, DesafioLadder.MENSAGEM_ERRO_DESAFIANTE_MUITO_ABAIXO_DESAFIADO):
#             verificar_posicoes_desafiante_desafiado(PosicaoLadder.objects, self.jogador_pos_6, self.jogador_pos_2, timezone.now(), False)
            verificar_posicoes_desafiante_desafiado(desafio)
    
    def test_desafiante_qtd_mais_2_posicoes_abaixo_2_proximos_com_ferias(self):
        """Desafiante está LIMITE_POSICOES_DESAFIO+2 abaixo mas os 2 próximos jogadores estão de férias, portanto pode desafiar"""
        # Criar desafios férias
        RegistroFerias.objects.create(jogador=self.jogador_pos_5, data_inicio=(timezone.now() - datetime.timedelta(days=10)),
                                      data_fim=(timezone.now() + datetime.timedelta(days=10)))
        RegistroFerias.objects.create(jogador=self.jogador_pos_4, data_inicio=(timezone.now() - datetime.timedelta(days=10)),
                                      data_fim=(timezone.now() + datetime.timedelta(days=10)))
        
        desafio = DesafioLadder(desafiante=self.jogador_pos_7, desafiado=self.jogador_pos_2, 
                                data_hora=timezone.now(), desafio_coringa=False)
#         verificar_posicoes_desafiante_desafiado(PosicaoLadder.objects, self.jogador_pos_6, self.jogador_pos_2, timezone.now(), False)
        verificar_posicoes_desafiante_desafiado(desafio)
        
    def test_desafio_coringa_ladder_atual(self):
        """Desafiante usa desafio coringa na ladder atual, basta desafiado não estar de férias"""
        # Criar desafio férias
        RegistroFerias.objects.create(jogador=self.jogador_pos_3, data_inicio=(timezone.now() - datetime.timedelta(days=10)),
                                      data_fim=(timezone.now() + datetime.timedelta(days=10)))
        
        for jogador in self.jogadores:
            # Desafiante não pode desafiar a si mesmo
            if jogador == self.jogador_pos_7:
                pass
            elif jogador == self.jogador_pos_3:
                desafio = DesafioLadder(desafiante=self.jogador_pos_7, desafiado=jogador, 
                                        data_hora=timezone.now(), desafio_coringa=True)
                with self.assertRaisesMessage(ValueError, DesafioLadder.MENSAGEM_ERRO_DESAFIADO_FERIAS):
#                     verificar_posicoes_desafiante_desafiado(PosicaoLadder.objects, self.jogador_pos_7, jogador, timezone.now(), True)
                    verificar_posicoes_desafiante_desafiado(desafio)
            else:
                desafio = DesafioLadder(desafiante=self.jogador_pos_7, desafiado=jogador, 
                                        data_hora=timezone.now(), desafio_coringa=True)
#                 verificar_posicoes_desafiante_desafiado(PosicaoLadder.objects, self.jogador_pos_7, jogador, timezone.now(), True)
                verificar_posicoes_desafiante_desafiado(desafio)

class CopiarLadderTestCase(TestCase):
    """Testes para a função que copia uma ladder em outra"""
    @classmethod
    def setUpTestData(cls):
        super(CopiarLadderTestCase, cls).setUpTestData()
        
        criar_jogadores_teste()
        
        # Pegar objetos de jogador de acordo com sua posição
        cls.jogador_pos_1 = Jogador.objects.get(nick='teets')
        cls.jogador_pos_2 = Jogador.objects.get(nick='saraiva')
        cls.jogador_pos_3 = Jogador.objects.get(nick='sena')
        cls.jogador_pos_4 = Jogador.objects.get(nick='mad')
        cls.jogador_pos_5 = Jogador.objects.get(nick='blöwer')
        cls.jogador_pos_6 = Jogador.objects.get(nick='frodo')
        cls.jogador_pos_7 = Jogador.objects.get(nick='dan')
        cls.jogador_pos_8 = Jogador.objects.get(nick='phils')
        cls.jogador_pos_9 = Jogador.objects.get(nick='rata')
        cls.jogador_pos_10 = Jogador.objects.get(nick='tiovsky')
        
        # Criar ladders para verificar que adicionar desafio não as afeta
        criar_ladder_teste()
        
        # Preparar mês anterior para histórico
        data_atual = timezone.now().date()
        cls.mes, cls.ano = mes_ano_ant(data_atual.month, data_atual.year)
        
        criar_ladder_historico_teste(cls.ano, cls.mes)
        
    def test_copiar_registros_ladders_iguais(self):
        """Testa copiar registros entre ladders iguais"""
        ladder_destino = PosicaoLadder.objects.all()
        ladder_origem = HistoricoLadder.objects.all()
        
        ladder_destino_antes = list(ladder_destino.order_by('posicao'))
        
        copiar_ladder(ladder_destino, ladder_origem)
        
        ladder_destino_depois = list(ladder_destino.order_by('posicao'))
        
        for registro_antes, registro_depois in zip(ladder_destino_antes, ladder_destino_depois):
            self.assertEqual(registro_antes.posicao, registro_depois.posicao)
            self.assertEqual(registro_antes.jogador, registro_depois.jogador)
            
        for registro_origem, registro_depois in zip(list(ladder_origem.order_by('posicao')), ladder_destino_depois):
            self.assertEqual(registro_origem.posicao, registro_depois.posicao)
            self.assertEqual(registro_origem.jogador, registro_depois.jogador)
    
    def test_copiar_registros_mesmos_jogadores(self):
        """Testa copiar registros entre ladders com mesmos jogadores porém posições diferentes"""
        ladder_destino = PosicaoLadder.objects.all()
        ladder_origem = HistoricoLadder.objects.all()
        
        # Alterar posições na ladder de destino, jogador 5 vai parar posição 3, 3 para 4 e 4 para 5
        jogador_3 = ladder_destino.get(posicao=3)
        jogador_4 = ladder_destino.get(posicao=4)
        jogador_5 = ladder_destino.get(posicao=5)
        
        # Remover posição para poder atualizar
        jogador_5.posicao = 0
        jogador_5.save()
        
        jogador_4.posicao = 5
        jogador_4.save()
        jogador_3.posicao = 4
        jogador_3.save()
        jogador_5.posicao = 3
        jogador_5.save()
        
        ladder_destino_antes = list(ladder_destino.order_by('posicao'))
        
        copiar_ladder(ladder_destino, ladder_origem)
        
        ladder_destino_depois = list(ladder_destino.order_by('posicao'))
        
        # Posições 1 e 2 devem estar iguais
        for registro_antes, registro_depois in zip(ladder_destino_antes[:2], ladder_destino_depois[:2]):
            self.assertEqual(registro_antes.posicao, registro_depois.posicao)
            self.assertEqual(registro_antes.jogador, registro_depois.jogador)
        
        # Posições 3 a 5 devem estar diferentes
        for registro_antes, registro_depois in zip(ladder_destino_antes[2:5], ladder_destino_depois[2:5]):
            self.assertEqual(registro_antes.posicao, registro_depois.posicao)
            self.assertNotEqual(registro_antes.jogador, registro_depois.jogador)
            
        # Da posição 6 em diante deve estar igual
        for registro_antes, registro_depois in zip(ladder_destino_antes[5:], ladder_destino_depois[5:]):
            self.assertEqual(registro_antes.posicao, registro_depois.posicao)
            self.assertEqual(registro_antes.jogador, registro_depois.jogador)
            
        for registro_origem, registro_depois in zip(list(ladder_origem.order_by('posicao')), ladder_destino_depois):
            self.assertEqual(registro_origem.posicao, registro_depois.posicao)
            self.assertEqual(registro_origem.jogador, registro_depois.jogador)
        
    def test_copiar_registros_para_historico(self):
        """Testa copiar registros para uma ladder de histórico"""
        ladder_destino = HistoricoLadder.objects.filter(mes=self.mes, ano=self.ano)
        ladder_origem = PosicaoLadder.objects.all()
        
        # Alterar posições na ladder de destino, jogador 5 vai parar posição 3, 3 para 4 e 4 para 5
        jogador_3 = ladder_destino.get(posicao=3)
        jogador_4 = ladder_destino.get(posicao=4)
        jogador_5 = ladder_destino.get(posicao=5)
        
        # Remover posição para poder atualizar
        jogador_5.posicao = 0
        jogador_5.save()
        
        jogador_4.posicao = 5
        jogador_4.save()
        jogador_3.posicao = 4
        jogador_3.save()
        jogador_5.posicao = 3
        jogador_5.save()
        
        # Remover última posição na ladder de destino
        ladder_destino.get(posicao=10).delete()
        
        ladder_destino_antes = list(ladder_destino.order_by('posicao'))
        
        copiar_ladder(ladder_destino, ladder_origem)
        
        ladder_destino_depois = list(ladder_destino.order_by('posicao'))
        
        # Posições 1 e 2 devem estar iguais
        for registro_antes, registro_depois in zip(ladder_destino_antes[:2], ladder_destino_depois[:2]):
            self.assertEqual(registro_antes.posicao, registro_depois.posicao)
            self.assertEqual(registro_antes.jogador, registro_depois.jogador)
        
        # Posições 3 a 5 devem estar diferentes
        for registro_antes, registro_depois in zip(ladder_destino_antes[2:5], ladder_destino_depois[2:5]):
            self.assertEqual(registro_antes.posicao, registro_depois.posicao)
            self.assertNotEqual(registro_antes.jogador, registro_depois.jogador)
            
        # Da posição 6 em diante deve estar igual
        for registro_antes, registro_depois in zip(ladder_destino_antes[5:], ladder_destino_depois[5:]):
            self.assertEqual(registro_antes.posicao, registro_depois.posicao)
            self.assertEqual(registro_antes.jogador, registro_depois.jogador)
            
        for registro_origem, registro_depois in zip(list(ladder_origem.order_by('posicao')), ladder_destino_depois):
            self.assertEqual(registro_origem.posicao, registro_depois.posicao)
            self.assertEqual(registro_origem.jogador, registro_depois.jogador)
        
    def test_erro_copiar_ladder_origem_vazia(self):
        """Testa erro ao copiar de uma ladder que está vazia"""
        # Apagar registros de ladder de origem
        HistoricoLadder.objects.all().delete()
        
        ladder_destino = PosicaoLadder.objects.all()
        ladder_origem = HistoricoLadder.objects.all()
        
        with self.assertRaisesMessage(ValueError, 'Ladder de origem não pode estar vazia'):
            copiar_ladder(ladder_destino, ladder_origem)
            
    def test_copiar_ladder_destino_historico_vazia(self):
        """Testa copiar para uma ladder de histórico que está vazia"""
        # Apagar registros de ladder de destino
        HistoricoLadder.objects.all().delete()
        
        ladder_destino = HistoricoLadder.objects.filter(mes=self.mes, ano=self.ano)
        ladder_origem = PosicaoLadder.objects.all()
        
        copiar_ladder(ladder_destino, ladder_origem, self.mes, self.ano)
        
        for registro_origem, registro_depois in zip(list(ladder_origem.order_by('posicao')), ladder_destino):
            self.assertEqual(registro_origem.posicao, registro_depois.posicao)
            self.assertEqual(registro_origem.jogador, registro_depois.jogador)
        
    def test_copiar_ladder_origem_com_mais_registros(self):
        """Testa copiar ladder com mais registros que destino"""
        # Remover registros da ladder destino
        PosicaoLadder.objects.filter(posicao__gte=9).delete()
        
        ladder_destino = PosicaoLadder.objects.all()
        ladder_origem = HistoricoLadder.objects.all()
        
        ladder_destino_antes = list(ladder_destino.order_by('posicao'))
        self.assertEqual(len(ladder_destino_antes), 8)
        
        copiar_ladder(ladder_destino, ladder_origem)
        
        ladder_destino_depois = list(ladder_destino.order_by('posicao'))
        self.assertEqual(len(ladder_destino_depois), 10)
        
        for registro_antes, registro_depois in zip(ladder_destino_antes[:8], ladder_destino_depois[:8]):
            self.assertEqual(registro_antes.posicao, registro_depois.posicao)
            self.assertEqual(registro_antes.jogador, registro_depois.jogador)
            
        for registro_origem, registro_depois in zip(list(ladder_origem.order_by('posicao')), ladder_destino_depois):
            self.assertEqual(registro_origem.posicao, registro_depois.posicao)
            self.assertEqual(registro_origem.jogador, registro_depois.jogador)
        
    def test_copiar_ladder_origem_com_menos_registros(self):
        """Testa copiar ladder com menos registros que destino"""
        # Remover registros da ladder de origem
        HistoricoLadder.objects.filter(posicao__gte=9).delete()
        
        ladder_destino = PosicaoLadder.objects.all()
        ladder_origem = HistoricoLadder.objects.all()
        
        ladder_destino_antes = list(ladder_destino.order_by('posicao'))
        self.assertEqual(len(ladder_destino_antes), 10)
        
        copiar_ladder(ladder_destino, ladder_origem)
        
        ladder_destino_depois = list(ladder_destino.order_by('posicao'))
        self.assertEqual(len(ladder_destino_depois), 8)
        
        for registro_antes, registro_depois in zip(ladder_destino_antes[:8], ladder_destino_depois[:8]):
            self.assertEqual(registro_antes.posicao, registro_depois.posicao)
            self.assertEqual(registro_antes.jogador, registro_depois.jogador)
            
        for registro_origem, registro_depois in zip(list(ladder_origem.order_by('posicao')), ladder_destino_depois):
            self.assertEqual(registro_origem.posicao, registro_depois.posicao)
            self.assertEqual(registro_origem.jogador, registro_depois.jogador)
            
class DecairJogadorTestCase(TestCase):
    """Testes para a função de decair jogador na ladder"""
    @classmethod
    def setUpTestData(cls):
        super(DecairJogadorTestCase, cls).setUpTestData()
        
        criar_jogadores_teste()
        
        # Pegar objetos de jogador de acordo com sua posição
        cls.jogador_pos_1 = Jogador.objects.get(nick='teets')
        cls.jogador_pos_2 = Jogador.objects.get(nick='saraiva')
        cls.jogador_pos_3 = Jogador.objects.get(nick='sena')
        cls.jogador_pos_4 = Jogador.objects.get(nick='mad')
        cls.jogador_pos_5 = Jogador.objects.get(nick='blöwer')
        cls.jogador_pos_6 = Jogador.objects.get(nick='frodo')
        cls.jogador_pos_7 = Jogador.objects.get(nick='dan')
        cls.jogador_pos_8 = Jogador.objects.get(nick='phils')
        cls.jogador_pos_9 = Jogador.objects.get(nick='rata')
        cls.jogador_pos_10 = Jogador.objects.get(nick='tiovsky')
        
        # Criar ladders para verificar que adicionar desafio não as afeta
        criar_ladder_teste()
        
        # Gerar decaimentos
        cls.decaimento_jogador_3 = DecaimentoJogador.objects.create(jogador=cls.jogador_pos_3, posicao_inicial=3, 
                                                     data=timezone.localtime(), qtd_periodos_inatividade=1)
        cls.decaimento_jogador_9 = DecaimentoJogador.objects.create(jogador=cls.jogador_pos_9, posicao_inicial=9, 
                                                     data=timezone.localtime(), qtd_periodos_inatividade=1)
        cls.decaimento_jogador_10 = DecaimentoJogador.objects.create(jogador=cls.jogador_pos_10, posicao_inicial=10, 
                                                      data=timezone.localtime(), qtd_periodos_inatividade=2)
        
    def test_decair_jogador_sucesso(self):
        """Testa decaimento de jogador com sucesso"""
        # Pegar situação da ladder antes
        ladder_antes = list(PosicaoLadder.objects.all().order_by('posicao').values_list('jogador', 'posicao'))
        
        # Decair jogador 3 por inatividade
        decair_jogador(self.decaimento_jogador_3)
        
        # Pegar situação da ladder após
        ladder_apos = list(PosicaoLadder.objects.all().order_by('posicao').values_list('jogador', 'posicao'))
        
        # Tamanho da ladder deve ser o mesmo
        self.assertEqual(len(ladder_antes), len(ladder_apos))
        
        # 2 primeiras posições não devem mudar
        for situacao_antes, situacao_apos in zip(ladder_antes[:2], ladder_apos[:2]):
            self.assertEqual(situacao_antes, situacao_apos)
            
        # Jogadores afetados pelo decaimento de 3
        self.assertIn((self.jogador_pos_3.id, 6), ladder_apos)
        self.assertIn((self.jogador_pos_4.id, 3), ladder_apos)
        self.assertIn((self.jogador_pos_5.id, 4), ladder_apos)
        self.assertIn((self.jogador_pos_6.id, 5), ladder_apos)
        
        # Outras permanecem
        for situacao_antes, situacao_apos in zip(ladder_antes[6:], ladder_apos[6:]):
            self.assertEqual(situacao_antes, situacao_apos)
            
        # Validar resultados
        resultados = self.decaimento_jogador_3.resultadodecaimentojogador_set.all()
        self.assertEqual(resultados.count(), 4)
        self.assertTrue(resultados.filter(decaimento=self.decaimento_jogador_3, jogador=self.jogador_pos_3, 
                                          alteracao_posicao=DecaimentoJogador.QTD_POSICOES_DECAIMENTO).exists())
        self.assertTrue(resultados.filter(decaimento=self.decaimento_jogador_3, jogador=self.jogador_pos_4, 
                                          alteracao_posicao=-1).exists())
        self.assertTrue(resultados.filter(decaimento=self.decaimento_jogador_3, jogador=self.jogador_pos_5, 
                                          alteracao_posicao=-1).exists())
        self.assertTrue(resultados.filter(decaimento=self.decaimento_jogador_3, jogador=self.jogador_pos_6, 
                                          alteracao_posicao=-1).exists())
        
            
    def test_decair_jogador_prox_final_ladder(self):
        """Testa decaimento de jogador com menos de QTD_POSICOES_DECAIMENTO posições do fim da ladder"""
        
        # Pegar situação da ladder antes
        ladder_antes = list(PosicaoLadder.objects.all().order_by('posicao').values_list('jogador', 'posicao'))
        
        # Decair jogador 9 por inatividade
        decair_jogador(self.decaimento_jogador_9)
        
        # Pegar situação da ladder após
        ladder_apos = list(PosicaoLadder.objects.all().order_by('posicao').values_list('jogador', 'posicao'))
        
        # Tamanho da ladder deve ser o mesmo
        self.assertEqual(len(ladder_antes), len(ladder_apos))
        
        # 2 primeiras posições não devem mudar
        for situacao_antes, situacao_apos in zip(ladder_antes[:7], ladder_apos[:7]):
            self.assertEqual(situacao_antes, situacao_apos)
            
        # Jogadores afetados pelo decaimento de 9
        self.assertIn((self.jogador_pos_9.id, 10), ladder_apos)
        self.assertIn((self.jogador_pos_10.id, 9), ladder_apos)
        
        # Validar resultados
        resultados = self.decaimento_jogador_9.resultadodecaimentojogador_set.all()
        self.assertEqual(resultados.count(), 2)
        self.assertTrue(resultados.filter(decaimento=self.decaimento_jogador_9, jogador=self.jogador_pos_9, 
                                          alteracao_posicao=1).exists())
        self.assertTrue(resultados.filter(decaimento=self.decaimento_jogador_9, jogador=self.jogador_pos_10, 
                                          alteracao_posicao=-1).exists())

    def test_decair_jogador_final_ladder(self):
        """Testa decaimento de jogador no fim da ladder, não deve alterar posição"""
        
        # Pegar situação da ladder antes
        ladder_antes = list(PosicaoLadder.objects.all().order_by('posicao').values_list('jogador', 'posicao'))
        
        # Decair jogador 10 por inatividade
        decair_jogador(self.decaimento_jogador_10)
        
        # Pegar situação da ladder após
        ladder_apos = list(PosicaoLadder.objects.all().order_by('posicao').values_list('jogador', 'posicao'))
        
        # Tamanho da ladder deve ser o mesmo
        self.assertEqual(len(ladder_antes), len(ladder_apos))
        
        # Posições não devem mudar
        for situacao_antes, situacao_apos in zip(ladder_antes, ladder_apos):
            self.assertEqual(situacao_antes, situacao_apos)
            
        # Validar resultados
        resultados = self.decaimento_jogador_3.resultadodecaimentojogador_set.all()
        self.assertEqual(resultados.count(), 0)
            
class AvaliarDecaimentoTestCase(TestCase):
    """Testes para a função de gerar decaimento de jogador"""
    @classmethod
    def setUpTestData(cls):
        super(AvaliarDecaimentoTestCase, cls).setUpTestData()
        
        criar_jogadores_teste()
        
        # Pegar objetos de jogador de acordo com sua posição
        cls.jogador_pos_1 = Jogador.objects.get(nick='teets')
        cls.jogador_pos_2 = Jogador.objects.get(nick='saraiva') # Último desafio validado a PERIODO_INATIVIDADE * 2 dias (gerar decaimento 2)
        cls.jogador_pos_3 = Jogador.objects.get(nick='sena') # Último desafio validado a PERIODO_INATIVIDADE + 5 dias (férias de 5 dias)
        cls.jogador_pos_4 = Jogador.objects.get(nick='mad') # Último desafio validado a PERIODO_INATIVIDADE + 4 dias (férias de 5 dias)
        cls.jogador_pos_5 = Jogador.objects.get(nick='blöwer') # Último desafio validado a PERIODO_INATIVIDADE - 1 dias
        cls.jogador_pos_6 = Jogador.objects.get(nick='frodo') # Último desafio validado a PERIODO_INATIVIDADE  dias
        cls.jogador_pos_7 = Jogador.objects.get(nick='dan') # Último desafio validado a PERIODO_INATIVIDADE + 1 dias (sem registro)
        cls.jogador_pos_8 = Jogador.objects.get(nick='phils') # Último desafio validado a PERIODO_INATIVIDADE + 1 dias (com registro)
        cls.jogador_pos_9 = Jogador.objects.get(nick='rata') # Último desafio validado a PERIODO_INATIVIDADE dias
        cls.jogador_pos_10 = Jogador.objects.get(nick='tiovsky') # Último desafio validado a PERIODO_INATIVIDADE dias
        
        # Criar novo entrante
        cls.new = criar_jogador_teste('new')
        
        # Criar ladders para verificar que adicionar desafio não as afeta
        criar_ladder_teste()
        
        # Gerar desafios validados
        # Jogador posição 2
        desafio_2 = criar_desafio_ladder_simples_teste(cls.jogador_pos_2, cls.jogador_pos_1, 0, 3, 
                                                       timezone.localtime() - datetime.timedelta(days=DecaimentoJogador.PERIODO_INATIVIDADE*2), 
                                                       False, cls.jogador_pos_1, 2, 1)
        validar_desafio_ladder_teste(desafio_2, cls.jogador_pos_1, False)
        DecaimentoJogador.objects.create(jogador=cls.jogador_pos_2, data=timezone.localtime() - datetime.timedelta(days=DecaimentoJogador.PERIODO_INATIVIDADE), 
                                         posicao_inicial=1, qtd_periodos_inatividade=1)
        
        # Jogador posição 3
        desafio_3 = criar_desafio_ladder_simples_teste(cls.jogador_pos_3, cls.jogador_pos_1, 0, 3, 
                                                       timezone.localtime() - datetime.timedelta(days=DecaimentoJogador.PERIODO_INATIVIDADE+5), 
                                                       False, cls.jogador_pos_1, 3, 1)
        validar_desafio_ladder_teste(desafio_3, cls.jogador_pos_1, False)
        # Adicionar registro férias de 5 dias
        RegistroFerias.objects.create(jogador=cls.jogador_pos_3, data_inicio=timezone.localdate() - datetime.timedelta(days=10), 
                                      data_fim=timezone.localdate() - datetime.timedelta(days=5))
        
        # Jogador posição 4
        desafio_4 = criar_desafio_ladder_simples_teste(cls.jogador_pos_4, cls.jogador_pos_1, 0, 3, 
                                                       timezone.localtime() - datetime.timedelta(days=DecaimentoJogador.PERIODO_INATIVIDADE+4), 
                                                       False, cls.jogador_pos_1, 4, 1)
        validar_desafio_ladder_teste(desafio_4, cls.jogador_pos_1, False)
        # Adicionar registro férias de 5 dias
        RegistroFerias.objects.create(jogador=cls.jogador_pos_4, data_inicio=timezone.localdate() - datetime.timedelta(days=10), 
                                      data_fim=timezone.localdate() - datetime.timedelta(days=5))
        
        # Jogador posição 5
        desafio_5 = criar_desafio_ladder_simples_teste(cls.jogador_pos_5, cls.jogador_pos_1, 0, 3, 
                                                       timezone.localtime() - datetime.timedelta(days=DecaimentoJogador.PERIODO_INATIVIDADE-1), 
                                                       True, cls.jogador_pos_1, 5, 1)
        validar_desafio_ladder_teste(desafio_5, cls.jogador_pos_1, False)
        
        # Jogador posição 6
        desafio_6 = criar_desafio_ladder_simples_teste(cls.jogador_pos_6, cls.jogador_pos_1, 0, 3, 
                                                       timezone.localtime() - datetime.timedelta(days=DecaimentoJogador.PERIODO_INATIVIDADE), 
                                                       True, cls.jogador_pos_1, 6, 1)
        validar_desafio_ladder_teste(desafio_6, cls.jogador_pos_1, False)
        
        # Jogador posição 7
        desafio_7 = criar_desafio_ladder_simples_teste(cls.jogador_pos_7, cls.jogador_pos_1, 0, 3, 
                                                       timezone.localtime() - datetime.timedelta(days=DecaimentoJogador.PERIODO_INATIVIDADE+1), 
                                                       True, cls.jogador_pos_1, 7, 1)
        validar_desafio_ladder_teste(desafio_7, cls.jogador_pos_1, False)
        
        # Jogador posição 8
        desafio_8 = criar_desafio_ladder_simples_teste(cls.jogador_pos_8, cls.jogador_pos_1, 0, 3, 
                                                       timezone.localtime() - datetime.timedelta(days=DecaimentoJogador.PERIODO_INATIVIDADE+1), 
                                                       True, cls.jogador_pos_1, 8, 1)
        validar_desafio_ladder_teste(desafio_8, cls.jogador_pos_1, False)
        DecaimentoJogador.objects.create(jogador=cls.jogador_pos_8, data=timezone.localtime() - datetime.timedelta(days=1), 
                                         posicao_inicial=5, qtd_periodos_inatividade=1)
        
        # Jogador posição 9
        desafio_9 = criar_desafio_ladder_simples_teste(cls.jogador_pos_9, cls.jogador_pos_1, 0, 3, 
                                                       timezone.localtime() - datetime.timedelta(days=DecaimentoJogador.PERIODO_INATIVIDADE), 
                                                       True, cls.jogador_pos_1, 9, 1)
        validar_desafio_ladder_teste(desafio_9, cls.jogador_pos_1, False)
        
        # Jogador posição 10
        desafio_10 = criar_desafio_ladder_simples_teste(cls.jogador_pos_10, cls.jogador_pos_1, 0, 3, 
                                                       timezone.localtime() - datetime.timedelta(days=DecaimentoJogador.PERIODO_INATIVIDADE), 
                                                       True, cls.jogador_pos_1, 10, 1)
        validar_desafio_ladder_teste(desafio_10, cls.jogador_pos_1, False)
        
    def test_avaliar_jogador_quase_periodo_inatividade(self):
        """Testa avaliar jogador próximo de completar período de inatividade"""
        # Não deve gerar decaimento
        self.assertEqual(avaliar_decaimento(self.jogador_pos_5), None)
        
    def test_avaliar_jogador_no_periodo_inatividade(self):
        """Testa avaliar jogador que acaba de completar período de inatividade"""
        # Deve gerar decaimento
        decaimento = avaliar_decaimento(self.jogador_pos_6)
        
        self.assertEqual(decaimento.jogador, self.jogador_pos_6)
        self.assertEqual(decaimento.data.date(), timezone.localdate())
        self.assertEqual(decaimento.posicao_inicial, 6)
#         self.assertEqual(decaimento.posicao_final, 6 + DecaimentoJogador.QTD_POSICOES_DECAIMENTO)
        self.assertEqual(decaimento.qtd_periodos_inatividade, 1)
        
    def test_avaliar_jogador_apos_periodo_inatividade_sem_registro(self):
        """Testa avaliar jogador após período de inatividade, sem registro de decaimento"""
        # Deve gerar decaimento
        decaimento = avaliar_decaimento(self.jogador_pos_7)
        
        self.assertEqual(decaimento.jogador, self.jogador_pos_7)
        self.assertEqual(decaimento.data.date(), timezone.localdate() - datetime.timedelta(days=1))
        self.assertEqual(decaimento.posicao_inicial, 7)
#         self.assertEqual(decaimento.posicao_final, 7 + DecaimentoJogador.QTD_POSICOES_DECAIMENTO)
        self.assertEqual(decaimento.qtd_periodos_inatividade, 1)
        
    def test_avaliar_jogador_apos_periodo_inatividade_com_registro(self):
        """Testa avaliar jogador após período de inatividade, com registro de decaimento"""
        # Não deve gerar decaimento
        self.assertEqual(avaliar_decaimento(self.jogador_pos_8), None)
        
    def test_avaliar_jogador_decaimento_prox_fim_ladder(self):
        """Testa avaliar decaimento de jogador próximo ao fim da ladder"""
        # Deve gerar decaimento
        decaimento = avaliar_decaimento(self.jogador_pos_9)
        
        self.assertEqual(decaimento.jogador, self.jogador_pos_9)
        self.assertEqual(decaimento.data.date(), timezone.localdate())
        self.assertEqual(decaimento.posicao_inicial, 9)
#         self.assertEqual(decaimento.posicao_final, 10)
        self.assertEqual(decaimento.qtd_periodos_inatividade, 1)
        
    def test_avaliar_jogador_decaimento_fim_ladder(self):
        """Testa avaliar decaimento de jogador no fim da ladder"""
        # Deve gerar decaimento
        decaimento = avaliar_decaimento(self.jogador_pos_10)
        
        self.assertEqual(decaimento.jogador, self.jogador_pos_10)
        self.assertEqual(decaimento.data.date(), timezone.localdate())
        self.assertEqual(decaimento.posicao_inicial, 10)
#         self.assertEqual(decaimento.posicao_final, 10)
        self.assertEqual(decaimento.qtd_periodos_inatividade, 1)
        
    def test_avaliar_jogador_decaimento_2_periodos_inatividade(self):
        """Testa avaliar decaimento para jogador há 2 perídos inativo"""
        # Deve gerar decaimento
        decaimento = avaliar_decaimento(self.jogador_pos_2)
        
        self.assertEqual(decaimento.jogador, self.jogador_pos_2)
        self.assertEqual(decaimento.data.date(), timezone.localdate())
        self.assertEqual(decaimento.posicao_inicial, 2)
#         self.assertEqual(decaimento.posicao_final, 2 + DecaimentoJogador.QTD_POSICOES_DECAIMENTO)
        self.assertEqual(decaimento.qtd_periodos_inatividade, 2)
        
    def test_avaliar_jogador_ferias_sem_cair_no_periodo_inatividade(self):
        """Testa avaliar jogador com férias que não cai no período de inatividade"""
        # Não deve gerar decaimento
        self.assertEqual(avaliar_decaimento(self.jogador_pos_4), None)
        
    def test_avaliar_jogador_ferias_caindo_no_periodo_inatividade(self):
        """Testa avaliar jogador com férias que cai no período de inatividade"""
        # Deve gerar decaimento
        decaimento = avaliar_decaimento(self.jogador_pos_3)
        
        self.assertEqual(decaimento.jogador, self.jogador_pos_3)
        self.assertEqual(decaimento.data.date(), timezone.localdate())
        self.assertEqual(decaimento.posicao_inicial, 3)
#         self.assertEqual(decaimento.posicao_final, 3 + DecaimentoJogador.QTD_POSICOES_DECAIMENTO)
        self.assertEqual(decaimento.qtd_periodos_inatividade, 1)
        
    def test_avaliar_jogador_fora_ladder(self):
        """Testa erro avaliar jogador que não está na ladder"""
        # Deve jogar erro
        with self.assertRaisesMessage(ValueError, f'{self.new} não está na ladder'):
            avaliar_decaimento(self.new)
            
class BuscarDesafiaveisTestCase(TestCase):
    """Testes para a função de buscar jogadores desafiáveis"""
    @classmethod
    def setUpTestData(cls):
        super(BuscarDesafiaveisTestCase, cls).setUpTestData()
        criar_jogadores_teste()
        
        # Pegar objetos de jogador de acordo com sua posição
        cls.jogador_pos_1 = Jogador.objects.get(nick='teets')
        cls.jogador_pos_2 = Jogador.objects.get(nick='saraiva')
        cls.jogador_pos_3 = Jogador.objects.get(nick='sena')
        cls.jogador_pos_4 = Jogador.objects.get(nick='mad')
        cls.jogador_pos_5 = Jogador.objects.get(nick='blöwer')
        cls.jogador_pos_6 = Jogador.objects.get(nick='frodo')
        cls.jogador_pos_6.posicao_ladder = 6
        cls.jogador_pos_7 = Jogador.objects.get(nick='dan')
        cls.jogador_pos_8 = Jogador.objects.get(nick='phils')
        cls.jogador_pos_9 = Jogador.objects.get(nick='rata')
        cls.jogador_pos_10 = Jogador.objects.get(nick='tiovsky')
        
        
    
        criar_ladder_teste()
    
    def test_trazer_desafiaveis_com_sucesso(self):
        """Testa trazer os desafiáveis para jogador"""
        desafiaveis = buscar_desafiaveis(self.jogador_pos_6, timezone.localtime())
        
        self.assertEqual(len(desafiaveis), DesafioLadder.LIMITE_POSICOES_DESAFIO)
        for jogador_id in desafiaveis:
            self.assertIn(PosicaoLadder.objects.get(jogador__id=jogador_id).posicao, 
                          list(range(self.jogador_pos_6.posicao_ladder - 1, self.jogador_pos_6.posicao_ladder - 1 \
                                      - DesafioLadder.LIMITE_POSICOES_DESAFIO, -1)))
        
    def test_erro_jogador_nao_preenchido(self):
        """Testa erro ao não enviar jogador"""
        with self.assertRaisesMessage(ValueError, 'Desafiante inválido'):
            buscar_desafiaveis(None, timezone.localtime())
        
    def test_erro_data_hora_nao_preenchida(self):
        """Testa erro ao não enviar data/hora"""
        with self.assertRaisesMessage(ValueError, 'Data/hora inválida'):
            buscar_desafiaveis(self.jogador_pos_6, None)
        
    def test_trazer_desafiaveis_sucesso_coringa(self):
        """Testa trazer desafiáveis para desafio coringa"""
        desafiaveis = buscar_desafiaveis(self.jogador_pos_6, timezone.localtime(), True)
        
        self.assertEqual(len(desafiaveis), self.jogador_pos_6.posicao_ladder - 1)
        for jogador_id in desafiaveis:
            self.assertIn(PosicaoLadder.objects.get(jogador__id=jogador_id).posicao, 
                          list(range(self.jogador_pos_6.posicao_ladder - 1, 0, -1)))
            
    def test_erro_desafiante_nao_possui_coringa(self):
        """Testa erro caso desafiante ainda não possa utilizar coringa"""
        # Adicionar uso de coringa para jogador
        self.jogador_pos_6.ultimo_uso_coringa = timezone.localdate() - datetime.timedelta(days=1)
        self.jogador_pos_6.save()
        
        with self.assertRaisesMessage(ValueError, 'Jogador não pode usar coringa na data'):
            buscar_desafiaveis(self.jogador_pos_6, timezone.localtime(), True)
            
        # Apagar uso de coringa
        self.jogador_pos_6.ultimo_uso_coringa = None
        self.jogador_pos_6.save()
        
    def test_trazer_desafiaveis_com_ferias(self):
        """Testa se jogador de férias é excluído de desafiáveis e o próximo da lista entra no seu lugar"""
        # Adicionar férias para jogador na posição 5
        RegistroFerias.objects.create(jogador=self.jogador_pos_5, data_inicio=timezone.localdate(), 
                                      data_fim=timezone.localdate() + datetime.timedelta(days=10))
        
        desafiaveis = buscar_desafiaveis(self.jogador_pos_6, timezone.localtime())
        
        self.assertEqual(len(desafiaveis), DesafioLadder.LIMITE_POSICOES_DESAFIO)
        for jogador_id in desafiaveis:
            self.assertIn(PosicaoLadder.objects.get(jogador__id=jogador_id).posicao, 
                          list(range(self.jogador_pos_6.posicao_ladder - 1, self.jogador_pos_6.posicao_ladder - 1 \
                                      - DesafioLadder.LIMITE_POSICOES_DESAFIO - 1, -1)))
    
    def test_trazer_lista_vazia_para_1_lugar(self):
        """Testa se desafiante for o primeiro colocado, trazer lista vazia"""
        desafiaveis = buscar_desafiaveis(self.jogador_pos_1, timezone.localtime())
        
        self.assertEqual(len(desafiaveis), 0)
        
    def test_trazer_desafiaveis_anterior_a_desafio(self):
        """Testa se desafios posteriores à data informada são desfeitos para listar desafiáveis"""
        desafio = criar_desafio_ladder_simples_teste(self.jogador_pos_6, self.jogador_pos_4, 3, 0, timezone.localtime(), False, 
                                                     self.jogador_pos_6, 6, 4)
        
        validar_desafio_ladder_teste(desafio, self.jogador_pos_1)
        desafiaveis_atual = buscar_desafiaveis(self.jogador_pos_6, timezone.localtime())
        desafiaveis_anterior = buscar_desafiaveis(self.jogador_pos_6, timezone.localtime() - datetime.timedelta(minutes=30))
        
        self.assertEqual(len(desafiaveis_anterior), len(desafiaveis_atual))
        self.assertNotEqual(desafiaveis_anterior, desafiaveis_atual)
        self.assertIn(self.jogador_pos_3.id, desafiaveis_atual)
        self.assertIn(self.jogador_pos_2.id, desafiaveis_atual)
        self.assertIn(self.jogador_pos_1.id, desafiaveis_atual)
        
    def test_trazer_ultimos_para_desafiante_fora_ladder(self):
        """Testa trazer os últimos colocados da ladder para caso de desafiante novo entrante"""
        novo_jogador = criar_jogador_teste('new')
        posicao_jogador = 11
        
        desafiaveis = buscar_desafiaveis(novo_jogador, timezone.localtime())
        
        self.assertEqual(len(desafiaveis), DesafioLadder.LIMITE_POSICOES_DESAFIO)
        for jogador_id in desafiaveis:
            self.assertIn(PosicaoLadder.objects.get(jogador__id=jogador_id).posicao, 
                          list(range(posicao_jogador - 1, posicao_jogador - 1 - DesafioLadder.LIMITE_POSICOES_DESAFIO, -1)))
            
    def test_nao_trazer_novos_entrantes_apos_data_hora(self):
        """Testa se jogadores novos entrantes após data/hora da checagem não são retornados"""
        novo_jogador_1 = criar_jogador_teste('new')
        
        novo_jogador_2 = criar_jogador_teste('new_2')
        posicao_jogador_2 = 11
        
        desafio = criar_desafio_ladder_simples_teste(novo_jogador_2, self.jogador_pos_9, 3, 0, timezone.localtime(), False, 
                                                     self.jogador_pos_9, posicao_jogador_2, 9)
        
        validar_desafio_ladder_teste(desafio, self.jogador_pos_1)
        
        desafiaveis = buscar_desafiaveis(novo_jogador_1, timezone.localtime() - datetime.timedelta(minutes=5))
        
        self.assertEqual(len(desafiaveis), DesafioLadder.LIMITE_POSICOES_DESAFIO)
        
        self.assertIn(self.jogador_pos_10.id, desafiaveis)
        self.assertIn(self.jogador_pos_9.id, desafiaveis)
        self.assertIn(self.jogador_pos_8.id, desafiaveis)
        