class BuscarTorneioChallongeTestCase(TestCase):

class SalvarTorneioChallongeTestCase(TestCase):

class BuscarJogadoresTorneioChallongeTestCase(TestCase):

class SalvarJogadoresTorneioChallongeTestCase(TestCase):

class BuscarPartidasChallongeTestCase(TestCase):

class SalvarPartidasChallongeTestCase(TestCase):

class VincularAutomaticamenteJogadorTorneioAJogadorLadder(TestCase):
    """Testes para vinculação entre jogador de torneio e jogador da ladder"""
    @classmethod
    def setUpTestData(cls):
        super(VincularJogadorTorneioJogadorLadder, cls).setUpTestData()
        
        criar_jogadores_teste()
        # Jogadores
        cls.teets = Jogador.objects.get(nick='teets')
        cls.saraiva = Jogador.objects.get(nick='saraiva')
        cls.sena = Jogador.objects.get(nick='sena')
        cls.mad = Jogador.objects.get(nick='mad')
        cls.blower = Jogador.objects.get(nick='blöwer')
        cls.frodo = Jogador.objects.get(nick='frodo')
        cls.dan = Jogador.objects.get(nick='dan')
        cls.phils = Jogador.objects.get(nick='phils')
        cls.rata = Jogador.objects.get(nick='rata')
        cls.tiovsky = Jogador.objects.get(nick='tiovsky')
        
        cls.torneio = criar_torneio_teste()
    
    
    def test_verificar_se_vinculos_foram_gerados(self):
        vincular_automaticamente_jogadores_torneio_a_ladder(self.torneio)
        
        # Testar jogadores vinculados
        self.assertTrue(self.teets.jogadortorneio_set.count() > 0)
        self.assertFalse(self.saraiva.jogadortorneio_set.count() > 0)
        self.assertTrue(self.sena.jogadortorneio_set.count() > 0)
        self.assertTrue(self.mad.jogadortorneio_set.count() > 0)
        self.assertFalse(self.blower.jogadortorneio_set.count() > 0)
        self.assertFalse(self.frodo.jogadortorneio_set.count() > 0)
        self.assertFalse(self.dan.jogadortorneio_set.count() > 0)
        self.assertTrue(self.phils.jogadortorneio_set.count() > 0)
        self.assertFalse(self.rata.jogadortorneio_set.count() > 0)
        self.assertFalse(self.tiovsky.jogadortorneio_set.count() > 0)
        
    def test_verificar_vinculos_gerados_com_vinculos_recentes(self):
        # Vincular primeiro torneio
        vincular_automaticamente_jogadores_torneio_a_ladder(self.torneio)
        self.torneio_2 = criar_torneio_teste('Torneio 2', outra_data)
        
        vincular_automaticamente_jogadores_torneio_a_ladder(self.torneio_2)
        
    def test_verificar_vinculos_gerados_sem_vinculos_recentes(self):
        # Vincular primeiro torneio
        vincular_automaticamente_jogadores_torneio_a_ladder(self.torneio)
        
        # Outro torneio está a uma diferença maior do que é considerado recente
        self.torneio_2 = criar_torneio_teste('Torneio 2', outra_data)
        
        vincular_automaticamente_jogadores_torneio_a_ladder(self.torneio_2)
    