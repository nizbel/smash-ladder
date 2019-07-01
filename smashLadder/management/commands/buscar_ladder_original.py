# -*- coding: utf-8 -*-
import json

from django.core.management.base import BaseCommand
from django.db import transaction

from ladder.models import InicioLadder, HistoricoLadder
from smashLadder import settings
from smashLadder.utils import mes_ano_ant


class Command(BaseCommand):
    help = 'Testa ver ladder inicial ao remover desafios'

    def handle(self, *args, **options):
        # Não rodar em produção
        if settings.DEBUG == False:
            return
        
        mes_ano_validos = list()
        for ano, mes in HistoricoLadder.objects.filter(ano__lte=2002).order_by('ano', 'mes').values('ano', 'mes').distinct().values_list('ano', 'mes'):
            ladder_mes = HistoricoLadder.objects.filter(ano=ano, mes=mes).order_by('posicao').values_list('jogador__nick', 'posicao')
            
            if ('Mad', 6) in ladder_mes:
                if ('Niz', 10) in ladder_mes:
                    if ('Blöwer', 4) in ladder_mes:
                        if ('C0ox', 9) in ladder_mes:
                            if ('Bacabau', 5) in ladder_mes:
                                if ('Yalda', 3) in ladder_mes:
                                    mes_ano_validos.append((mes, ano))
        
        print('qtd validos:', len(mes_ano_validos))
        for mes, ano in mes_ano_validos:
            print(f'{mes}/{ano}:', HistoricoLadder.objects.filter(ano=ano, mes=mes).order_by('posicao').values_list('jogador__nick', 'posicao'))
        
        if 2 == 2:
            return
#         HistoricoLadder.objects.filter(ano__lte=2002).delete()
        try:
            mes = 12
            ano = 2001
            
            nova_ladder = InicioLadder.objects.all().select_related('jogador').order_by('posicao')
            
            # Decrementar mes ano para poder copiar
            mes, ano = mes_ano_ant(mes, ano)
            nova_opcao = copiar_ladder_como_historico(nova_ladder, mes, ano)
            opcoes_ladder = [nova_opcao,]
            
            print('Inicial:', nova_ladder.values_list('jogador__nick', 'posicao'))
            with open('templates/desafios.json', 'r') as arq:
                desafios = json.load(arq)
#                     print(desafios)
                
                for desafio in reversed(desafios):
                    with transaction.atomic():
                
                        jogador_1 = desafio['jogador_1']
                        score_1 = desafio['score_jogador_1']
                        jogador_2 = desafio['jogador_2']
                        score_2 = desafio['score_jogador_2']
                        print('-----------------------------------')
                        print(jogador_1, jogador_2)
                        
                        # Guardar próximo índice a ser avaliado
                        indice_prox = 0
                        
                        # Guardar opções que serão removidas
                        opcoes_a_remover = list()
                        
                        # Percorrer todas as possibilidades
                        for indice, opcao_ladder in enumerate(opcoes_ladder):
                            # Barrar novas entradas na lista
                            if indice < indice_prox:
                                continue
                            
                            indice_prox = indice + 1
                            
    #                             if len(opcoes_ladder) < 4:
    #                                 print([situacao.values_list('jogador__nick', 'posicao') for situacao in opcoes_ladder])
                            
                            print(f'Indice atual: {indice+1} de {len(opcoes_ladder)}')
                            # Desfazer desafio
                            posicao_1 = opcao_ladder.get(jogador__nick=jogador_1).posicao
                            posicao_2 = opcao_ladder.get(jogador__nick=jogador_2).posicao
    #                             print(f'Luta: {jogador_1} em {posicao_1} e  {jogador_2} em {posicao_2}')
    #                             print(opcao_ladder.values_list('jogador__nick', 'posicao'))
                            
    #                             jogador_verificar_1 = 'CPU'
    #                             jogador_verificar_2 = 'Yalda'
    #                             posicao_verificar_1 = opcao_ladder.get(jogador__nick=jogador_verificar_1).posicao
    #                             posicao_verificar_2 = opcao_ladder.get(jogador__nick=jogador_verificar_2).posicao
    #                             print(f'Posições a verificar: {jogador_verificar_1} em {posicao_verificar_1} e  {jogador_verificar_2} em {posicao_verificar_2}')
                            
                            # Diferença de mais de 2 posições tem de ser removida
                            if abs(posicao_1 - posicao_2) > 2:
    #                                 print(f'Retirar por diferença maior de 2 posições, {jogador_1}:{posicao_1} e {jogador_2}:{posicao_2}')
                                opcoes_a_remover.append(opcao_ladder)
                                continue
                                
                            
                            # Se 1 está na frente, e possui o score maior, voltar posição
                            if posicao_1 < posicao_2 and score_1 > score_2:
                                # Gerar novas possibilidades
                                # A opção padrão é sempre defesa
    #                                 print('Defesa', jogador_1)
                                
                                # Apenas adiciona situação de vitória se ganhador estiver 1 na frente
                                if posicao_1 + 1 == posicao_2:
                                    mes, ano = mes_ano_ant(mes, ano)
                                    opcao_2_diferenca = copiar_ladder_como_historico(opcao_ladder, mes, ano)
    #                                 print('Voltar 2 posições', jogador_1)
                                    opcao_2_diferenca.filter(posicao=posicao_1).update(posicao=0)
                                    opcao_2_diferenca.filter(posicao=posicao_2).update(posicao=posicao_1)
                                    opcao_2_diferenca.filter(posicao=(posicao_2 + 1)).update(posicao=(posicao_1 + 1))
                                    opcao_2_diferenca.filter(posicao=0).update(posicao=(posicao_2 + 1))
    #                                 print('Resultado:', opcao_2_diferenca)
                                    opcoes_ladder.insert(indice+1, opcao_2_diferenca)
                                    indice_prox += 1
                                
                                    mes, ano = mes_ano_ant(mes, ano)
                                    opcao_1_diferenca = copiar_ladder_como_historico(opcao_ladder, mes, ano)
    #                                     print('Voltar 1 posição', jogador_1)
                                    opcao_1_diferenca.filter(posicao=posicao_1).update(posicao=0)
                                    opcao_1_diferenca.filter(posicao=posicao_2).update(posicao=posicao_1)
                                    opcao_1_diferenca.filter(posicao=0).update(posicao=posicao_2)
    #                                     print('Resultado:', opcao_1_diferenca)
                                    opcoes_ladder.insert(indice+2, opcao_1_diferenca)
                                    indice_prox += 1
                                
    #                             print(nova_ladder.values_list('jogador__nick', 'posicao'))
                            
                            elif posicao_1 < posicao_2 and score_1 < score_2:
                                # Se jogador 1 está na frente mas perdeu, remover da lista
    #                                 print('Retirar por jogador 1 estar na frente mas ter perdido')
                                opcoes_a_remover.append(opcao_ladder)
                                continue
                                
                                
                                
                                
    #                           # Se 2 está na frente, e possui o score maior, voltar posição
                            elif posicao_2 < posicao_1 and score_2 > score_1:
                                # Gerar novas possibilidades
                                # A opção padrão é sempre defesa
    #                                 print('Defesa', jogador_2)
                                
                                # Apenas adiciona situação de vitória se ganhador estiver 1 na frente
                                if posicao_2 + 1 == posicao_1:
                                    mes, ano = mes_ano_ant(mes, ano)
                                    opcao_2_diferenca = copiar_ladder_como_historico(opcao_ladder, mes, ano)
    #                                 print('Voltar 2 posições', jogador_2)
                                    opcao_2_diferenca.filter(posicao=posicao_2).update(posicao=0)
                                    opcao_2_diferenca.filter(posicao=posicao_1).update(posicao=posicao_2)
                                    opcao_2_diferenca.filter(posicao=(posicao_1 + 1)).update(posicao=(posicao_2 + 1))
                                    opcao_2_diferenca.filter(posicao=0).update(posicao=(posicao_1 + 1))
    #                                 print('Resultado:', opcao_2_diferenca)
                                    opcoes_ladder.insert(indice+1, opcao_2_diferenca)
                                    indice_prox += 1
                                
                                    mes, ano = mes_ano_ant(mes, ano)
                                    opcao_1_diferenca = copiar_ladder_como_historico(opcao_ladder, mes, ano)
    #                                     print('Voltar 1 posição', jogador_2)
                                    opcao_1_diferenca.filter(posicao=posicao_2).update(posicao=0)
                                    opcao_1_diferenca.filter(posicao=posicao_1).update(posicao=posicao_2)
                                    opcao_1_diferenca.filter(posicao=0).update(posicao=posicao_1)
    #                                     print('Resultado:', opcao_1_diferenca)
                                    opcoes_ladder.insert(indice+2, opcao_1_diferenca)
                                    indice_prox += 1
                                
    #                             print(nova_ladder.values_list('jogador__nick', 'posicao'))
                            
                            elif posicao_2 < posicao_1 and score_2 < score_1:
                                # Se jogador 1 está na frente mas perdeu, remover da lista
    #                                 print('Retirar por jogador 2 estar na frente mas ter perdido')
                                opcoes_a_remover.append(opcao_ladder)
                                continue
    
                        # Aplicar remoções
                        print(f'Remover {len(opcoes_a_remover)} de {len(opcoes_ladder)}')
                        for remover in opcoes_a_remover:
                            remover.delete()
                            opcoes_ladder.remove(remover)
                        print(len(opcoes_ladder))
                
                if len(opcoes_ladder) == 1:
                    print(opcoes_ladder[0].values_list('jogador__nick', 'posicao'))
                
                elif len(opcoes_ladder) >= 3:
                    print(opcoes_ladder[0].values_list('jogador__nick', 'posicao'))
                    print(opcoes_ladder[1].values_list('jogador__nick', 'posicao'))
                    print(opcoes_ladder[2].values_list('jogador__nick', 'posicao'))
                    
        except:
            if score_1 == 3:
                print(f'Vitória de {jogador_1} em {posicao_1}, {jogador_2} em {posicao_2}', opcao_ladder.values_list('jogador__nick', 'posicao'))
            elif score_2 == 3:
                print(f'{jogador_1} em {posicao_1}, Vitória de {jogador_2} em {posicao_2}', opcao_ladder.values_list('jogador__nick', 'posicao'))
            raise
        
#  [('Aceblind', 2), ('Phils', 1), ('Yalda', 3), ('Mad', 6), ('Bacabau', 5), ('Teets', 7), ('Blöwer', 4), ('CPU', 13), ('Tio da Samus', 9), ('C0ox', 8), ('CDX', 12), ('Niz', 10), ('DAN.', 15), ('Sena', 16), ('TXR', 11), ('Mizuno', 17), ('PK', 20), ('Fowtha-z', 18), ('Fofão', 14), ('Rata', 19)]
        
def copiar_ladder_como_historico(ladder, mes, ano):
    for reg in ladder:
        HistoricoLadder.objects.create(posicao=reg.posicao, jogador=reg.jogador, mes=mes, ano=ano)
    
    return HistoricoLadder.objects.filter(mes=mes, ano=ano)
                