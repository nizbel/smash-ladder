# -*- coding: utf-8 -*-
"""Views para torneios"""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.db.models.aggregates import Count
from django.db.models.expressions import F, Case, When
from django.db.models.query_utils import Q
from django.http.response import JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.urls.base import reverse

from jogadores.models import Jogador
from torneios.forms import CriarTorneioForm, JogadorTorneioForm, RoundForm
from torneios.models import Torneio, Partida, JogadorTorneio, Round
from torneios.utils import buscar_torneio_challonge, gerar_torneio_challonge, \
    buscar_jogadores_challonge, gerar_jogadores_challonge, \
    buscar_partidas_challonge, gerar_partidas_challonge, logar_challonge, \
    vincular_automaticamente_jogadores_torneio_a_ladder, alterar_nome_rounds


@login_required
def criar_torneio(request):
    """Cria um torneio vinculado ao Challonge"""
    # Precisa ser admin para gerar um torneio
    if not request.user.jogador.admin:
        raise PermissionDenied
    
    if request.POST:
        form_criar_torneio = CriarTorneioForm(request.POST)
        
        if form_criar_torneio.is_valid():
            identificador_torneio = form_criar_torneio.cleaned_data['identificador_torneio']
            site = form_criar_torneio.cleaned_data['site']
            delimitador_time = form_criar_torneio.cleaned_data['delimitador_time']
            
            if site == Torneio.SITE_CHALLONGE_ID:
                # Criar um torneio vinculado ao Challonge
                try:
                    with transaction.atomic():
                        # Verificar se identificador é uma URL
                        if Torneio.SITE_CHALLONGE_URL in identificador_torneio:
                            identificador_torneio = identificador_torneio.split('/')[-1]
                        
                        # Logar
                        logar_challonge()
                        
                        # Buscar torneio
                        dados_torneio = buscar_torneio_challonge(identificador_torneio)
                        torneio = gerar_torneio_challonge(dados_torneio)
                        torneio.adicionado_por = request.user.jogador
                        torneio.save()
                        
                        # Buscar jogadores
                        dados_jogadores = buscar_jogadores_challonge(identificador_torneio)
                        jogadores, times = gerar_jogadores_challonge(dados_jogadores, torneio, delimitador_time)
                        for time in times:
                            time.save()
                        for jogador in jogadores:
                            if jogador.time:
                                jogador.time_id = jogador.time.id
                            jogador.save()
                        
                        # Buscar partidas
                        dados_partidas = buscar_partidas_challonge(identificador_torneio)
                        partidas, rounds, vitorias_por_ausencia = gerar_partidas_challonge(dados_partidas, torneio)
                        for round_torneio in rounds:
                            round_torneio.save()
                        alterar_nome_rounds(torneio)
                        for partida in partidas:
                            partida.round_id = partida.round.id
                            partida.save()
                        for vitoria_por_ausencia in vitorias_por_ausencia:
                            vitoria_por_ausencia.partida_id = vitoria_por_ausencia.partida.id
                            vitoria_por_ausencia.save()
                        
                        vincular_automaticamente_jogadores_torneio_a_ladder(torneio)
                        
                        messages.success(request, Torneio.MENSAGEM_SUCESSO_CRIACAO_TORNEIO)
                        
                        return redirect(reverse('torneios:editar_torneio', kwargs={'torneio_id': torneio.id}))
                        
                except Exception as e:
                    messages.error(request, str(e))
            else:
                raise ValueError(Torneio.MENSAGEM_ERRO_SITE_INVALIDO)
            
        else:
            for erro in form_criar_torneio.non_field_errors():
                messages.error(request, erro)
    
    else:
        form_criar_torneio = CriarTorneioForm()
    
    return render(request, 'torneios/criar_torneio.html', {'opcoes_site': Torneio.OPCOES_SITE, 'form_criar_torneio': form_criar_torneio})
    
def detalhar_torneio(request, torneio_id):
    """Detalha um torneio"""
    torneio = get_object_or_404(Torneio.objects.select_related('adicionado_por'), id=torneio_id)
    
    torneio.top_3 = JogadorTorneio.objects.filter(torneio=torneio, posicao_final__lte=3).order_by('posicao_final').select_related('time')
    
    torneio.partidas = Partida.objects.filter(round__torneio=torneio).order_by('round') \
        .select_related('jogador_1__time', 'jogador_2__time', 'round', 'ganhador')[:5]
    
    torneio.qtd_jogadores = JogadorTorneio.objects.filter(torneio=torneio, valido=True).count()
    
    return render(request, 'torneios/detalhar_torneio.html', {'torneio': torneio})

@login_required
def editar_torneio(request, torneio_id):
    """Edita um torneio"""
    # Precisa ser admin para gerar um torneio
    if not request.user.jogador.admin:
        raise PermissionDenied
    
    if request.is_ajax():
        # Verificar se foi alterado um jogador
        if request.POST.get('form-jogador'):
            instance = JogadorTorneio.objects.get(id=request.POST.get('form-jogador'))
            form_jogador = JogadorTorneioForm(request.POST, instance=instance,
                                              prefix=f'{instance.id}')
            if form_jogador.is_valid():
                jogador = form_jogador.save(commit=False)
                
                jogador.save()
                
                return JsonResponse({'mensagem': 'Jogador alterado com sucesso'})
            else:
                return JsonResponse({'mensagem': form_jogador.non_field_errors(), 'erro': True})
            
        # Verificar se a alteração foi em um round
        elif request.POST.get('form-round'):
            instance = Round.objects.get(id=request.POST.get('form-round'))
            form_round = RoundForm(request.POST, instance=instance, prefix=f'{instance.id}')
            if form_round.is_valid():
                round_torneio = form_round.save(commit=False)
                
                round_torneio.save()
                
                return JsonResponse({'mensagem': 'Round alterado com sucesso'})
            else:
                return JsonResponse({'mensagem': form_round.non_field_errors(), 'erro': True})
    else:
        torneio = get_object_or_404(Torneio, id=torneio_id)
        
        forms_jogador = list()
        for jogador in JogadorTorneio.objects.filter(torneio=torneio).order_by('seed'):
            forms_jogador.append(JogadorTorneioForm(instance=jogador, prefix=f'{jogador.id}'))
        
        # Adicionar rounds ordenando por número absoluto 
        forms_round = list()
        rounds = list()
        for round_torneio in Round.objects.filter(torneio=torneio):
            rounds.append(round_torneio)
            
        for round_torneio in sorted(rounds, key=lambda x: abs(x.indice)):
            forms_round.append(RoundForm(instance=round_torneio))
        
    return render(request, 'torneios/editar_torneio.html', {'torneio': torneio, 'forms_jogador': forms_jogador, 'forms_round': forms_round})

def listar_torneios(request):
    """Lista torneios cadastrados"""
    torneios = Torneio.objects.all().order_by('data')
    
    return render(request, 'torneios/listar_torneios.html', {'torneios': torneios})

def detalhar_partida(request, torneio_id, partida_id):
    """Detalha uma partida"""
    partida = get_object_or_404(Partida.objects.select_related('jogador_1', 'jogador_2', 'round__torneio'), id=partida_id)
    
    
    return render(request, 'torneios/detalhar_partida.html', {'partida': partida})

def listar_partidas(request, torneio_id):
    """Lista partidas cadastrados"""
    torneio = get_object_or_404(Torneio, id=torneio_id)
    partidas = Partida.objects.filter(round__torneio__id=torneio_id)
    
    return render(request, 'torneios/listar_partidas.html', {'torneio': torneio, 'partidas': partidas})

def detalhar_jogador(request, torneio_id, jogador_id):
    """Detalha um jogador de um torneio"""
    jogador = get_object_or_404(JogadorTorneio.objects.select_related('jogador__user'), id=jogador_id)
    partidas = Partida.objects.filter(Q(jogador_1=jogador) | Q(jogador_2=jogador), round__torneio=jogador.torneio) \
        .select_related('jogador_1__time', 'jogador_2__time', 'round', 'ganhador')
    jogador.qtd_partidas = len(partidas)
    
    # Verificar se jogador possui outros torneios
    if jogador.jogador:
        # Precisa estar vinculado a um jogador da ladder
        jogador.outros_torneios = JogadorTorneio.objects.filter(jogador=jogador.jogador).exclude(torneio__id=torneio_id) \
            .select_related('torneio')
    
    return render(request, 'torneios/detalhar_jogador.html', {'jogador': jogador, 'partidas': partidas})

@login_required
def editar_jogador(request, torneio_id, jogador_id):
    """Detalha um jogador de um torneio"""
    if not request.user.jogador.admin:
        raise PermissionDenied
    
    jogador = get_object_or_404(JogadorTorneio, id=jogador_id)
    
    if request.POST:
        form_jogador = JogadorTorneioForm(request.POST, instance=jogador)
        if form_jogador.is_valid():
            try:
                with transaction.atomic():
                    jogador = form_jogador.save(commit=False)
                    
                    jogador.save()
                    
                    return redirect(reverse('torneios:detalhar_jogador_torneio', kwargs={'torneio_id': torneio_id,
                                                                                         'jogador_id': jogador.id}))
            except Exception as e:
                messages.error(request, str(e))
        else:
            for erro in form_jogador.non_field_errors():
                messages.error(request, erro)
            
    else:
        form_jogador = JogadorTorneioForm(instance=jogador)
    
    return render(request, 'torneios/editar_jogador.html', {'form_jogador': form_jogador})

def listar_jogadores(request, torneio_id):
    """Lista jogadores de um torneio"""
    torneio = get_object_or_404(Torneio, id=torneio_id)
    jogadores = JogadorTorneio.objects.filter(torneio__id=torneio_id).order_by('posicao_final')
    
    return render(request, 'torneios/listar_jogadores.html', {'jogadores': jogadores, 'torneio': torneio})

def analises_por_jogador(request):
    """Mostrar análises de resultado em torneios por jogador"""
    jogadores = Jogador.objects.filter(jogadortorneio__isnull=False, jogadortorneio__valido=True).order_by('nick').distinct()
    return render(request, 'torneios/analises_por_jogador.html', {'jogadores': jogadores})
                             
def analise_resultado_torneio_para_um_jogador(request):
    """Retorna dados sobre resultados em torneios de um jogador"""
    if request.is_ajax():
        jogador_id = int(request.GET.get('jogador_id'))
        
        # Verificar se jogador existe
        jogador = get_object_or_404(Jogador, id=jogador_id)
        
        dados_jogador = list(JogadorTorneio.objects.filter(valido=True, jogador=jogador).order_by('torneio__data') \
            .values('posicao_final', 'torneio__data', 'torneio'))
        dados_torneios = Torneio.objects.filter(id__in=[dado['torneio'] for dado in dados_jogador]) \
            .annotate(qtd_jogadores=Count(Case(When(jogadortorneio__valido=True, then=1)))) \
            .values('id', 'qtd_jogadores')
        
        for dado_jogador in dados_jogador:
            for dado_torneio in dados_torneios:
                if dado_jogador['torneio'] == dado_torneio['id']:
                    dado_jogador['qtd_jogadores'] = dado_torneio['qtd_jogadores']
                    break
        
        return JsonResponse({'data': [dado['torneio__data'] for dado in dados_jogador], 
                             'posicao': [dado['posicao_final'] for dado in dados_jogador], 
                             'qtd_jogadores': [dado['qtd_jogadores'] for dado in dados_jogador]})
