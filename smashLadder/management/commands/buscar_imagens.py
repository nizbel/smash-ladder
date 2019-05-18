# -*- coding: utf-8 -*-
import os
import re
import urllib.request

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
                for personagem in Personagem.objects.all():
                    nome_arquivo = (personagem.nome + 'Imagem.png')
                    if os.path.isfile(settings.BASE_DIR + \
                                      '/smashLadder/static/img/personagens/' + nome_arquivo):
                        personagem.imagem = PASTA_IMAGENS + 'personagens/' + nome_arquivo
                        personagem.save()
                        
                    # Buscar imagens apenas em desenvolvimento
                    elif settings.DEBUG:
                        print(personagem.nome)
                        nome_formatado = personagem.nome.replace(' ', '_')
                        
                        url = f'https://www.ssbwiki.com/File:{nome_formatado}_SSBU.png'
    
                        fp = urllib.request.urlopen(url)
                        url_bytes = fp.read()
                    
                        html = url_bytes.decode("utf8")
                        fp.close()
                        
                        imagem_url = re.findall(r'src="/images/thumb/[^"]+SSBU\.png"', html)[0]
                        print(imagem_url)
                        
                        url_formatada = imagem_url.replace('src=', '').replace('"', '')
                        print(url_formatada)
                         
                        nome_arquivo = (personagem.nome + 'Imagem.png')
                         
                        urllib.request.urlretrieve('https://www.ssbwiki.com' + url_formatada, settings.BASE_DIR + \
                                                   '/smashLadder/static/img/personagens/' + nome_arquivo)

                
        except:
            raise
        