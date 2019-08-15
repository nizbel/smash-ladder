class ViewRemoverPermissaoAumentoRangeTestCase(TestCase):
    """Testes para a view de remover permissão de aumento de range"""
    @classmethod
    def setUpTestData(cls):
        super(ViewRemoverPermissaoAumentoRangeTestCase, cls).setUpTestData()
        criar_jogadores_teste(['sena', 'teets',])
        cls.jogador_1 = Jogador.objects.get(nick='sena')
        cls.admin = Jogador.objects.get(nick='teets')
        cls.jogador_6 = Jogador.objects.get(nick='')
        
    def test_acesso_deslogado(self):
        """Testa acesso a tela de remover permissão de aumento de range sem logar"""
        response = self.client.get(reverse('ladder:remover_permissao_aumento_range'))
        url_esperada = settings.LOGIN_URL + '?next=' + reverse('ladder:remover_permissao_aumento_range')
        self.assertRedirects(response, url_esperada)
        self.assertEqual(response.status_code, 302)
        
    def test_acesso_logado(self):
        """Testa acesso a tela de remover permissão de aumento de range logando sem admin"""
        self.client.login(username=self.jogador_1.user.username, password=SENHA_TESTE)
        response = self.client.get(reverse('ladder:remover_permissao_aumento_range'))
        self.assertEqual(response.status_code, 403)
    
    def test_acesso_logado_admin(self):
        """Testa acesso a tela de remover permissão de aumento de range logando como admin"""
        self.client.login(username=self.jogador_2.user.username, password=SENHA_TESTE)
        response = self.client.get(reverse('ladder:remover_permissao_aumento_range'))
        self.assertEqual(response.status_code, 200)
        
    def test_remover_permissao_sucesso(self):
        """Testa remover uma permissão com sucesso"""
        # Gerar permissão para remoção
        permissao = PermissaoAumentoRange.objects.create(admin_permissor=self.jogador_2.id, jogador=self.jogador_1.id, data_hora=timezone.localtime())
        
        self.client.login(username=self.jogador_2.user.username, password=SENHA_TESTE)
        response = self.client.post(reverse('ladder:remover_permissao_aumento_range'), {permissao_id: permissao.id})
        self.assertEqual(response.status_code, 200)
        
        messages = list(response.context['messages'])
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), PermissaoAumentoRange.MENSAGEM_SUCESSO_REMOCAO_PERMISSAO)
        
        # Verificar que não há mais permissões cadastradas
        self.assertEqual(PermissaoAumentoRange.objects.all().count(), 0)
        
    def test_erro_remover_permissao_com_desafio_cadastrado(self):
        """Testa erro ao tentar remover permissão que já possui desafio cadastrado"""
        # Gerar permissão para remoção
        permissao = PermissaoAumentoRange.objects.create(admin_permissor=self.jogador_2.id, jogador=self.jogador_1.id, data_hora=timezone.localtime())
        # Cadastrar desafio usando permissão
        desafio = DesafioLadder.objects.create(desafiante=self.jogador_6, desafiado=self.jogador_2, data_hora=timezone.localtime(), score_desafiante=0, 
            score_desafiado=3, coringa=False)
        test_validar_desafio(desafio)
        
        self.client.login(username=self.jogador_2.user.username, password=SENHA_TESTE)
        response = self.client.post(reverse('ladder:remover_permissao_aumento_range'), {permissao_id: permissao.id})
        self.assertEqual(response.status_code, 200)
        
        messages = list(response.context['messages'])
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), PermissaoAumentoRange.MENSAGEM_ERRO_DESAFIO_UTILIZANDO_PERMISSAO)
        
        # Verificar que não há mais permissões cadastradas
        self.assertEqual(PermissaoAumentoRange.objects.all().count(), 1)
        
    def test_remover_permissao_com_desafio_cancelado(self):
        """Testa sucesso ao remover permissão que possui desafio cadastrado porém cancelado"""
        # Gerar permissão para remoção
        permissao = PermissaoAumentoRange.objects.create(admin_permissor=self.jogador_2.id, jogador=self.jogador_6.id, data_hora=timezone.localtime())
        # Cadastrar desafio usando permissão
        desafio = DesafioLadder.objects.create(desafiante=self.jogador_6, desafiado=self.jogador_2, data_hora=timezone.localtime(), score_desafiante=0, 
            score_desafiado=3, coringa=False)
        test_validar_desafio(desafio)
        # Cancelar desafio
        test_cancelar_desafio(desafio)
        
        self.client.login(username=self.jogador_2.user.username, password=SENHA_TESTE)
        response = self.client.post(reverse('ladder:remover_permissao_aumento_range'), {permissao_id: permissao.id})
        self.assertEqual(response.status_code, 200)
        
        messages = list(response.context['messages'])
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), PermissaoAumentoRange.MENSAGEM_SUCESSO_REMOCAO_PERMISSAO)
        
        # Verificar que não há mais permissões cadastradas
        self.assertEqual(PermissaoAumentoRange.objects.all().count(), 0)
        
    def test_nao_mostrar_permissoes_com_remocao_impossivel(self):
        """Testa se tela não mostra permissões cuja remoção não seja possível, por tempo decorrido ou já utilizada"""
        # Adicionar permissão com período inválido
        permissao_passada = PermissaoAumentoRange.objects.create(admin_permissor=self.jogador_2.id, jogador=self.jogador_1.id, data_hora=timezone.localtime() \
            - datetime.timedelta(hours=PermissaoAumentoRange.PERIODO_PERMISSAO + 1))
        
        # Adicionar permissão com desafio já cadastrado
        permissao_utilizada = PermissaoAumentoRange.objects.create(admin_permissor=self.jogador_2.id, jogador=self.jogador_6.id, data_hora=timezone.localtime())
        # Cadastrar desafio usando permissão
        desafio = DesafioLadder.objects.create(desafiante=self.jogador_6, desafiado=self.jogador_2, data_hora=timezone.localtime(), score_desafiante=0, 
            score_desafiado=3, coringa=False)
        test_validar_desafio(desafio)
        
        # Adicionar permissão válida
        permissao_valida = PermissaoAumentoRange.objects.create(admin_permissor=self.jogador_2.id, jogador=self.jogador_1.id, data_hora=timezone.localtime())
        
        self.client.login(username=self.jogador_2.user.username, password=SENHA_TESTE)
        response = self.client.get(reverse('ladder:remover_permissao_aumento_range'), {permissao_id: permissao.id})
        self.assertEqual(response.status_code, 200)
        
        # Verificar quais permissões estão sendo mostradas
        self.assertEqual(len(response.context['permissoes']), 1)
        self.assertEqual(response.context['permissoes'][0], permissao_valida)
        
        # Permitir remover
        self.assertNotContains(response, reverse('ladder:remover_permissao_aumento_range', kwargs={'permissao_id': permissao_valida.id}))
        
        