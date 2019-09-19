# -*- coding: utf-8 -*-
from django.contrib.auth.models import User, Permission, Group
from django.core.management.base import BaseCommand
from django.db import transaction

permissoes_admins = [
    'Can view', 
    'Can add user', 'Can change user', 
    'Can add jogador', 'Can change jogador',
    'Can add registro ferias', 'Can change registro ferias']

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
                    for permissao_admin in permissoes_admins:
                        if permissao_admin in permissao.name:
                            grupo_admins.permissions.add(permissao)
                            break
                            
                    else:
                        if grupo_admins.permissions.filter(id=permissao.id).exists():
                            grupo_admins.permissions.remove(permissao)
                grupo_admins.save()
                
        except:
            raise
        