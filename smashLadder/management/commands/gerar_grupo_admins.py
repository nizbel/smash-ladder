# -*- coding: utf-8 -*-
from django.contrib.auth.models import User, Permission, Group
from django.core.management.base import BaseCommand
from django.db import transaction


class Command(BaseCommand):
    help = 'Gera grupo inicial de admins'

    def add_arguments(self, parser):
        parser.add_argument('--desafios', action='store_true')
        
    def handle(self, *args, **options):
        try:
            with transaction.atomic():
                # Gera grupo de admin caso não exista
                grupo_admins, _ = Group.objects.get_or_create(name='Admins')
            
                # Varre permissões para dar apenas permissões de visualizar
                for permissao in Permission.objects.all():
                    if 'Can view' in permissao.name:
                        grupo_admins.permissions.add(permissao)
                    elif 'Can add user' in permissao.name:
                        grupo_admins.permissions.add(permissao)
                    elif 'Can add jogador' in permissao.name:
                        grupo_admins.permissions.add(permissao)
                    elif 'Can add registro ferias' in permissao.name:
                        grupo_admins.permissions.add(permissao)
                    elif 'Can change registro ferias' in permissao.name:
                        grupo_admins.permissions.add(permissao)
                    else:
                        if grupo_admins.permissions.filter(permissao).exists():
                            grupo_admins.permissions.remove(permissao)
                grupo_admins.save()
                
        except:
            raise
        