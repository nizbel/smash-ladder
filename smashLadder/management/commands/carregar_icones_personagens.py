# -*- coding: utf-8 -*-
import os

from django.core.management.base import BaseCommand
from django.db import transaction

from jogadores.models import Personagem
from smashLadder import settings
from smashLadder.settings import PASTA_IMAGENS


class Command(BaseCommand):
    help = 'Carrega ícones para os personagens'

    def handle(self, *args, **options):
        try:
            with transaction.atomic():
                if settings.DEBUG:
                    # Formatar imagens
                    for arquivo in [imagem for imagem in os.listdir(settings.BASE_DIR + \
                                                  '/smashLadder/static/img/') if imagem.endswith('.png')]:
                        if not arquivo.endswith('Icone.png'):
                            os.rename(settings.BASE_DIR + '/smashLadder/static/img/' + arquivo, 
                                      settings.BASE_DIR + '/smashLadder/static/img/' + arquivo[:-4] + 'Icone.png')
                    
                    # Adicionar a personagens
                    for personagem in Personagem.objects.all():
                        icone = (personagem.nome + 'Icone.png')
                        personagem.icone = PASTA_IMAGENS + icone
                        personagem.save()
                        if not os.path.isfile(settings.BASE_DIR + \
                                          '/smashLadder/static/img/' + icone):
                            print(f'{icone} não existe')
                            
                else:
                    # Adicionar a personagens
                    for personagem in Personagem.objects.all():
                        personagem.icone = PASTA_IMAGENS + personagem.nome + 'Icone.png'
                        personagem.save()
                
        except:
            raise
        