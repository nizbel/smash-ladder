# -*- coding: utf-8 -*-
"""Funções para ladder"""
import calendar
import datetime
import re

from django.db import transaction
from django.db.models.aggregates import Sum, Max
from django.db.models.expressions import F
from django.db.models.query_utils import Q
from django.utils import timezone

from jogadores.models import Jogador
from ladder.models import DesafioLadder, HistoricoLadder, PosicaoLadder, \
    InicioLadder, LutaLadder, JogadorLuta, Luta, ResultadoDesafioLadder, \
    RemocaoJogador, DecaimentoJogador, ResultadoDecaimentoJogador, \
    ResultadoRemocaoJogador, PermissaoAumentoRange, Season
from smashLadder.utils import mes_ano_ant


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
    
    # Buscar season atual
    season_atual = Season.objects.order_by('-data_inicio')[0]
    
    # Preparar iterador de desafio
    evento = None
    try:
        with transaction.atomic():
            
            # Definir desafios a serem recalculados
            if informou_desafio:
                eventos = list(DesafioLadder.validados.na_season(season_atual).filter(data_hora__gte=desafio_ladder.data_hora) \
                               .exclude(id=desafio_ladder.id).order_by('data_hora', 'posicao_desafiado', 'id'))
                
                # Adiciona desafio atual se não tiver sido cancelado
                if not desafio_ladder.is_cancelado():
                    eventos.append(desafio_ladder)
                    
                # Adicionar remoções
                remocoes = RemocaoJogador.objects.filter(data__gte=desafio_ladder.data_hora) \
                    .annotate(data_hora=F('data')).annotate(posicao_desafiado=F('posicao_jogador')).order_by('data', '-posicao_desafiado')
                eventos.extend(list(remocoes))
                    
                # Adicionar decaimentos
                decaimentos = DecaimentoJogador.objects.filter(data__gte=desafio_ladder.data_hora) \
                    .annotate(data_hora=F('data')).annotate(posicao_desafiado=F('posicao_inicial')).order_by('data', '-posicao_desafiado')
                eventos.extend(list(decaimentos))
                
                eventos.sort(key=lambda x: (x.data_hora, x.posicao_desafiado if isinstance(x, DesafioLadder) else -x.posicao_desafiado))
                
                # Apagar ladders futuras e resultados para reescrever
                mes, ano = desafio_ladder.mes_ano_ladder

                desafios_a_desfazer = list(DesafioLadder.validados.filter(data_hora__gte=desafio_ladder.data_hora)).exclude(id=desafio_ladder.id)
                if desafio_ladder.is_cancelado():
                    desafios_a_desfazer.append(desafio_ladder)
                    
                ladder_resultante = desfazer_lote_desafios(desafios_a_desfazer, list(PosicaoLadder.objects.all()), 
                                                           remocoes, decaimentos)
                
                copiar_ladder(PosicaoLadder.objects.all().order_by('posicao'), ladder_resultante)
                
                # Limpar resultados
                ResultadoDecaimentoJogador.objects.filter(decaimento__in=decaimentos).delete()
                ResultadoDesafioLadder.objects.filter(desafio_ladder__admin_validador__isnull=False, desafio_ladder__cancelamentodesafioladder__isnull=True) \
                    .filter(desafio_ladder__data_hora__gte=desafio_ladder.data_hora).delete()
                ResultadoRemocaoJogador.objects.filter(remocao__in=remocoes).delete()
                            
            elif informou_ladder_atual:
                data_atual = timezone.localdate()
                mes_atual = data_atual.month
                ano_atual = data_atual.year
                
                eventos = list(DesafioLadder.validados.filter(data_hora__month=mes_atual, data_hora__year=ano_atual) \
                    .order_by('data_hora', 'posicao_desafiado', 'id'))
                
                # Adicionar remoções
                eventos.extend(list(RemocaoJogador.objects.filter(data__month=mes_atual, data__year=ano_atual) \
                    .annotate(data_hora=F('data')).annotate(posicao_desafiado=F('posicao_jogador')).order_by('data', '-posicao_desafiado')))
                
                # Adicionar decaimentos
                eventos.extend(list(DecaimentoJogador.objects.filter(data__month=mes_atual, data__year=ano_atual) \
                    .annotate(data_hora=F('data')).annotate(posicao_desafiado=F('posicao_inicial')).order_by('data', '-posicao_desafiado')))
                
                eventos.sort(key=lambda x: (x.data_hora, x.posicao_desafiado if isinstance(x, DesafioLadder) else -x.posicao_desafiado))
                
                # Copiar último histórico ou inicial
                if HistoricoLadder.objects.all().exists():
                    # Pegar último histórico
                    mes, ano = HistoricoLadder.objects.all().order_by('-ano', '-mes').values_list('mes', 'ano')[0]
                    copiar_ladder(PosicaoLadder.objects.all().order_by('posicao'), 
                                  HistoricoLadder.objects.filter(ano=ano, mes=mes).order_by('posicao'))
                else:
                    copiar_ladder(PosicaoLadder.objects.all().order_by('posicao'), 
                                  InicioLadder.objects.all().order_by('posicao'))
                    
                mes = None
                ano = None
                
                # Limpar resultados
                ResultadoDecaimentoJogador.objects.filter(decaimento__data__month=mes_atual, decaimento__data__year=ano_atual).delete()
                ResultadoDesafioLadder.objects.filter(desafio_ladder__admin_validador__isnull=False, desafio_ladder__cancelamentodesafioladder__isnull=True) \
                    .filter(desafio_ladder__data_hora__month=mes_atual, desafio_ladder__data_hora__year=ano_atual).delete()
                ResultadoRemocaoJogador.objects.filter(remocao__data__month=mes_atual, remocao__data__year=ano_atual).delete()
                
                
            elif informou_ladder_historico:
                data = timezone.make_aware(timezone.datetime(ano, mes, 1))
                eventos = list(DesafioLadder.validados.filter(data_hora__gte=data) \
                    .order_by('data_hora', 'posicao_desafiado', 'id'))
                
                # Adicionar remoções
                eventos.extend(list(RemocaoJogador.objects.filter(data__gte=data) \
                    .annotate(data_hora=F('data')).annotate(posicao_desafiado=F('posicao_jogador')).order_by('data', '-posicao_desafiado')))
                
                # Adicionar decaimentos
                eventos.extend(list(DecaimentoJogador.objects.filter(data__gte=data) \
                    .annotate(data_hora=F('data')).annotate(posicao_desafiado=F('posicao_inicial')).order_by('data', '-posicao_desafiado')))
                
                eventos.sort(key=lambda x: (x.data_hora, x.posicao_desafiado if isinstance(x, DesafioLadder) else -x.posicao_desafiado))
                
                # Copiar último histórico ou inicial
                mes_anterior, ano_anterior = mes_ano_ant(mes, ano)
                    
                if HistoricoLadder.objects.filter(mes=mes_anterior, ano=ano_anterior).exists():
                    # Pegar último histórico
                    copiar_ladder(HistoricoLadder.objects.filter(mes=mes, ano=ano).order_by('posicao'), 
                              HistoricoLadder.objects.filter(mes=mes_anterior, ano=ano_anterior).order_by('posicao'),
                              mes, ano)
                else:
                    copiar_ladder(HistoricoLadder.objects.filter(mes=mes, ano=ano).order_by('posicao'), 
                              InicioLadder.objects.all().order_by('posicao'),
                              mes, ano)
                    
                # Limpar resultados
                ResultadoDecaimentoJogador.objects.filter(decaimento__data__gte=data).delete()
                ResultadoDesafioLadder.objects.filter(desafio_ladder__admin_validador__isnull=False, desafio_ladder__cancelamentodesafioladder__isnull=True) \
                    .filter(desafio_ladder__data_hora__gte=data).delete()
                ResultadoRemocaoJogador.objects.filter(remocao__data__gte=data).delete()
                
            mes_atual = mes
            ano_atual = ano

            # Reescrever
            for evento in eventos:
#                 print(evento)
                # Verificar se alterou mês/ano para próximo desafio
                if isinstance(evento, DesafioLadder):
                    mes, ano = evento.mes_ano_ladder
                elif isinstance(evento, RemocaoJogador):
                    mes, ano = evento.mes_ano_ladder
                elif isinstance(evento, DecaimentoJogador):
                    mes, ano = evento.mes_ano_ladder
                    
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
                            else:
                                # Gerar histórico de ladder
                                copiar_ladder(HistoricoLadder.objects.filter(mes=prox_mes, ano=prox_ano).order_by('posicao'), 
                                              HistoricoLadder.objects.filter(mes=mes_atual, ano=ano_atual).order_by('posicao'),
                                              prox_mes, prox_ano)
                                
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
                                          HistoricoLadder.objects.filter(mes=mes_atual, ano=ano_atual).order_by('posicao'),
                                          prox_mes, prox_ano)
                                
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
                
                if isinstance(evento, DesafioLadder):
                    verificar_posicoes_desafiante_desafiado(evento, list(ladder))
                    
                    alterar_ladder(evento, False)
                    
                elif isinstance(evento, RemocaoJogador):
                    processar_remocao(evento)
                    
                elif isinstance(evento, DecaimentoJogador):
                    # Verificar se decaimento ainda é válido
                    if verificar_decaimento_valido(evento):
                        # Se válido, verificar posição
                        posicao_decaimento = evento.jogador.posicao_em(evento.data)
                        if posicao_decaimento != evento.posicao_inicial:
                            evento.posicao_inicial = posicao_decaimento
                            evento.save()
                            
                        if not evento.qtd_periodos_inatividade == 1 \
                                or (evento.qtd_periodos_inatividade == 1 and not DecaimentoJogador.ABONAR_PRIMEIRO_DECAIMENTO):
                            decair_jogador(evento)
                    else:
                        evento.delete()
                
            # Se tiver chegado a data atual, retornar
            if mes_atual == None and ano_atual == None:
                return
            
            # Copiar ladder até posição atual
            while mes_atual != timezone.localdate().month or ano_atual != timezone.localdate().year:
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
                else:
                    # Gerar histórico de ladder
                    copiar_ladder(HistoricoLadder.objects.filter(mes=prox_mes, ano=prox_ano).order_by('posicao'), 
                                  HistoricoLadder.objects.filter(mes=mes_atual, ano=ano_atual).order_by('posicao'),
                                  prox_mes, prox_ano)
                    
                mes_atual = prox_mes
                ano_atual = prox_ano
            
    except Exception as e:
        if evento:
            nome_evento = re.sub(r'(\w)([A-Z])', r'\1 \2', evento.__class__.__name__)
            raise ValueError(f'{nome_evento} {evento.id}: {e}')
        raise

def alterar_ladder(desafio_ladder, verificar_posteriores=True):
    """Altera posições da ladder com base em um desafio de ladder"""
    # Verifica se há desafios ou decaimentos validados posteriores, se sim, recalcular ladder
    if verificar_posteriores:
        if DesafioLadder.validados.filter(data_hora__gte=desafio_ladder.data_hora).exclude(id=desafio_ladder.id).exists():
            recalcular_ladder(desafio_ladder)
            return
        elif DecaimentoJogador.objects.filter(data__gte=desafio_ladder.data_hora).exists():
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
        posicao_desafiado = desafiado.posicao_em(desafio_ladder.data_hora)
        if posicao_desafiado == 0:
            posicao_desafiado = gerar_posicao_novo_entrante(desafio_ladder, desafiado)
            
            # Criar posição desafiado
            if desafio_ladder.is_historico():
                novo_entrante = HistoricoLadder(posicao=posicao_desafiado, jogador=desafiado, mes=mes, ano=ano)
            else:
                novo_entrante = PosicaoLadder(posicao=posicao_desafiado, jogador=desafiado)
            novo_entrante.save()
            
        # Verificar posição do desafiante
        posicao_desafiante = desafiante.posicao_em(desafio_ladder.data_hora)
        if posicao_desafiante == 0:
            posicao_desafiante = gerar_posicao_novo_entrante(desafio_ladder, desafiante)
            # Criar posição desafiante
            if desafio_ladder.is_historico():
                novo_entrante = HistoricoLadder(posicao=posicao_desafiante, jogador=desafiante, mes=mes, ano=ano)
            else:
                novo_entrante = PosicaoLadder(posicao=posicao_desafiante, jogador=desafiante)
            novo_entrante.save()
        
        posicoes_entre_jogadores = list()
        posicoes_alterar_ladder = list(ladder_para_alterar.all().order_by('-posicao'))
        # Buscar desafiado e desafiante nas posições da ladder
        achou_desafiante = False
        for posicao in posicoes_alterar_ladder:
            if posicao.jogador == desafiante:
                posicoes_entre_jogadores.append(posicao)
                achou_desafiante = True
                
            elif achou_desafiante:
                posicoes_entre_jogadores.append(posicao)
                if posicao.jogador == desafiado:
                    break
            
#         posicoes_entre_jogadores = list(ladder_para_alterar.filter(posicao__lte=posicao_desafiante, 
#                                                                 posicao__gte=posicao_desafiado).order_by('-posicao'))
        
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
        posicao_desafiado = desafiado.posicao_em(desafio_ladder.data_hora)
        if posicao_desafiado == 0:
            posicao_desafiado = gerar_posicao_novo_entrante(desafio_ladder, desafiado)
            # Criar posição desafiado
            if desafio_ladder.is_historico():
                novo_entrante = HistoricoLadder(posicao=posicao_desafiado, jogador=desafiado, mes=mes, ano=ano)
            else:
                novo_entrante = PosicaoLadder(posicao=posicao_desafiado, jogador=desafiado)
            novo_entrante.save()
        
        posicao_desafiante = desafiante.posicao_em(desafio_ladder.data_hora)
        if posicao_desafiante == 0:
            posicao_desafiante = gerar_posicao_novo_entrante(desafio_ladder, desafiante)
            # Criar posição desafiante
            if desafio_ladder.is_historico():
                novo_entrante = HistoricoLadder(posicao=posicao_desafiante, jogador=desafiante, mes=mes, ano=ano)
            else:
                novo_entrante = PosicaoLadder(posicao=posicao_desafiante, jogador=desafiante)
            novo_entrante.save()

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
        
    
            
def verificar_posicoes_desafiante_desafiado(desafio_ladder, ladder=None):
    """Verifica se desafiante está abaixo e com a distância correta de desafiado na ladder"""
    desafiante = desafio_ladder.desafiante
    desafiado = desafio_ladder.desafiado
    
    # Jogador não pode desafiar a si mesmo
    if desafiante == desafiado:
        raise ValueError(DesafioLadder.MENSAGEM_ERRO_MESMO_JOGADOR)
    
    # Verificar posição do desafiado
    desafiado_esta_na_ladder = True
    posicao_desafiado = desafiado.posicao_em(desafio_ladder.data_hora)
    if posicao_desafiado == 0:
        desafiado_esta_na_ladder = False
        posicao_desafiado = gerar_posicao_novo_entrante(desafio_ladder, desafiado)
    
    # Verificar posição do desafiante
    posicao_desafiante = desafiante.posicao_em(desafio_ladder.data_hora)
    if posicao_desafiante == 0:
        posicao_desafiante = gerar_posicao_novo_entrante(desafio_ladder, desafiante)
    
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
            
            else:
                # Desfazer alterações de desafios no mesmo horário
                ladder = desfazer_lote_desafios(list(DesafioLadder.validados.filter(data_hora=desafio_ladder.data_hora)), 
                                                ladder)
            
            # TODO Melhorar isso aqui sem férias
            # Verificar quais jogadores são desafiáveis devido a possibilidade de férias
            desafiaveis = list()
            ladder.sort(key=lambda x: x.posicao, reverse=True)
            
            # Verificar se desafiante possui permissão de aumento de range
            limite_range = (DesafioLadder.LIMITE_POSICOES_DESAFIO + PermissaoAumentoRange.AUMENTO_RANGE) \
                if desafio_ladder.desafiante.possui_permissao_aumento_range(desafio_ladder.data_hora) else DesafioLadder.LIMITE_POSICOES_DESAFIO

            for jogador_posicao in [ladder_posicao for ladder_posicao in ladder if ladder_posicao.posicao < posicao_desafiante]:
                desafiaveis.append(jogador_posicao.jogador)
                
                # Verifica se quantidade de desafiáveis já supre o limite de posições acima
                if len(desafiaveis) == limite_range:
                    break
            
            # Desafiado é desafiável?
            if desafiado not in desafiaveis:
                # Verificar se desafiante possui permissão de aumento de range
                if desafio_ladder.desafiante.possui_permissao_aumento_range(desafio_ladder.data_hora):
                    raise ValueError(PermissaoAumentoRange.MENSAGEM_ERRO_DESAFIANTE_MUITO_ABAIXO_DESAFIADO)
                else:
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

def desfazer_lote_desafios(desafios, ladder, remocoes=None, decaimentos=None):
    """Retorna posições da ladder anteriores ao resultado de um lote de desafios ordenados"""
    # Se desafios está vazio, retornar ladder
    if not desafios:
        return ladder
    
    # Guardar season atual
    season_atual = Season.objects.order_by('-data_inicio')[0]

    jogadores_ladder = [posicao_ladder.jogador_id for posicao_ladder in ladder]
    
    resultados_desafios = dict(ResultadoDesafioLadder.objects.filter(desafio_ladder__in=desafios).order_by('jogador').values('jogador') \
                               .annotate(alteracao_total=Sum('alteracao_posicao')).values_list('jogador', 'alteracao_total'))
    
    
    if not decaimentos:
        decaimentos = list()
    
    resultados_decaimentos = dict(ResultadoDecaimentoJogador.objects.filter(decaimento__in=decaimentos).order_by('jogador').values('jogador') \
                              .annotate(alteracao_total=Sum('alteracao_posicao')).values_list('jogador', 'alteracao_total'))
    
    if not remocoes:
        remocoes = list()
    
    resultados_remocoes = dict(ResultadoRemocaoJogador.objects.filter(remocao__in=remocoes).order_by('jogador').values('jogador') \
                              .annotate(alteracao_total=Sum('alteracao_posicao')).values_list('jogador', 'alteracao_total'))
    
    resultados = { k: resultados_desafios.get(k, 0) + resultados_decaimentos.get(k, 0) + resultados_remocoes.get(k, 0)  \
                  for k in set(resultados_desafios) | set(resultados_decaimentos) | set(resultados_remocoes) }
    
    # Listar jogadores removidos pois serão tratados diferente
    jogadores_remocoes = [remocao.jogador_id for remocao in remocoes]
    
    # Adicionar removidos a resultados caso não estejam presentes
    for jogador_removido in [jogador for jogador in jogadores_remocoes if jogador not in resultados]:
        resultados[jogador_removido] = 0
    
    # Se remoções está preenchido, verificar se ladder é atual ou histórico para posterior operação
    if remocoes:
        data_atual = timezone.localdate()
        mes, ano = desafios[0].mes_ano_ladder
        ladder_atual = bool(mes == data_atual.month and ano == data_atual.year)
    
    # Verificar se todos os jogadores presentes no resultado estão indicados na ladder
    for jogador in resultados:
        if jogador not in jogadores_ladder and jogador not in jogadores_remocoes:
            raise ValueError(f'Resultados do desafio não condizem com a ladder especificada')
    
    # Alterar ladder
    for jogador, alteracao in resultados.items():
        # Procurar jogador
        if jogador in jogadores_remocoes:
            # Pegar remoção mais antiga do jogador e desfazer desafios anteriores
            remocoes_jogador = [remocao for remocao in remocoes if remocao.jogador_id == jogador]
            primeira_remocao = sorted(remocoes_jogador, key=lambda x: x.data)[0]
            
            alteracao_jogador = ResultadoDesafioLadder.objects.filter(desafio_ladder__in=desafios, jogador__id=jogador,
                                                                            desafio_ladder__data_hora__lt=primeira_remocao.data) \
                                      .values('jogador').aggregate(alteracao_total=Sum('alteracao_posicao'))['alteracao_total'] or 0
                                      
            alteracao_jogador += ResultadoDecaimentoJogador.objects.filter(decaimento__in=decaimentos, jogador__id=jogador,
                                                                            decaimento__data__lt=primeira_remocao.data) \
                                      .values('jogador').aggregate(alteracao_total=Sum('alteracao_posicao'))['alteracao_total'] or 0
                                      
            alteracao_jogador += ResultadoRemocaoJogador.objects.filter(remocao__in=remocoes, jogador__id=jogador,
                                                                            remocao__data__lt=primeira_remocao.data) \
                                      .values('jogador').aggregate(alteracao_total=Sum('alteracao_posicao'))['alteracao_total'] or 0
            
            if ladder_atual:
                ladder.append(PosicaoLadder(jogador=primeira_remocao.jogador, 
                                            posicao=(primeira_remocao.posicao_jogador - alteracao_jogador)))
            else:
                ladder.append(HistoricoLadder(mes=mes, ano=ano, jogador=primeira_remocao.jogador, 
                                              posicao=(primeira_remocao.posicao_jogador - alteracao_jogador)))
                                      
        else:
            for posicao_ladder in ladder:
                if posicao_ladder.jogador_id == jogador:
                    # Alterar posição
                    posicao_ladder.posicao -= alteracao
                    break
                
    # Ordenar ladder após alterações
    ladder.sort(key=lambda x: x.posicao)
    
    # Verificar quais jogadores já existiam na ladder
    desafio_mais_antigo = sorted(desafios, key=lambda x: x.data_hora)[0]
    novos_entrantes = list()
    
    for posicao_ladder in reversed(ladder):
        if DesafioLadder.validados.na_season(season_atual).filter(Q(desafiante__id=posicao_ladder.jogador_id) | Q(desafiado__id=posicao_ladder.jogador_id)) \
            .filter(data_hora__lt=desafio_mais_antigo.data_hora).exists():
            # Se jogador possuir desafio e não possuir remoção desde este desafio, não é novo entrante
            desafio_mais_recente_pre_desfeitos = DesafioLadder.validados.na_season(season_atual) \
                .filter(Q(desafiante__id=posicao_ladder.jogador_id) | Q(desafiado__id=posicao_ladder.jogador_id)) \
                .filter(data_hora__lt=desafio_mais_antigo.data_hora).order_by('-data_hora')[0]
            if RemocaoJogador.objects.filter(jogador__id=posicao_ladder.jogador_id).filter(data__range=[desafio_mais_recente_pre_desfeitos.data_hora, 
                                                                                                        desafio_mais_antigo.data_hora]).exists():
                novos_entrantes.append(posicao_ladder)
        elif not InicioLadder.objects.filter(jogador__id=posicao_ladder.jogador_id).exists():
            novos_entrantes.append(posicao_ladder)
    
    for posicao in novos_entrantes:
        ladder.remove(posicao)
    
    return ladder


def gerar_posicao_novo_entrante(desafio_ladder, jogador):
    """Retorna posição de novo entrante na data/hora do desafio definido"""
    desafios_validos = list(DesafioLadder.validados.filter(data_hora=desafio_ladder.data_hora).exclude(id=desafio_ladder.id) \
                            .order_by('posicao_desafiado', 'posicao_desafiante'))
    
    # Adicionar desafio especificado
    desafios_validos.append(desafio_ladder)
    # Ordenar
    desafios_validos.sort(key=lambda x: (x.posicao_desafiado, x.posicao_desafiante))
    
    # Definir ultima ladder
    mes, ano = mes_ano_ant(desafio_ladder.data_hora.month, desafio_ladder.data_hora.year)
    if HistoricoLadder.objects.filter(ano=ano, mes=mes).exists():
        ultima_ladder = HistoricoLadder.objects.filter(ano=ano, mes=mes)
    else:
        ultima_ladder = InicioLadder.objects.all()    
    
    # Buscar última posição disponível na data
    ultima_posicao_disponivel = max(DesafioLadder.validados.filter(data_hora__lt=desafio_ladder.data_hora, 
                                                                   data_hora__month=desafio_ladder.data_hora.month,
                                                                   data_hora__year=desafio_ladder.data_hora.year) \
        .aggregate(ultima_posicao=Max('posicao_desafiante'))['ultima_posicao'] or 0, 
        ultima_ladder.aggregate(ultima_posicao=Max('posicao'))['ultima_posicao'] or 0) + 1
        
    # Considerar jogadores que saíram da ladder
    if DesafioLadder.validados.filter(posicao_desafiante=ultima_posicao_disponivel-1, data_hora__month=desafio_ladder.data_hora.month,
                                      data_hora__year=desafio_ladder.data_hora.year,
                                      data_hora__lt=desafio_ladder.data_hora).exists():
        ultima_data_hora = DesafioLadder.validados.filter(posicao_desafiante=ultima_posicao_disponivel-1, 
                                                          data_hora__month=desafio_ladder.data_hora.month, 
                                                          data_hora__year=desafio_ladder.data_hora.year, 
                                                          data_hora__lt=desafio_ladder.data_hora) \
            .order_by('-data_hora')[0].data_hora
        
        ultima_posicao_disponivel -= RemocaoJogador.objects.filter(data__gt=ultima_data_hora, data__lt=desafio_ladder.data_hora).count()
        
        # Computar entradas no mês, anteriores ao desafio
        if DesafioLadder.validados.filter(data_hora__gt=ultima_data_hora, data_hora__lt=desafio_ladder.data_hora) \
                                      .exclude(desafiante__in=ultima_ladder.values_list('jogador', flat=True), 
                                               desafiado__in=ultima_ladder.values_list('jogador', flat=True)).exists():
            ultima_posicao_disponivel += DesafioLadder.validados.filter(data_hora__gt=ultima_data_hora, 
                                                                        data_hora__lt=desafio_ladder.data_hora) \
                                          .exclude(desafiante__in=ultima_ladder.values_list('jogador', flat=True)).count()
            ultima_posicao_disponivel += DesafioLadder.validados.filter(data_hora__gt=ultima_data_hora, 
                                                                        data_hora__lt=desafio_ladder.data_hora) \
                                          .exclude(desafiado__in=ultima_ladder.values_list('jogador', flat=True)).count()
        
    else:
        ultima_posicao_disponivel -= RemocaoJogador.objects.filter(data__month=desafio_ladder.data_hora.month,
                                      data__year=desafio_ladder.data_hora.year, data__lt=desafio_ladder.data_hora).count()
        # Computar entradas no mês, anteriores ao desafio
        if DesafioLadder.validados.filter(data_hora__month=desafio_ladder.data_hora.month,
                                      data_hora__year=desafio_ladder.data_hora.year, data_hora__lt=desafio_ladder.data_hora) \
                                      .exclude(desafiante__in=ultima_ladder.values_list('jogador', flat=True), 
                                               desafiado__in=ultima_ladder.values_list('jogador', flat=True)).exists():
            ultima_posicao_disponivel += DesafioLadder.validados.filter(data_hora__month=desafio_ladder.data_hora.month,
                                          data_hora__year=desafio_ladder.data_hora.year, data_hora__lt=desafio_ladder.data_hora) \
                                          .exclude(desafiante__in=ultima_ladder.values_list('jogador', flat=True)).count()
            ultima_posicao_disponivel += DesafioLadder.validados.filter(data_hora__month=desafio_ladder.data_hora.month,
                                          data_hora__year=desafio_ladder.data_hora.year, data_hora__lt=desafio_ladder.data_hora) \
                                          .exclude(desafiado__in=ultima_ladder.values_list('jogador', flat=True)).count()
    
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
    # Verifica se ladder de origem não está vazia
    if not ladder_origem:
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
    
def remover_jogador(remocao):
    """Remove um jogador da ladder"""
    # Verificar se jogador está na ladder da data
    data_atual = timezone.localdate()
#     if data.month == data_atual.month and data.year == data_atual.year:
#         ladder = PosicaoLadder.objects.all()
#     else:
#         ladder = HistoricoLadder.objects.filter(mes=data.month, ano=data.year)
#     
#     if not ladder.filter(jogador=jogador).exists():
#         raise ValueError('Jogador não estava presente na ladder na data especificada')
    
    try:
        with transaction.atomic():
#             # Verificar se jogador está na ladder
#             posicao_jogador = jogador.posicao_em(data)
#             if posicao_jogador == 0:
#                 raise ValueError('Jogador não estava presente na ladder na data especificada')
#             
#             # Gerar registro de remoção
#             remocao = RemocaoJogador(jogador=jogador, data=data, admin_removedor=admin_removedor, 
#                                      posicao_jogador=posicao_jogador)
#             remocao.save()
            
            # Recalcular ladders a partir da ladder da data
            if remocao.data.month == data_atual.month and remocao.data.year == data_atual.year:
                recalcular_ladder()
            else:
                recalcular_ladder(mes=remocao.data.month, ano=remocao.data.year)
    except:
        raise
        
def processar_remocao(remocao):
    """Processa uma remoção de jogador da ladder"""
    # Verifica se é ladder atual ou histórico
    data_atual = timezone.localdate()
    if remocao.data.month == data_atual.month and remocao.data.year == data_atual.year:
        ladder_para_alterar = PosicaoLadder.objects
    else:
        ladder_para_alterar = HistoricoLadder.objects.filter(ano=remocao.data.year, mes=remocao.data.month)
        
    try:
        with transaction.atomic():
            posicao_jogador_ladder = ladder_para_alterar.get(jogador=remocao.jogador)
            
            # Salva posição do jogador caso tenha sido alterada
            if posicao_jogador_ladder.posicao != remocao.posicao_jogador:
                remocao.posicao_jogador = posicao_jogador_ladder.posicao
                remocao.save()
            
            # Remove jogador da ladder
            posicao_jogador_ladder.delete()
            
            # Sobe uma posição todos os estiverem abaixo dele
            for posicao_ladder in ladder_para_alterar.filter(posicao__gt=remocao.posicao_jogador).order_by('posicao'):
                posicao_ladder.posicao -= 1
                posicao_ladder.save()
                
                # Gravar resultado da remoção
                resultado_remocao = ResultadoRemocaoJogador(jogador=posicao_ladder.jogador, alteracao_posicao=-1, remocao=remocao)
                resultado_remocao.save()
                
    except:
        raise
    
def avaliar_decaimento(jogador):
    """Avalia se jogador é alvo de decaimento por inatividade"""
    # Jogador deve estar na ladder atualmente
    if not PosicaoLadder.objects.filter(jogador=jogador).exists():
        raise ValueError(f'{jogador} não está na ladder')
    
    # Se ainda não há desafios validados na Season atual, não há decaimentos
    season_atual = Season.objects.order_by('-data_inicio')[0]
    if not DesafioLadder.validados.na_season(season_atual).exists():
        return None
    
    # Verificar último desafio validado do jogador na season
    if DesafioLadder.validados.na_season(season_atual).filter(Q(desafiante=jogador) | Q(desafiado=jogador)).exists():
        ultimo_desafio = DesafioLadder.validados.na_season(season_atual).filter(Q(desafiante=jogador) | Q(desafiado=jogador)) \
        .order_by('-data_hora')[0]
    else:
        # Se não há desafios registrados, buscar data do primeiro desafio adicionado na ladder nesta Season
        ultimo_desafio = DesafioLadder(data_hora=DesafioLadder.validados \
                                       .na_season(season_atual).order_by('data_hora')[0].data_hora)
    
    # Verificar se jogador já possui decaimento desde último desafio
    decaimentos_desde_desafio = DecaimentoJogador.objects.filter(jogador=jogador, data__gt=ultimo_desafio.data_hora)
    
    # Verificar quantidade de períodos de inatividade
    qtd_periodos_inatividade = (timezone.localdate() - ultimo_desafio.data_hora.date()).days
    qtd_periodos_inatividade = qtd_periodos_inatividade // DecaimentoJogador.PERIODO_INATIVIDADE
    
    # Gerar decaimento para quantidade de períodos apontado na variável, se 0, não deve ser criado
    decaimento_atual = 0
    for numero_decaimento in range(1, qtd_periodos_inatividade + 1, 1):
        if numero_decaimento not in [decaimento.qtd_periodos_inatividade for decaimento in decaimentos_desde_desafio]:
            decaimento_atual = numero_decaimento
            break
    
    if decaimento_atual > 0:
        # Gerar decaimento
        try: 
            with transaction.atomic():
                # Buscar data em que o período de inatividade foi completado
                data_decaimento = ultimo_desafio.data_hora.date() + datetime.timedelta(days=decaimento_atual * 
                                                                                       DecaimentoJogador.PERIODO_INATIVIDADE)
                
                data_decaimento = timezone.datetime(data_decaimento.year, data_decaimento.month, data_decaimento.day, 
                                                    tzinfo=timezone.get_current_timezone())
                
                posicao_inicial = jogador.posicao_em(data_decaimento)
                decaimento = DecaimentoJogador(jogador=jogador, data=data_decaimento, posicao_inicial=posicao_inicial, 
                                               qtd_periodos_inatividade=decaimento_atual)
                decaimento.save()
                
                return decaimento
        except:
            raise
    
    return None
    
def decair_jogador(decaimento):
    """Decai um jogador por inatividade"""
    # Definir se deve alterar histórico
    if decaimento.is_historico():
        mes, ano = decaimento.mes_ano_ladder
        ladder_para_alterar = HistoricoLadder.objects.filter(ano=ano, mes=mes)
    else:
        ladder_para_alterar = PosicaoLadder.objects
    
    # Se decaimento for de jogador no fim da ladder (não tem para onde cair), terminar função
    if decaimento.posicao_inicial == ladder_para_alterar.aggregate(ultima_posicao=Max('posicao'))['ultima_posicao']:
        return
    
    try:
        with transaction.atomic():
            # Remover resultados para recalculá-los
            ResultadoDecaimentoJogador.objects.filter(decaimento=decaimento).delete()
            
            # Salva posição do jogador caso tenha sido alterada
            posicao_jogador_ladder = ladder_para_alterar.get(jogador=decaimento.jogador)
            if posicao_jogador_ladder.posicao != decaimento.posicao_inicial:
                decaimento.posicao_inicial = posicao_jogador_ladder.posicao
                decaimento.save()
                
            # Buscar posições de jogadores que serão alteradas
            posicoes_entre_jogadores = list(ladder_para_alterar.filter(posicao__gte=decaimento.posicao_inicial, 
                                                                         posicao__lte=decaimento.posicao_inicial + DecaimentoJogador.QTD_POSICOES_DECAIMENTO) \
                                                                         .order_by('posicao'))
            
            # Retira jogador decaído da ladder momentaneamente
            posicoes_entre_jogadores[0].posicao = 0
            posicoes_entre_jogadores[0].save()
            
            # Adiciona uma posição a cada jogador à frente 
            for posicao_jogador in posicoes_entre_jogadores[1:]:
                posicao_jogador.posicao -= 1
                posicao_jogador.save()
                
                # Adiciona aos resultados do decaimento
                resultado_jogador = ResultadoDecaimentoJogador(decaimento=decaimento, jogador=posicao_jogador.jogador, alteracao_posicao=-1)
                resultado_jogador.save()
        
            # Coloca desafiante uma posição atrás do final da lista
            posicoes_entre_jogadores[0].posicao = posicoes_entre_jogadores[-1].posicao + 1
            posicoes_entre_jogadores[0].save()
            
            # Adiciona resultado para jogador que caiu
            resultado = ResultadoDecaimentoJogador(decaimento=decaimento, jogador=decaimento.jogador, 
                                   alteracao_posicao=posicoes_entre_jogadores[0].posicao - decaimento.posicao_inicial)
            resultado.save()
            
    except:
        raise
    
def verificar_decaimento_valido(decaimento):
    """Verifica se decaimento é válido"""
    # Decaimento só é válido na ladder atual
    season_atual = Season.objects.order_by('-data_inicio')[0]
    
#     print('desafios validados', DesafioLadder.validados.count())
#     print('desafios validados na season', DesafioLadder.validados.na_season(season_atual).count())
    
    # Se não há desafios, decaimento não é válido
    if not DesafioLadder.validados.na_season(season_atual).exists():
        return False
    
    if DesafioLadder.validados.na_season(season_atual) \
            .filter(Q(desafiante=decaimento.jogador) | Q(desafiado=decaimento.jogador)) \
            .filter(data_hora__lt=decaimento.data).exists():
        data_hora_ultimo_desafio = DesafioLadder.validados.na_season(season_atual) \
            .filter(Q(desafiante=decaimento.jogador) | Q(desafiado=decaimento.jogador)) \
            .filter(data_hora__lt=decaimento.data).order_by('-data_hora').values_list('data_hora', flat=True)[0]
    else:
        # Se não há desafios registrados, buscar data do primeiro desafio adicionado na ladder, na season
        data_hora_ultimo_desafio = DesafioLadder.validados.na_season(season_atual) \
        .order_by('data_hora')[0].data_hora
    
    # Retorna válido para caso de período de inatividade apontado pelo decaimento ainda ser verdadeiro
    return decaimento.data.date() >= data_hora_ultimo_desafio.date() \
        + datetime.timedelta(days=decaimento.qtd_periodos_inatividade * DecaimentoJogador.PERIODO_INATIVIDADE)
        
def buscar_desafiaveis(jogador, data_hora, coringa=False, retornar_ids=True):
    """Retorna lista com jogadores desafiáveis pelo jogador"""
    # Verificar se valores foram preenchidos
    if jogador == None:
        raise ValueError('Desafiante inválido')
    
    if data_hora == None:
        raise ValueError('Data/hora inválida')
    
    # Verificar se jogador pode usar coringa na data
    if coringa and not jogador.pode_usar_coringa_na_data(data_hora.date()):
        raise ValueError('Jogador não pode usar coringa na data')
    
    # Buscar ladder para data_hora especificada
    data_atual = timezone.localtime()
    if data_hora.month == data_atual.month and data_hora.year == data_atual.year:
        ladder_para_alterar = PosicaoLadder.objects.all().select_related('jogador')
    else:
        ladder_para_alterar = HistoricoLadder.objects.filter(ano=data_hora.year, mes=data_hora.month).select_related('jogador')
    
    # Desfazer desafios posteriores
    # Buscar remoções, decaimentos e desafios para desfazer
    remocoes = RemocaoJogador.objects.filter(data__gte=data_hora) \
        .annotate(data_hora=F('data')).annotate(posicao_desafiado=F('posicao_jogador')).order_by('data', '-posicao_desafiado')
        
    decaimentos = DecaimentoJogador.objects.filter(data__gte=data_hora) \
        .annotate(data_hora=F('data')).annotate(posicao_desafiado=F('posicao_inicial')).order_by('data', '-posicao_desafiado')
        
    desafios_a_desfazer = list(DesafioLadder.validados.filter(data_hora__gte=data_hora).filter(data_hora__month=data_hora.month, 
                                                                                                          data_hora__year=data_hora.year))
    
    ladder_para_alterar = desfazer_lote_desafios(desafios_a_desfazer, list(ladder_para_alterar), remocoes, decaimentos)
    ladder_para_alterar.sort(key=lambda x: -x.posicao)
    
    for posicao_ladder in ladder_para_alterar:
        if posicao_ladder.jogador == jogador:
            posicao_jogador = posicao_ladder.posicao
            break
    else:
        posicao_jogador = ladder_para_alterar[0].posicao + 1
    
    # Montar lista com desafiáveis
    desafiaveis = list()
    
    # Avaliar limite de range
    limite_range = (DesafioLadder.LIMITE_POSICOES_DESAFIO + PermissaoAumentoRange.AUMENTO_RANGE) \
                if jogador.possui_permissao_aumento_range(data_hora) else DesafioLadder.LIMITE_POSICOES_DESAFIO
                
    for desafiavel in [posicao_ladder.jogador for posicao_ladder in \
                       ladder_para_alterar if posicao_ladder.posicao < posicao_jogador]:
        if retornar_ids:
            desafiaveis.append(desafiavel.id)
        else:
            desafiaveis.append(desafiavel)
            
        if not coringa and len(desafiaveis) == limite_range:
            break
    
    # Se jogador estiver fora da ladder, adicionar jogadores que também estão de fora
    if posicao_jogador == ladder_para_alterar[0].posicao + 1:
        jogadores_fora_da_ladder = Jogador.objects.all().exclude(id=jogador.id) \
            .exclude(id__in=[posicao_ladder.jogador.id for posicao_ladder in ladder_para_alterar])
        for jogador_fora in jogadores_fora_da_ladder:
            if retornar_ids:
                desafiaveis.append(jogador_fora.id)
            else:
                desafiaveis.append(jogador_fora)
    
    return desafiaveis
    