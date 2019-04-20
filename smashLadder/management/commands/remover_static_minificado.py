# -*- encoding: utf-8 -*-
from os import walk
import os

from django.core.management.base import BaseCommand

from smashLadder import settings


class Command(BaseCommand):
    help = 'Remove CSS e JS que tiver sido minificado'

    def add_arguments(self, parser):
        parser.add_argument('-r', action='store_true')
        
    def handle(self, *args, **options):
        arqs = []
        for (dirpath, _, arq_nomes) in walk(settings.BASE_DIR + 'smashLadder/static'):
            arqs.extend(['%s/%s' % (dirpath, arq_nome) for arq_nome in arq_nomes if arq_nome[-3:] == 'css' or arq_nome[-2:] == 'js'])
        
        removidos = 0
        for arq_nome in [arq_nao_min for arq_nao_min in arqs if '.min.css' not in arq_nao_min and '.min.js' not in arq_nao_min]:
            nome, ext = os.path.splitext(arq_nome)
            if (nome + '.min' + ext) in arqs:
                if options['r']:
                    os.remove(arq_nome)
                else:
                    print('Removido', arq_nome)
                removidos += 1
        
        print(f'{removidos} arquivo(s) removidos')