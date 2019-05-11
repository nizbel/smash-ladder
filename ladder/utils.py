# -*- coding: utf-8 -*-
"""Funções para ladder"""
import calendar
import datetime

from django.db import transaction
from django.db.models.aggregates import Sum, Max
from django.utils import timezone

from jogadores.models import Jogador
from ladder.models import DesafioLadder, HistoricoLadder, PosicaoLadder, \
    InicioLadder, LutaLadder, JogadorLuta, Luta, ResultadoDesafioLadder


def recalcular_ladder(desafio_ladder=None, mes=None, ano=None):
    informou_desafio = False
    informou_ladder_atual = False
    informou_ladder_historico = False
    
    if desafio_ladder != None and mes == None and ano == None:
        informou_desafio = True
    elif desafio_ladder == None:
        if mes == None and ano == None:
            informou_ladder_atual = True
        elif mes == None:
            raise ValueError('Informe um mês')
        elif ano == None:
            raise ValueError('Informe um ano')
        else:
            informou_ladder_historico = True
    else:
        raise ValueError('Informe apenas um desafio ou um mês/ano')
    
    try:
        with transaction.atomic():
            # Definir desafios a serem recalculados
            if informou_desafio:
                desafios = list(DesafioLadder.validados.filter(data_hora__gte=desafio_ladder.data_hora).exclude(id=desafio_ladder.id) \
                    .order_by('data_hora', 'posicao_desafiado', 'id'))
                
                # Adiciona desafio atual se não tiver sido cancelado
                if not desafio_ladder.is_cancelado():
                    desafios.append(desafio_ladder)
                desafios.sort(key=lambda x: (x.data_hora, x.posicao_desafiado, x.id))
                
                # Apagar ladders futuras e resultados para reescrever
                mes, ano = desafio_ladder.mes_ano_ladder
#                 print('MÊS/ANO', mes, ano)
                if mes != None and ano != None:
#                     HistoricoLadder.objects.filter(ano=ano, mes__gt=mes).delete()
#                     HistoricoLadder.objects.filter(ano__gt=ano).delete()
#                     PosicaoLadder.objects.all().delete()
                    
                    # Desfazer desafios para ladder do desafio
                    desafios_a_desfazer = list(DesafioLadder.validados.filter(data_hora__gte=desafio_ladder.data_hora).filter(data_hora__month=mes, 
                                                                                                                          data_hora__year=ano))
                    if desafio_ladder.is_cancelado():
                        desafios_a_desfazer.append(desafio_ladder)
                        
                    ladder_resultante = desfazer_lote_desafios(desafios_a_desfazer, 
                                                               list(HistoricoLadder.objects.filter(mes=mes, ano=ano)))
                    
                    copiar_ladder(HistoricoLadder.objects.filter(mes=mes, ano=ano).order_by('posicao'), ladder_resultante)
#                     HistoricoLadder.objects.filter(mes=mes, ano=ano).delete()
#                     for posicao_resultante in ladder_resultante:
#                         nova_posicao = HistoricoLadder(posicao=posicao_resultante.posicao, jogador = posicao_resultante.jogador, 
#                                                        mes=mes, ano=ano)
#                         nova_posicao.save()
                    
                else:
#                     for _ in PosicaoLadder.objects.all().order_by('posicao'):
#                         print(_)
                    desafios_a_desfazer = list(DesafioLadder.validados.filter(data_hora__gte=desafio_ladder.data_hora))
                    if desafio_ladder.is_cancelado():
                        desafios_a_desfazer.append(desafio_ladder)
                        
                    ladder_resultante = desfazer_lote_desafios(desafios_a_desfazer, list(PosicaoLadder.objects.all()))
                    
                    copiar_ladder(PosicaoLadder.objects.all().order_by('posicao'), ladder_resultante)
#                     PosicaoLadder.objects.all().delete()
#                     for posicao_resultante in ladder_resultante:
#                         nova_posicao = PosicaoLadder(posicao=posicao_resultante.posicao, jogador = posicao_resultante.jogador)
#                         nova_posicao.save()
                            
#                     for _ in PosicaoLadder.objects.all().order_by('posicao'):
#                         print(_)
                    
            elif informou_ladder_atual:
                data_atual = timezone.localdate()
                mes_atual = data_atual.month
                ano_atual = data_atual.year
                
                desafios = list(DesafioLadder.validados.filter(data_hora__month=mes_atual, data_hora__year=ano_atual) \
                    .order_by('data_hora', 'posicao_desafiado', 'id'))
                
#                 PosicaoLadder.objects.all().delete()
                
                # Copiar último histórico ou inicial
                if HistoricoLadder.objects.all().exists():
                    # Pegar último histórico
                    mes, ano = HistoricoLadder.objects.all().order_by('-ano', '-mes').values_list('mes', 'ano')[0]
                    copiar_ladder(PosicaoLadder.objects.all().order_by('posicao'), 
                                  HistoricoLadder.objects.filter(ano=ano, mes=mes).order_by('posicao'))
#                     for posicao_ladder in HistoricoLadder.objects.filter(ano=ano, mes=mes).order_by('posicao'):
#                         posicao_atual = PosicaoLadder(posicao=posicao_ladder.posicao, jogador=posicao_ladder.jogador)
#                         posicao_atual.save()
                else:
                    copiar_ladder(PosicaoLadder.objects.all().order_by('posicao'), 
                                  InicioLadder.objects.all().order_by('posicao'))
#                     for posicao_ladder in InicioLadder.objects.all().order_by('posicao'):
#                         posicao_atual = PosicaoLadder(posicao=posicao_ladder.posicao, jogador=posicao_ladder.jogador)
#                         posicao_atual.save()
                
                mes = None
                ano = None
                
            elif informou_ladder_historico:
                data = timezone.make_aware(timezone.datetime(ano, mes, 1))
                desafios = list(DesafioLadder.validados.filter(data_hora__gte=data) \
                    .order_by('data_hora', 'posicao_desafiado', 'id'))
                
#                 HistoricoLadder.objects.filter(ano=ano, mes__gte=mes).delete()
#                 HistoricoLadder.objects.filter(ano__gt=ano).delete()
#                 PosicaoLadder.objects.all().delete()
                
                # Copiar último histórico ou inicial
                mes_anterior = mes - 1
                if mes_anterior == 0:
                    mes_anterior = 12
                    ano_anterior = ano - 1
                else:
                    ano_anterior = ano
                    
                if HistoricoLadder.objects.filter(mes=mes_anterior, ano=ano_anterior).exists():
                    # Pegar último histórico
                    for posicao_ladder in HistoricoLadder.objects.filter(mes=mes_anterior, ano=ano_anterior).order_by('posicao'):
                        posicao_atual = HistoricoLadder(posicao=posicao_ladder.posicao, jogador=posicao_ladder.jogador, 
                                                        mes=mes, ano=ano)
                        posicao_atual.save()
                else:
                    for posicao_ladder in InicioLadder.objects.all().order_by('posicao'):
                        posicao_atual = HistoricoLadder(posicao=posicao_ladder.posicao, jogador=posicao_ladder.jogador, 
                                                        mes=mes, ano=ano)
                        posicao_atual.save()
            
#             ResultadoDesafioLadder.objects.filter(desafio_ladder__in=desafios).delete()
            
            mes_atual = mes
            ano_atual = ano
            
#             print(desafios)
            
            # Reescrever
            for desafio in desafios:
                # Verificar se alterou mês/ano para próximo desafio
                mes, ano = desafio.mes_ano_ladder
                if mes != mes_atual or ano != ano_atual:
                    # Alterou mês/ano na última iteração
                    
                    # Já chegou a data atual?
                    if mes == None and ano == None:
                        data_atual = timezone.localdate()
                        # Se sim, alterar ano_atual e mes_atual até poder utilizar PosicaoLadder
                        while mes_atual != data_atual.month or ano_atual != data_atual.year:
                            # Incrementar data
                            prox_mes = mes_atual + 1
                            if prox_mes == 13:
                                prox_ano = ano_atual + 1
                                prox_mes = 1
                            else:
                                prox_ano = ano_atual
                                
                            if prox_mes == data_atual.month and prox_ano == data_atual.year:
                                # Gerar ladder atual
                                copiar_ladder(PosicaoLadder.objects.all().order_by('posicao'), 
                                              HistoricoLadder.objects.filter(mes=mes_atual, ano=ano_atual).order_by('posicao'))
#                                 for historico in HistoricoLadder.objects.filter(mes=mes_atual, ano=ano_atual).order_by('posicao'):
#                                     posicao_ladder = PosicaoLadder(posicao=historico.posicao, 
#                                                                      jogador=historico.jogador)
#                                     posicao_ladder.save()
                            else:
                                # Gerar histórico de ladder
                                copiar_ladder(HistoricoLadder.objects.filter(mes=prox_mes, ano=prox_ano).order_by('posicao'), 
                                              HistoricoLadder.objects.filter(mes=mes_atual, ano=ano_atual).order_by('posicao'))
#                                 for historico in HistoricoLadder.objects.filter(mes=mes_atual, ano=ano_atual).order_by('posicao'):
#                                     novo_historico = HistoricoLadder(mes=prox_mes, ano=prox_ano, posicao=historico.posicao, 
#                                                                      jogador=historico.jogador)
#                                     novo_historico.save()
                                
                            mes_atual = prox_mes
                            ano_atual = prox_ano
                                
                            
                    else:
                        # Se não, alterar até mes, ano
                        while mes_atual != mes or ano_atual != ano:
                            # Incrementar data
                            prox_mes = mes_atual
                            prox_ano = ano_atual
                            prox_mes += 1
                            if prox_mes == 13:
                                prox_ano += 1
                                prox_mes = 1
                            
                            # Gerar histórico de ladder
                            copiar_ladder(HistoricoLadder.objects.filter(mes=prox_mes, ano=prox_ano).order_by('posicao'),
                                          HistoricoLadder.objects.filter(mes=mes_atual, ano=ano_atual).order_by('posicao'))
#                             for historico in HistoricoLadder.objects.filter(mes=mes_atual, ano=ano_atual).order_by('posicao'):
#                                 novo_historico = HistoricoLadder(mes=prox_mes, ano=prox_ano, posicao=historico.posicao, 
#                                                                  jogador=historico.jogador)
#                                 novo_historico.save()
                                
                            mes_atual = prox_mes
                            ano_atual = prox_ano
                    
                    # Atualizar mes e ano atual para iterações
                    mes_atual = mes
                    ano_atual = ano
                    
                # Verificar posições
                if mes == None and ano == None:
                    ladder = PosicaoLadder.objects.all()
                else:
                    ladder = HistoricoLadder.objects.filter(mes=mes, ano=ano)
                verificar_posicoes_desafiante_desafiado(desafio, list(ladder))
                
                alterar_ladder(desafio, False)
                
            # Se tiver chegado a data atual, retornar
            if mes_atual == None and ano_atual == None:
                return
            
            # Copiar ladder até posição atual
            while mes_atual != timezone.localdate().month and ano_atual != timezone.localdate().year:
                # Incrementar data
                prox_mes = mes_atual
                prox_ano = ano_atual
                prox_mes += 1
                if prox_mes == 13:
                    prox_ano += 1
                    prox_mes = 1
                    
                if prox_mes == timezone.localdate().month and prox_ano == timezone.localdate().year:
                    # Gerar ladder atual
                    copiar_ladder(PosicaoLadder.objects.all().order_by('posicao'), 
                                  HistoricoLadder.objects.filter(mes=mes_atual, ano=ano_atual).order_by('posicao'))
#                     for historico in HistoricoLadder.objects.filter(mes=mes_atual, ano=ano_atual).order_by('posicao'):
#                         posicao_ladder = PosicaoLadder(posicao=historico.posicao, 
#                                                          jogador=historico.jogador)
#                         posicao_ladder.save()
                else:
                    # Gerar histórico de ladder
                    copiar_ladder(HistoricoLadder.objects.filter(mes=prox_mes, ano=prox_ano).order_by('posicao'), 
                                  HistoricoLadder.objects.filter(mes=mes_atual, ano=ano_atual).order_by('posicao'))
#                     for historico in HistoricoLadder.objects.filter(mes=mes_atual, ano=ano_atual).order_by('posicao'):
#                         novo_historico = HistoricoLadder(mes=prox_mes, ano=prox_ano, posicao=historico.posicao, 
#                                                          jogador=historico.jogador)
#                         novo_historico.save()
                    
                mes_atual = prox_mes
                ano_atual = prox_ano
            
    except Exception as e:
        if desafio:
            raise ValueError(f'Desafio Ladder {desafio.id}: {e}')
        else:
            raise

def alterar_ladder(desafio_ladder, verificar_posteriores=True):
    """Altera posições da ladder com base em um desafio de ladder"""
#     print(desafio_ladder.data_hora)
    # Verifica se há desafios validados posteriores, se sim, recalcular ladder
    if verificar_posteriores:
        if DesafioLadder.validados.filter(data_hora__gte=desafio_ladder.data_hora).exclude(id=desafio_ladder.id).exists():
            recalcular_ladder(desafio_ladder)
            return
    
    desafiante = desafio_ladder.desafiante
    desafiado = desafio_ladder.desafiado
    
    # Remover resultados para recalculá-los
    ResultadoDesafioLadder.objects.filter(desafio_ladder=desafio_ladder).delete()
    
    # Se desafiante venceu
    if desafio_ladder.desafiante_venceu():
        # Definir se deve alterar histórico
        if desafio_ladder.is_historico():
            mes, ano = desafio_ladder.mes_ano_ladder
            ladder_para_alterar = HistoricoLadder.objects.filter(ano=ano, mes=mes)
        else:
            ladder_para_alterar = PosicaoLadder.objects
            
        
        # Verificar posição do desafiado
        # TODO alterar forma de buscar posição
#         desafiado_esta_na_ladder = True
        posicao_desafiado = desafiado.posicao_em(desafio_ladder.data_hora)
#         print('Posição desafiado', posicao_desafiado)
        if posicao_desafiado == 0:
            posicao_desafiado = gerar_posicao_novo_entrante(desafio_ladder, desafiado)
            
            # Criar posição desafiado
            if desafio_ladder.is_historico():
                novo_entrante = HistoricoLadder(posicao=posicao_desafiado, jogador=desafiado, mes=mes, ano=ano)
            else:
                novo_entrante = PosicaoLadder(posicao=posicao_desafiado, jogador=desafiado)
            novo_entrante.save()
            
#         if ladder_para_alterar.filter(jogador=desafiado).exists():
#             posicao_desafiado = ladder_para_alterar.get(jogador=desafiado).posicao
#         else:
#             # Se não está na ladder, posição do desafiado é atrás do último
#             posicao_desafiado = ladder_para_alterar.all().order_by('-posicao')[0].posicao + 1
# #             desafiado_esta_na_ladder = False
#             
#             # Criar posição desafiado
#             if desafio_ladder.is_historico():
#                 novo_entrante = HistoricoLadder(posicao=posicao_desafiado, jogador=desafiado, mes=mes, ano=ano)
#             else:
#                 novo_entrante = PosicaoLadder(posicao=posicao_desafiado, jogador=desafiado)
#             novo_entrante.save()
        
        # Verificar posição do desafiante
        posicao_desafiante = desafiante.posicao_em(desafio_ladder.data_hora)
#         print('Posição desafiante vitoria', posicao_desafiante)
        if posicao_desafiante == 0:
            posicao_desafiante = gerar_posicao_novo_entrante(desafio_ladder, desafiante)
            # Criar posição desafiante
            if desafio_ladder.is_historico():
                novo_entrante = HistoricoLadder(posicao=posicao_desafiante, jogador=desafiante, mes=mes, ano=ano)
            else:
                novo_entrante = PosicaoLadder(posicao=posicao_desafiante, jogador=desafiante)
            novo_entrante.save()
        
#         if ladder_para_alterar.filter(jogador=desafiante).exists():
#             posicao_desafiante = ladder_para_alterar.get(jogador=desafiante).posicao
#         else:
#             # Se não está na ladder, posição do desafiante é atrás do desafiado
# #             if desafiado_esta_na_ladder:
#             posicao_desafiante = ladder_para_alterar.all().order_by('-posicao')[0].posicao + 1
# #             else:
# #                 posicao_desafiante = ladder_para_alterar.all().order_by('-posicao')[0].posicao + 2
#                 
#             # Criar posição desafiante
#             if desafio_ladder.is_historico():
#                 novo_entrante = HistoricoLadder(posicao=posicao_desafiante, jogador=desafiante, mes=mes, ano=ano)
#             else:
#                 novo_entrante = PosicaoLadder(posicao=posicao_desafiante, jogador=desafiante)
#             novo_entrante.save()
        
#         # Verificar se desafiante já estava na ladder
#         if ladder_para_alterar.filter(jogador=desafiante).exists():
#             posicao_desafiante = ladder_para_alterar.get(jogador=desafiante).posicao
#         else:
#             posicao_desafiante = ladder_para_alterar.all().order_by('-posicao')[0].posicao + 1
#             
#             # Criar posição desafiante
#             if desafio_ladder.is_historico():
#                 novo_entrante = HistoricoLadder(posicao=posicao_desafiante, jogador=desafiante, mes=mes, ano=ano)
#             else:
#                 novo_entrante = PosicaoLadder(posicao=posicao_desafiante, jogador=desafiante)
#             novo_entrante.save()
#             
#         posicao_desafiado = ladder_para_alterar.get(jogador=desafiado).posicao
        
        posicoes_entre_jogadores = list(ladder_para_alterar.filter(posicao__lte=posicao_desafiante, 
                                                                posicao__gte=posicao_desafiado).order_by('-posicao'))
        
        # Retira desafiante da ladder momentaneamente
        posicoes_entre_jogadores[0].posicao = 0
        posicoes_entre_jogadores[0].save()
        
        # Retira uma posição de cada jogador à frente 
        for posicao_jogador in posicoes_entre_jogadores[1:]:
            posicao_jogador.posicao += 1
            posicao_jogador.save()
            
            # Adiciona aos resultados do desafio
            resultado_jogador = ResultadoDesafioLadder(desafio_ladder=desafio_ladder, jogador=posicao_jogador.jogador, alteracao_posicao=1)
            resultado_jogador.save()
        
        # Coloca desafiante uma posição à frente do desafiado (final da lista)
        posicoes_entre_jogadores[0].posicao = posicoes_entre_jogadores[-1].posicao - 1
        posicoes_entre_jogadores[0].save()
        
        # Adiciona resultado para desafiante
        resultado_desafiante = ResultadoDesafioLadder(desafio_ladder=desafio_ladder, jogador=desafiante, 
                                                      alteracao_posicao=posicoes_entre_jogadores[0].posicao - posicao_desafiante)
        resultado_desafiante.save()
        
    else:
        # Desafiante perdeu, caso seja novo entrante, adicionar a ladder
        # Definir se deve alterar histórico
        if desafio_ladder.is_historico():
            mes, ano = desafio_ladder.mes_ano_ladder
            ladder_para_alterar = HistoricoLadder.objects.filter(ano=ano, mes=mes)
        else:
            ladder_para_alterar = PosicaoLadder.objects
        
        # Pegar posições de jogadores
#         desafiado_esta_na_ladder = True
        posicao_desafiado = desafiado.posicao_em(desafio_ladder.data_hora)
#         print('Posição desafiado', posicao_desafiado)
        if posicao_desafiado == 0:
            posicao_desafiado = gerar_posicao_novo_entrante(desafio_ladder, desafiado)
            # Criar posição desafiado
            if desafio_ladder.is_historico():
                novo_entrante = HistoricoLadder(posicao=posicao_desafiado, jogador=desafiado, mes=mes, ano=ano)
            else:
                novo_entrante = PosicaoLadder(posicao=posicao_desafiado, jogador=desafiado)
            novo_entrante.save()
        
#         if ladder_para_alterar.filter(jogador=desafiado).exists():
#             posicao_desafiado = ladder_para_alterar.get(jogador=desafiado).posicao
#         else:
#             # Se não está na ladder, posição do desafiado é atrás do último
#             posicao_desafiado = ladder_para_alterar.all().order_by('-posicao')[0].posicao + 1
# #             desafiado_esta_na_ladder = False
#             
#             # Criar posição desafiado
#             if desafio_ladder.is_historico():
#                 novo_entrante = HistoricoLadder(posicao=posicao_desafiado, jogador=desafiado, mes=mes, ano=ano)
#             else:
#                 novo_entrante = PosicaoLadder(posicao=posicao_desafiado, jogador=desafiado)
#             novo_entrante.save()
            
        posicao_desafiante = desafiante.posicao_em(desafio_ladder.data_hora)
#         print('Posição desafiante derrota', posicao_desafiante)
        if posicao_desafiante == 0:
            posicao_desafiante = gerar_posicao_novo_entrante(desafio_ladder, desafiante)
            # Criar posição desafiante
            if desafio_ladder.is_historico():
                novo_entrante = HistoricoLadder(posicao=posicao_desafiante, jogador=desafiante, mes=mes, ano=ano)
            else:
                novo_entrante = PosicaoLadder(posicao=posicao_desafiante, jogador=desafiante)
            novo_entrante.save()

#         if ladder_para_alterar.filter(jogador=desafiante).exists():
#             posicao_desafiante = ladder_para_alterar.get(jogador=desafiante).posicao
#         else:
# #             if desafiado_esta_na_ladder:
#             posicao_desafiante = ladder_para_alterar.all().order_by('-posicao')[0].posicao + 1
# #             else:
# #                 posicao_desafiante = ladder_para_alterar.all().order_by('-posicao')[0].posicao + 2
#             
#             # Criar posição desafiante
#             if desafio_ladder.is_historico():
#                 novo_entrante = HistoricoLadder(posicao=posicao_desafiante, jogador=desafiante, mes=mes, ano=ano)
#             else:
#                 novo_entrante = PosicaoLadder(posicao=posicao_desafiante, jogador=desafiante)
#             novo_entrante.save()
        
    # Salvar posições de desafiante e desafiado, pré-desafio
    desafio_ladder.posicao_desafiante = posicao_desafiante
    desafio_ladder.posicao_desafiado = posicao_desafiado
    desafio_ladder.save()
            
def recalcular_ladder_old(mes=None, ano=None):
    """Recalcula todas as posições de uma ladder"""
    # Se mês e ano não foram preenchidos, ladder é a atual
    if mes == None and ano == None:
        ladder = PosicaoLadder.objects
        
        # Guarda se estamos alterando ladder atual
        is_ladder_atual = True
        
        # Verificar histórico mês anterior
        data_atual = timezone.localdate()
        ano_historico_mes_anterior = data_atual.year
        mes_historico_mes_anterior = data_atual.month - 1
        if mes_historico_mes_anterior == 0:
            mes_historico_mes_anterior = 12
            ano_historico_mes_anterior -= 1
            
        if HistoricoLadder.objects.filter(ano=ano_historico_mes_anterior, mes=mes_historico_mes_anterior).exists():
            historico_mes_anterior = HistoricoLadder.objects.filter(ano=ano_historico_mes_anterior, 
                                                                    mes=mes_historico_mes_anterior).order_by('posicao')
        else:
            historico_mes_anterior = None
            
        # Guardar mês e ano atuais
        mes = data_atual.month
        ano = data_atual.year
            
    elif mes == None:
        raise ValueError('Informe um mês')
    elif ano == None:
        raise ValueError('Informe um ano')
    else:
        # Pegar ladder histórica para mês/ano, caso não exista a ladder em si, verificar se existem desafios válidos
        #até o final do ano/mês apontado
        data_limite_desafio_ladder = datetime.date(ano, mes, calendar.monthrange(ano, mes)[1]) + datetime.timedelta(days=1)
        
        if HistoricoLadder.objects.filter(ano=ano, mes=mes).exists() or DesafioLadder.objects.filter(
                cancelamentodesafioladder__isnull=True, admin_validador__isnull=False, data_hora__date__lt=data_limite_desafio_ladder).exists():
            ladder = HistoricoLadder.objects.filter(ano=ano, mes=mes)
        else:
            raise ValueError(HistoricoLadder.MENSAGEM_LADDER_MES_ANO_INEXISTENTE)
        
        # Guarda se estamos alterando histórico
        is_ladder_atual = False
        
        # Verificar histórico mês anterior
        ano_historico_mes_anterior = ano
        mes_historico_mes_anterior = mes - 1
        if mes_historico_mes_anterior == 0:
            mes_historico_mes_anterior = 12
            ano_historico_mes_anterior -= 1
        
        if HistoricoLadder.objects.filter(ano=ano_historico_mes_anterior, mes=mes_historico_mes_anterior).exists():
            historico_mes_anterior = HistoricoLadder.objects.filter(ano=ano_historico_mes_anterior, 
                                                                    mes=mes_historico_mes_anterior).order_by('posicao')
        else:
            historico_mes_anterior = None
    
    # Se existe histórico de mês anterior, buscar dele
    if historico_mes_anterior:
        try:
            with transaction.atomic():
                # Remover posições da ladder
                ladder.all().delete()
                # Remover resultados de desafios
                ResultadoDesafioLadder.objects.all().delete()
                
                # Preencher com dados do histórico
                for posicao_historico in historico_mes_anterior:
                    if is_ladder_atual:
                        nova_posicao = PosicaoLadder(jogador=posicao_historico.jogador, posicao=posicao_historico.posicao)
                        nova_posicao.save()
                    else:
                        nova_posicao = HistoricoLadder(jogador=posicao_historico.jogador, posicao=posicao_historico.posicao, ano=ano, mes=mes)
                        nova_posicao.save()
                    
                # Recalcular com desafios do mês validados e não cancelados
                try:
                    for desafio_ladder in DesafioLadder.objects.filter(cancelamentodesafioladder__isnull=True, 
                                                                         admin_validador__isnull=False, data_hora__month=mes, 
                                                                         data_hora__year=ano).order_by('data_hora'):
                        # Verificar posições
                        verificar_posicoes_desafiante_desafiado(desafio_ladder)
#                         # Validar uso coringa
#                         if desafio_ladder.desafio_coringa:
#                             # Verificar se desafiante pode utilizar desafio coringa
#                             if not desafio_ladder.desafiante.pode_usar_coringa_na_data(desafio_ladder.data_hora.date()):
#                                 raise ValueError(DesafioLadder.MENSAGEM_ERRO_PERIODO_ESPERA_CORINGA)
                            
                        alterar_ladder(desafio_ladder)
                except Exception as e:
                    raise ValueError(f'Desafio Ladder {desafio_ladder.id}: {e}')
        except:
            raise
        
    else:
        # Se não, buscar de ladder inicial
        try:
            with transaction.atomic():
                # Remover posições da ladder
                ladder.all().delete()
                # Remover resultados de desafios
                ResultadoDesafioLadder.objects.all().delete()
                
                # Preencher com dados do histórico
                for posicao_historico in InicioLadder.objects.all().order_by('posicao'):
                    if is_ladder_atual:
                        nova_posicao = PosicaoLadder(jogador=posicao_historico.jogador, posicao=posicao_historico.posicao)
                        nova_posicao.save()
                    else:
                        nova_posicao = HistoricoLadder(jogador=posicao_historico.jogador, posicao=posicao_historico.posicao, ano=ano, mes=mes)
                        nova_posicao.save()
                    
                # Recalcular com desafios do mês validados e não cancelados
                try:
                    for desafio_ladder in DesafioLadder.objects.filter(cancelamentodesafioladder__isnull=True, 
                                                                         admin_validador__isnull=False, data_hora__month=mes, 
                                                                         data_hora__year=ano).order_by('data_hora'):
                        alterar_ladder(desafio_ladder)
                except Exception as e:
                    raise ValueError(f'Desafio Ladder {desafio_ladder.id}: {e}')
        except:
            raise
        
    
            
# def verificar_posicoes_desafiante_desafiado(ladder, desafiante, desafiado, data_hora, desafio_coringa):
def verificar_posicoes_desafiante_desafiado(desafio_ladder, ladder=None):
#     print(desafio_ladder.data_hora)
    """Verifica se desafiante está abaixo e com a distância correta de desafiado na ladder"""
    desafiante = desafio_ladder.desafiante
    desafiado = desafio_ladder.desafiado
    
    # Verifica se desafiante e desafiado não estão de férias na data
    if desafiante.de_ferias_na_data(desafio_ladder.data_hora.date()):
        raise ValueError(DesafioLadder.MENSAGEM_ERRO_DESAFIANTE_FERIAS)
    
    if desafiado.de_ferias_na_data(desafio_ladder.data_hora.date()):
        raise ValueError(DesafioLadder.MENSAGEM_ERRO_DESAFIADO_FERIAS)
    
    # Jogador não pode desafiar a si mesmo
    if desafiante == desafiado:
        raise ValueError(DesafioLadder.MENSAGEM_ERRO_MESMO_JOGADOR)
    
    # Verificar posição do desafiado
    desafiado_esta_na_ladder = True
    posicao_desafiado = desafiado.posicao_em(desafio_ladder.data_hora)
#     print('desafiado inicial', posicao_desafiado)
    if posicao_desafiado == 0:
        desafiado_esta_na_ladder = False
        posicao_desafiado = gerar_posicao_novo_entrante(desafio_ladder, desafiado)
#     print('desafiado final', posicao_desafiado)
#     desafiado_esta_na_ladder = True
#     if ladder.filter(jogador=desafiado).exists():
#         posicao_desafiado = ladder.get(jogador=desafiado).posicao
#     else:
#         # Se não está na ladder, posição do desafiado é atrás do último
#         posicao_desafiado = ladder.all().order_by('-posicao')[0].posicao + 1
#         desafiado_esta_na_ladder = False
    
    # Verificar posição do desafiante
    posicao_desafiante = desafiante.posicao_em(desafio_ladder.data_hora)
#     print('desafiante inicial', posicao_desafiante)
    if posicao_desafiante == 0:
        desafiado_esta_na_ladder = False
        posicao_desafiante = gerar_posicao_novo_entrante(desafio_ladder, desafiante)
#     print('desafiante final', posicao_desafiante)
#     if ladder.filter(jogador=desafiante).exists():
#         posicao_desafiante = ladder.get(jogador=desafiante).posicao
#     else:
#         # Se não está na ladder, posição do desafiante é atrás do desafiado
#         if desafiado_esta_na_ladder:
#             posicao_desafiante = ladder.all().order_by('-posicao')[0].posicao + 1
#         else:
#             posicao_desafiante = ladder.all().order_by('-posicao')[0].posicao + 2
    
    if posicao_desafiante < posicao_desafiado:
        raise ValueError(DesafioLadder.MENSAGEM_ERRO_DESAFIANTE_ACIMA_DESAFIADO)
    elif not desafio_ladder.desafio_coringa:
        # Verificar se desafiado está na ladder
        if desafiado_esta_na_ladder:
            
            # Se ladder não foi informada, buscar desfazendo desafios futuros
            if ladder == None:
                # Verificar situação da ladder na data/hora
                mes, ano = desafio_ladder.mes_ano_ladder
                # Desfazer desafios para ladder do desafio
                if mes != None and ano != None:
                    ladder = desfazer_lote_desafios(list(DesafioLadder.validados.filter(data_hora__gte=desafio_ladder.data_hora) \
                                                                    .filter(data_hora__month=mes, data_hora__year=ano)), 
                                                               list(HistoricoLadder.objects.filter(mes=mes, ano=ano)))
                        
                else:
                    ladder = desfazer_lote_desafios(list(DesafioLadder.validados.filter(data_hora__gte=desafio_ladder.data_hora)), 
                                                                     list(PosicaoLadder.objects.all()))
            
            # Verificar quais jogadores são desafiáveis devido a possibilidade de férias
            desafiaveis = list()
            ladder.sort(key=lambda x: x.posicao, reverse=True)
            for jogador_posicao in [ladder_posicao for ladder_posicao in ladder if ladder_posicao.posicao < posicao_desafiante]:
                if not jogador_posicao.jogador.de_ferias_na_data(desafio_ladder.data_hora.date()):
                    desafiaveis.append(jogador_posicao.jogador)
                    
                    # Verifica se quantidade de desafiáveis já supre o limite de posições acima
                    if len(desafiaveis) == DesafioLadder.LIMITE_POSICOES_DESAFIO:
                        break
            
            # Desafiado é desafiável?
            if desafiado not in desafiaveis:
                raise ValueError(DesafioLadder.MENSAGEM_ERRO_DESAFIANTE_MUITO_ABAIXO_DESAFIADO)
        
def validar_e_salvar_lutas_ladder(desafio_ladder, formset_lutas):
    """Valida lutas em um formset para adicioná-las a desafio de ladder"""
    # Verificar se ganhadores apontados batem com resultado do desafio da ladder
    vitorias_desafiante = 0
    vitorias_desafiado = 0
    
    total_lutas = desafio_ladder.score_desafiante + desafio_ladder.score_desafiado 
    
    # Guarda ids das lutas válidas para desafio ladder
    lutas_validas_desafio_ladder = list()
    
    # Para cada form válido, criar Luta, LutaLadder com indice crescente
    for indice_luta, form_luta in enumerate(formset_lutas[:total_lutas], start=1):
        # Testa se todos os valores são nulos (não preenchidos) e form não possuia id, exceto o campo DELETE
        if (all([value == None for key, value in form_luta.cleaned_data.items() if key != 'DELETE'])) and \
                'id' not in form_luta.initial:
            # Se sim, desconsiderar form
            continue
        
        # Verificar se luta foi marcada para ser apagada
        if form_luta.cleaned_data.get('DELETE', False) and form_luta.instance.id:
            form_luta.instance.delete()
            continue
        
#         # Adicionar 1 a índice da luta pois começa em 0
#         indice_luta += 1
        
        luta = form_luta.save(commit=False)
         
        # Verificar se ganhador está na luta
        if luta.ganhador not in [desafio_ladder.desafiante, desafio_ladder.desafiado]:
            raise ValueError(f'Luta {indice_luta} indica ganhador que não está entre os participantes')
        
        elif luta.ganhador == desafio_ladder.desafiante:
            vitorias_desafiante += 1
        elif luta.ganhador == desafio_ladder.desafiado:
            vitorias_desafiado += 1
             
        # Se número de vitórias for incompatível
        if vitorias_desafiante > desafio_ladder.score_desafiante or \
                vitorias_desafiado > desafio_ladder.score_desafiado:
            raise ValueError('Resultado geral informado é incompatível com resultados das lutas')
         
        # Preencher campos de luta pelo desafio de ladder
        luta.adicionada_por = desafio_ladder.adicionado_por
        luta.data = desafio_ladder.data_hora.date()
        luta.save()
         
        # Guardar id da luta como válida
        lutas_validas_desafio_ladder.append(luta.id)
        
        # Relacionar a desafio de ladder se não for alteração
        if not LutaLadder.objects.filter(desafio_ladder=desafio_ladder, luta=luta).exists():
            luta_ladder = LutaLadder(desafio_ladder=desafio_ladder, luta=luta, indice_desafio_ladder=indice_luta)
            luta_ladder.save()
         
        # Adicionar jogadores a luta, se não for alteração
        jogadores_luta = JogadorLuta.objects.filter(luta=luta).order_by('id')
        
        # Preencher desafiante
        if jogadores_luta.count() >= 1: # Desafiante é sempre o primeiro a ser inserido
            
            # Verificar se houve alteração
            jogador_desafiante_luta = jogadores_luta[0]
            if jogador_desafiante_luta.jogador != desafio_ladder.desafiante \
                    or jogador_desafiante_luta.personagem != form_luta.cleaned_data['personagem_desafiante']:
                jogador_desafiante_luta.jogador = desafio_ladder.desafiante
                jogador_desafiante_luta.personagem = form_luta.cleaned_data['personagem_desafiante']
                jogador_desafiante_luta.save(update_fields=['jogador', 'personagem'])
        else:
            jogador_desafiante_luta = JogadorLuta(jogador=desafio_ladder.desafiante, luta=luta,
                                                  personagem=form_luta.cleaned_data['personagem_desafiante'])
            jogador_desafiante_luta.save()
             
        # Preencher desafiado
        if jogadores_luta.count() >= 2: # Desafiado é sempre o segundo a ser inserido
            
            # Verificar se houve alteração
            jogador_desafiado_luta = jogadores_luta[1]
            if jogador_desafiado_luta.jogador != desafio_ladder.desafiado \
                    or jogador_desafiado_luta.personagem != form_luta.cleaned_data['personagem_desafiado']:
                jogador_desafiado_luta.jogador = desafio_ladder.desafiado
                jogador_desafiado_luta.personagem = form_luta.cleaned_data['personagem_desafiado']
                jogador_desafiado_luta.save(update_fields=['jogador', 'personagem'])
        else:
            jogador_desafiado_luta = JogadorLuta(jogador=desafio_ladder.desafiado, luta=luta,
                                                 personagem=form_luta.cleaned_data['personagem_desafiado'])
            jogador_desafiado_luta.save()
    
    # Apagar lutas que não são mais válidas para desafio ladder
    Luta.objects.filter(lutaladder__desafio_ladder=desafio_ladder).exclude(id__in=lutas_validas_desafio_ladder).delete()
    
def desfazer_desafio(desafio_ladder, ladder):
    """Retorna posições da ladder anteriores ao resultado de um desafio"""
    resultados = desafio_ladder.resultadodesafioladder_set.all()
    
    jogadores_ladder = [posicao_ladder.jogador_id for posicao_ladder in ladder]
    
    # Verificar se todos os jogadores presentes no resultado estão indicados na ladder
    for jogador in resultados.values_list('jogador', flat=True):
        if jogador not in jogadores_ladder:
            raise ValueError(f'Resultados do desafio não condizem com a ladder especificada {jogador}')
    
    # Alterar ladder
    for resultado in resultados:
        # Procurar jogador
        for posicao_ladder in ladder:
            if posicao_ladder.jogador == resultado.jogador:
                # Alterar posição
                posicao_ladder.posicao -= resultado.alteracao_posicao
                break
                
    # Ordenar ladder após alterações
    ladder.sort(key=lambda x: x.posicao)
    
    return ladder

def desfazer_lote_desafios(desafios, ladder):
    """Retorna posições da ladder anteriores ao resultado de um desafio"""
    # Se desafios está vazio, retornar ladder
    if len(desafios) == 0:
        return ladder
    
    resultados = dict(ResultadoDesafioLadder.objects.filter(desafio_ladder__in=desafios).order_by('jogador').values('jogador') \
                                      .annotate(alteracao_total=Sum('alteracao_posicao')).values_list('jogador', 'alteracao_total'))
    
    jogadores_ladder = [posicao_ladder.jogador_id for posicao_ladder in ladder]
    
    # Verificar se todos os jogadores presentes no resultado estão indicados na ladder
    for jogador in resultados:
        if jogador not in jogadores_ladder:
            raise ValueError(f'Resultados do desafio não condizem com a ladder especificada')
    
    # Alterar ladder
    for jogador, alteracao in resultados.items():
        # Procurar jogador
        for posicao_ladder in ladder:
            if posicao_ladder.jogador_id == jogador:
                # Alterar posição
                posicao_ladder.posicao -= alteracao
                break
                
    # Ordenar ladder após alterações
    ladder.sort(key=lambda x: x.posicao)
#     print(ladder)
    
    # Verificar quais jogadores já existiam na ladder
    desafio_mais_antigo = sorted(desafios, key=lambda x: x.data_hora)[0]
    novos_entrantes = list()
    for posicao_ladder in reversed(ladder):
        if Jogador.objects.get(id=posicao_ladder.jogador_id).posicao_em(desafio_mais_antigo.data_hora) == 0:
            novos_entrantes.append(posicao_ladder)
    
#     print(novos_entrantes)
    for posicao in novos_entrantes:
        ladder.remove(posicao)
    
#     print(ladder)
    
    return ladder


def gerar_posicao_novo_entrante(desafio_ladder, jogador):
    """Retorna posição de novo entrante na data/hora do desafio definido"""
    desafios_validos = list(DesafioLadder.validados.filter(data_hora=desafio_ladder.data_hora).exclude(id=desafio_ladder.id).order_by('id'))
    
    # Adicionar desafio especificado
    desafios_validos.append(desafio_ladder)
    # Ordenar
    desafios_validos.sort(key=lambda x: (x.posicao_desafiado, x.posicao_desafiante))
    
    # Definir ultima ladder
    mes = desafio_ladder.data_hora.month
    ano = desafio_ladder.data_hora.year
    mes -= 1
    if mes == 0:
        mes = 12
        ano -= 1
    if HistoricoLadder.objects.filter(ano=ano, mes=mes).exists():
        ultima_ladder = HistoricoLadder.objects.filter(ano=ano, mes=mes)
    else:
        ultima_ladder = InicioLadder.objects.all()    
    
    # Buscar última posição disponível na data
    ultima_posicao_disponivel = max(DesafioLadder.validados.filter(data_hora__lt=desafio_ladder.data_hora) \
        .aggregate(ultima_posicao=Max('posicao_desafiante'))['ultima_posicao'] or 0, 
        ultima_ladder.aggregate(ultima_posicao=Max('posicao'))['ultima_posicao'] or 0) + 1
    
    # Percorrer todos os desafios na data/hora, ordenados por inserção, incrementando posições para novos entrantes
    for desafio in desafios_validos:
        if desafio.desafiado == jogador:
            return ultima_posicao_disponivel
        if desafio.desafiado.posicao_em(desafio_ladder.data_hora) == 0:
            ultima_posicao_disponivel += 1
            
        if desafio.desafiante == jogador:
            return ultima_posicao_disponivel
        if desafio.desafiante.posicao_em(desafio_ladder.data_hora) == 0:
            ultima_posicao_disponivel += 1
            
def copiar_ladder(ladder_destino, ladder_origem, mes_destino=None, ano_destino=None):
    """Copia as posições de ladder de origem para ladder de destino"""
    # Verifica se ladders não estão vazias
#     if len(ladder_destino) == 0:
#         raise ValueError('Ladder de destino não pode estar vazia')
    if len(ladder_origem) == 0:
        raise ValueError('Ladder de origem não pode estar vazia')
    
    # Deixa as posições negativas para que não atrapalhem ao copiar
    for posicao_dest in ladder_destino:
        posicao_dest.posicao = -posicao_dest.posicao
        posicao_dest.save()
        
    # Copia posições
    for posicao_orig in ladder_origem:
        # Buscar jogador na ladder original
        for posicao_dest in ladder_destino:
            if posicao_orig.jogador_id == posicao_dest.jogador_id:
                posicao_dest.posicao = posicao_orig.posicao
                posicao_dest.save()
                break
        else:
            if ladder_destino.model is PosicaoLadder:
                posicao_dest = PosicaoLadder(jogador=posicao_orig.jogador, posicao=posicao_orig.posicao)
                posicao_dest.save()
            elif ladder_destino.model is HistoricoLadder:
                try:
                    mes = ladder_destino[0].mes
                    ano = ladder_destino[0].ano
                except:
                    if ano_destino != None and mes_destino != None:
                        mes = mes_destino
                        ano = ano_destino
                    else:
                        raise ValueError('Ladder de destino é histórico mas não possui mês/ano definido')
                posicao_dest = HistoricoLadder(jogador=posicao_orig.jogador, posicao=posicao_orig.posicao, mes=mes, ano=ano)
                posicao_dest.save()
                
    # Apaga posições que se mantiverem negativas (jogadores não presentes na ladder)
    for posicao_dest in ladder_destino:
        if posicao_dest.posicao < 0:
            posicao_dest.delete()
    