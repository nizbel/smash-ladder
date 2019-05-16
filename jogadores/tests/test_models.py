# -*- coding: utf-8 -*-

class JogadorTestCase(TestCase):
    """Testes para o model Jogador"""
    @classmethod
    def setUpTestData(cls):
        super(JogadorTestCase, cls).setUpTestData()
        
        criar_jogadores_teste()
        
        cls.teets = Jogador.objects.get(nick='teets')
        cls.sena = Jogador.objects.get(nick='sena')
        cls.mad = Jogador.objects.get(nick='mad')
        
        # Criar ladder original
        
        # Criar ladder histórico e atual
        
        # Adicionar desafios
        
    def test_is_de_ferias_jogador_sem_ferias(self):
        """Testa se retorno indica que jogador não está de férias"""
        # TODO Alterar is_de_ferias para usar localtime em vez de now
        self.assertFalse(self.teets.is_de_ferias())
        
    def test_is_de_ferias_jogador_de_ferias(self):
        """Testa se retorno indica que jogador está de férias"""
        # Colocar jogador de férias
        RegistroFerias.objects.create(jogador=self.teets, data_inicio=timezone.now() - datetime.timedelta(days=5), data_fim=timezone.now() + datetime.timedelta(days=5))
        self.assertTrue(self.teets.is_de_ferias())
        
    def test_de_ferias_na_data_jogador_sem_ferias(self):
        """Testa se retorno indica que jogador não está de férias na data"""
        self.assertFalse(self.teets.de_ferias_na_data(timezone.now() - datetime.timedelta(days=5)))
        
    def test_de_ferias_na_data_jogador_de_ferias(self):
        """Testa se retorno indica que jogador está de férias na data"""
        # Colocar jogador de férias
        RegistroFerias.objects.create(jogador=self.teets, data_inicio=timezone.now() - datetime.timedelta(days=5), data_fim=timezone.now() + datetime.timedelta(days=5))
        self.assertFalse(self.teets.de_ferias_na_data(timezone.now() - datetime.timedelta(days=5)))
        
    def test_posicao_em_jogador_sem_desafios_nem_ladder_inicial(self):
        """Testa se retorno é 0 caso jogador não esteja na ladder inicial nem possua desafios"""
        self.assertEqual(self.mad.posicao_em(timezone.now(), 0)
        
    def test_posicao_em_jogador_sem_desafios_com_ladder_inicial(self):
        """Testa se retorno é a posição do jogador na ladder inicial"""
    
    def test_posicao_em_jogador_com_desafios_validados(self):
        """Testa se retorno é posição do jogador após o último desafio validado"""
    
    def test_posicao_em_jogador_com_desafios_pendentes(self):
        """Testa se retorno desconsidera desafios pendentes"""

    def test_posicao_em_jogador_com_desafios_cancelados(self):
        """Testa se retorno desconsidera desafios cancelados"""
    
    def test_posicao_em_jogador_com_desafios_removido_ladder(self):
        """Testa se retorno é 0 devido a remoção da ladder"""