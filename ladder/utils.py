# -*- coding: utf-8 -*-
"""Funções para ladder"""
import calendar
import datetime

from django.db import transaction
from django.utils import timezone

from ladder.models import RegistroLadder, HistoricoLadder, PosicaoLadder, \
    InicioLadder, LutaLadder, JogadorLuta, Luta


def alterar_ladder(registro_ladder):
    """Altera posições da ladder com base em um registro de ladder"""
    desafiante = registro_ladder.desafiante
    desafiado = registro_ladder.desafiado
    
    # Se desafiante venceu
    if registro_ladder.desafiante_venceu():
        # Definir se deve alterar histórico
        if registro_ladder.is_historico():
            mes, ano = registro_ladder.mes_ano_ladder
            ladder_para_alterar = HistoricoLadder.objects.filter(ano=ano, mes=mes)
        else:
            ladder_para_alterar = PosicaoLadder.objects
            
        
        # Verificar se desafiante já estava na ladder
        if ladder_para_alterar.filter(jogador=desafiante).exists():
            posicao_desafiante = ladder_para_alterar.get(jogador=desafiante).posicao
        else:
            posicao_desafiante = ladder_para_alterar.all().order_by('-posicao')[0].posicao + 1
            
            # Criar posição desafiante
            if registro_ladder.is_historico():
                novo_entrante = HistoricoLadder(posicao=posicao_desafiante, jogador=desafiante, mes=mes, ano=ano)
            else:
                novo_entrante = PosicaoLadder(posicao=posicao_desafiante, jogador=desafiante)
            novo_entrante.save()
            
        posicao_desafiado = ladder_para_alterar.get(jogador=desafiado).posicao
        
        posicoes_entre_jogadores = list(ladder_para_alterar.filter(posicao__lte=posicao_desafiante, 
                                                                posicao__gte=posicao_desafiado).order_by('-posicao'))
        
        # Retira desafiante da ladder momentaneamente
        posicoes_entre_jogadores[0].posicao = 0
        posicoes_entre_jogadores[0].save()
        
        # Retira uma posição de cada jogador à frente 
        for posicao_jogador in posicoes_entre_jogadores[1:]:
            posicao_jogador.posicao += 1
            posicao_jogador.save()
        
        # Coloca desafiante uma posição à frente do desafiado (final da lista)
        posicoes_entre_jogadores[0].posicao = posicoes_entre_jogadores[-1].posicao - 1
        posicoes_entre_jogadores[0].save()
        
    else:
        # Desafiante perdeu, caso seja novo entrante, adicionar a ladder
        # Definir se deve alterar histórico
        if registro_ladder.is_historico():
            mes, ano = registro_ladder.mes_ano_ladder
            ladder_para_alterar = HistoricoLadder.objects.filter(ano=ano, mes=mes)
        else:
            ladder_para_alterar = PosicaoLadder.objects
        
        if not ladder_para_alterar.filter(jogador=desafiante).exists():
            posicao_desafiante = ladder_para_alterar.all().order_by('-posicao')[0].posicao + 1
            
            # Criar posição desafiante
            if registro_ladder.is_historico():
                novo_entrante = HistoricoLadder(posicao=posicao_desafiante, jogador=desafiante, mes=mes, ano=ano)
            else:
                novo_entrante = PosicaoLadder(posicao=posicao_desafiante, jogador=desafiante)
            novo_entrante.save()
            
def recalcular_ladder(mes=None, ano=None):
    """Recalcula todas as posições de uma ladder"""
    # Se mês e ano não foram preenchidos, ladder é a atual
    if mes == None and ano == None:
        ladder = PosicaoLadder.objects
        
        # Guarda se estamos alterando ladder atual
        is_ladder_atual = True
        
        # Verificar histórico mês anterior
        data_atual = timezone.now().date()
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
        # Pegar ladder histórica para mês/ano, caso não exista a ladder em si, verificar se existem registros válidos
        #até o final do ano/mês apontado
        data_limite_registro_ladder = datetime.date(ano, mes, calendar.monthrange(ano, mes)[1]) + datetime.timedelta(days=1)
        
        if HistoricoLadder.objects.filter(ano=ano, mes=mes).exists() or RegistroLadder.objects.filter(
                cancelamentoregistroladder__isnull=True, admin_validador__isnull=False, data_hora__date__lt=data_limite_registro_ladder).exists():
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
                
                # Preencher com dados do histórico
                for posicao_historico in historico_mes_anterior:
                    if is_ladder_atual:
                        nova_posicao = PosicaoLadder(jogador=posicao_historico.jogador, posicao=posicao_historico.posicao)
                        nova_posicao.save()
                    else:
                        nova_posicao = HistoricoLadder(jogador=posicao_historico.jogador, posicao=posicao_historico.posicao, ano=ano, mes=mes)
                        nova_posicao.save()
                    
                # Recalcular com registros do mês validados e não cancelados
                try:
                    for registro_ladder in RegistroLadder.objects.filter(cancelamentoregistroladder__isnull=True, 
                                                                         admin_validador__isnull=False, data_hora__month=mes, 
                                                                         data_hora__year=ano).order_by('data_hora'):
                        # Verificar posições
                        verificar_posicoes_desafiante_desafiado(registro_ladder.ladder, registro_ladder.desafiante,
                                                                 registro_ladder.desafiado, registro_ladder.data_hora,
                                                                 registro_ladder.desafio_coringa)
#                         # Validar uso coringa
#                         if registro_ladder.desafio_coringa:
#                             # Verificar se desafiante pode utilizar desafio coringa
#                             if not registro_ladder.desafiante.pode_usar_coringa_na_data(registro_ladder.data_hora.date()):
#                                 raise ValueError(RegistroLadder.MENSAGEM_ERRO_PERIODO_ESPERA_CORINGA)
                            
                        alterar_ladder(registro_ladder)
                except Exception as e:
                    raise ValueError(f'Registro Ladder {registro_ladder.id}: {e}')
        except:
            raise
        
    else:
        # Se não, buscar de ladder inicial
        try:
            with transaction.atomic():
                # Remover posições da ladder
                ladder.all().delete()
                
                # Preencher com dados do histórico
                for posicao_historico in InicioLadder.objects.all().order_by('posicao'):
                    if is_ladder_atual:
                        nova_posicao = PosicaoLadder(jogador=posicao_historico.jogador, posicao=posicao_historico.posicao)
                        nova_posicao.save()
                    else:
                        nova_posicao = HistoricoLadder(jogador=posicao_historico.jogador, posicao=posicao_historico.posicao, ano=ano, mes=mes)
                        nova_posicao.save()
                    
                # Recalcular com registros do mês validados e não cancelados
                try:
                    for registro_ladder in RegistroLadder.objects.filter(cancelamentoregistroladder__isnull=True, 
                                                                         admin_validador__isnull=False, data_hora__month=mes, 
                                                                         data_hora__year=ano).order_by('data_hora'):
                        alterar_ladder(registro_ladder)
                except Exception as e:
                    raise ValueError(f'Registro Ladder {registro_ladder.id}: {e}')
        except:
            raise
        
    
            
def verificar_posicoes_desafiante_desafiado(ladder, desafiante, desafiado, data_hora, desafio_coringa):
    """Verifica se desafiante está abaixo e com a distância correta de desafiado na ladder"""
    # Verifica se desafiante e desafiado não estão de férias na data
    if desafiante.de_ferias_na_data(data_hora.date()):
        raise ValueError(RegistroLadder.MENSAGEM_ERRO_DESAFIANTE_FERIAS)
    
    if desafiado.de_ferias_na_data(data_hora.date()):
        raise ValueError(RegistroLadder.MENSAGEM_ERRO_DESAFIADO_FERIAS)
    
    # Jogador não pode desafiar a si mesmo
    if desafiante == desafiado:
        raise ValueError(RegistroLadder.MENSAGEM_ERRO_MESMO_JOGADOR)
    
    if ladder.filter(jogador=desafiante).exists():
        posicao_desafiante = ladder.get(jogador=desafiante).posicao
    else:
        # Se não está na ladder, posição do desafiante é atrás do último
        posicao_desafiante = ladder.all().order_by('-posicao')[0].posicao + 1
    
    posicao_desafiado = ladder.get(jogador=desafiado).posicao
    
    if posicao_desafiante < posicao_desafiado:
        raise ValueError(RegistroLadder.MENSAGEM_ERRO_DESAFIANTE_ACIMA_DESAFIADO)
    elif not desafio_coringa:
        # Verificar quais jogadores são desafiáveis devido a possibilidade de férias
        desafiaveis = list()
        for jogador_posicao in ladder.filter(posicao__lt=posicao_desafiante).order_by('-posicao'):
            if not jogador_posicao.jogador.de_ferias_na_data(data_hora.date()):
                desafiaveis.append(jogador_posicao.jogador)
                
                # Verifica se quantidade de desafiáveis já supre o limite de posições acima
                if len(desafiaveis) == RegistroLadder.LIMITE_POSICOES_DESAFIO:
                    break
        
        # Desafiado é desafiável?
        if desafiado not in desafiaveis:
            raise ValueError(RegistroLadder.MENSAGEM_ERRO_DESAFIANTE_MUITO_ABAIXO_DESAFIADO)
        
def validar_e_salvar_lutas_ladder(registro_ladder, formset_lutas):
    """Valida lutas em um formset para adicioná-las a registro de ladder"""
    # Verificar se ganhadores apontados batem com resultado do registro da ladder
    vitorias_desafiante = 0
    vitorias_desafiado = 0
    
    total_lutas = registro_ladder.score_desafiante + registro_ladder.score_desafiado 
    
    # Guarda ids das lutas válidas para registro ladder
    lutas_validas_registro_ladder = list()
    
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
        if luta.ganhador not in [registro_ladder.desafiante, registro_ladder.desafiado]:
            raise ValueError(f'Luta {indice_luta} indica ganhador que não está entre os participantes')
        
        elif luta.ganhador == registro_ladder.desafiante:
            vitorias_desafiante += 1
        elif luta.ganhador == registro_ladder.desafiado:
            vitorias_desafiado += 1
             
        # Se número de vitórias for incompatível
        if vitorias_desafiante > registro_ladder.score_desafiante or \
                vitorias_desafiado > registro_ladder.score_desafiado:
            raise ValueError('Resultado geral informado é incompatível com resultados das lutas')
         
        # Preencher campos de luta pelo registro de ladder
        luta.adicionada_por = registro_ladder.adicionado_por
        luta.data = registro_ladder.data_hora.date()
        luta.save()
         
        # Guardar id da luta como válida
        lutas_validas_registro_ladder.append(luta.id)
        
        # Relacionar a registro de ladder se não for alteração
        if not LutaLadder.objects.filter(registro_ladder=registro_ladder, luta=luta).exists():
            luta_ladder = LutaLadder(registro_ladder=registro_ladder, luta=luta, indice_registro_ladder=indice_luta)
            luta_ladder.save()
         
        # Adicionar jogadores a luta, se não for alteração
        jogadores_luta = JogadorLuta.objects.filter(luta=luta).order_by('id')
        
        # Preencher desafiante
        if jogadores_luta.count() >= 1: # Desafiante é sempre o primeiro a ser inserido
            
            # Verificar se houve alteração
            jogador_desafiante_luta = jogadores_luta[0]
            if jogador_desafiante_luta.jogador != registro_ladder.desafiante \
                    or jogador_desafiante_luta.personagem != form_luta.cleaned_data['personagem_desafiante']:
                jogador_desafiante_luta.jogador = registro_ladder.desafiante
                jogador_desafiante_luta.personagem = form_luta.cleaned_data['personagem_desafiante']
                jogador_desafiante_luta.save(update_fields=['jogador', 'personagem'])
        else:
            jogador_desafiante_luta = JogadorLuta(jogador=registro_ladder.desafiante, luta=luta,
                                                  personagem=form_luta.cleaned_data['personagem_desafiante'])
            jogador_desafiante_luta.save()
             
        # Preencher desafiado
        if jogadores_luta.count() >= 2: # Desafiado é sempre o segundo a ser inserido
            
            # Verificar se houve alteração
            jogador_desafiado_luta = jogadores_luta[1]
            if jogador_desafiado_luta.jogador != registro_ladder.desafiado \
                    or jogador_desafiado_luta.personagem != form_luta.cleaned_data['personagem_desafiado']:
                jogador_desafiado_luta.jogador = registro_ladder.desafiado
                jogador_desafiado_luta.personagem = form_luta.cleaned_data['personagem_desafiado']
                jogador_desafiado_luta.save(update_fields=['jogador', 'personagem'])
        else:
            jogador_desafiado_luta = JogadorLuta(jogador=registro_ladder.desafiado, luta=luta,
                                                 personagem=form_luta.cleaned_data['personagem_desafiado'])
            jogador_desafiado_luta.save()
    
    # Apagar lutas que não são mais válidas para registro ladder
    Luta.objects.filter(lutaladder__registro_ladder=registro_ladder).exclude(id__in=lutas_validas_registro_ladder).delete()
