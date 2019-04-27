# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand
from django.db import transaction

from jogadores.models import Personagem
from smashLadder.settings import PASTA_IMAGENS


class Command(BaseCommand):
    help = 'Carrega ícones para os personagens'

    def handle(self, *args, **options):
        try:
            with transaction.atomic():
                for personagem in Personagem.objects.all():
                    personagem.icone = PASTA_IMAGENS + personagem.nome + 'Icone.png'
                    personagem.save()
                
        except:
            raise
        