# -*- coding: utf-8 -*-
import os
import re
import subprocess

from django.core.mail import mail_admins
from django.core.management.base import BaseCommand
from django.db import connection
from django.template.loader import render_to_string

from conf.conf import DROPBOX_OAUTH2_TOKEN, DROPBOX_ROOT_PATH
import dropbox
from dropbox.exceptions import ApiError
from dropbox.files import WriteMode
from smashLadder import settings


class Command(BaseCommand):
    help = 'Busca tabelas atuais na base e prepara backup'

    def handle(self, *args, **options):
        preparar_backup()
        
        
def preparar_backup():
    str_tabelas = buscar_tabelas_string()
    
    arquivo_dump = 'db_dump.sh'
    arquivo_base = 'db_dump.txt'

    # Alterar db_dump.sh correspondente
    with open(arquivo_dump, 'w+') as arquivo:

        arquivo.write(render_to_string(arquivo_base, {'tabelas': str_tabelas, 'nome_db': settings.DATABASES['default']['NAME'],
                                                      'user': settings.DATABASES['default']['USER'], 
                                                      'host': settings.DATABASES['default']['HOST'], 'project_path': settings.BASE_DIR}))
        
    # Verificar se é possível chamar o db_dump por subprocess
    subprocess.call(['sh', arquivo_dump])

    os.remove(arquivo_dump)

    # Se produção, enviar backups para pasta do dropbox
    if settings.DEBUG == False:
        pattern = re.compile(r'backup-\d+-\d+-\d+-\d+')

        for (_, _, nomes_arquivo) in os.walk(DROPBOX_ROOT_PATH):
            for nome_arquivo in [nome for nome in nomes_arquivo if pattern.match(nome)]:
                backup(nome_arquivo)
                
def buscar_tabelas_string():
    cursor = connection.cursor()
    lista_tabelas = connection.introspection.get_table_list(cursor)
    lista_tabelas = [tabela.name for tabela in lista_tabelas if tabela.type == 't']
    str_lista = ['--table "public.%s"' % (tabela) for tabela in sorted(lista_tabelas)]
    str_lista = ' '.join(str_lista)
    return str_lista

def backup(file_name):
    """Envia para o Dropbox"""
    dbx = dropbox.Dropbox(DROPBOX_OAUTH2_TOKEN)
    file_path = DROPBOX_ROOT_PATH + file_name
    
    f = open(file_path, 'rb')
    file_size = os.path.getsize(file_path)
    
    CHUNK_SIZE = 4 * 1024 * 1024
    
    try:
        if file_size <= CHUNK_SIZE:
            print(dbx.files_upload(f.read(), '/smash/' + file_path, mode=WriteMode('overwrite')))
        
        else:
        
            upload_session_start_result = dbx.files_upload_session_start(f.read(CHUNK_SIZE))
            cursor = dropbox.files.UploadSessionCursor(session_id=upload_session_start_result.session_id,
                                                       offset=f.tell())
            commit = dropbox.files.CommitInfo(path=('/' + file_path), autorename=True)
        
            while f.tell() < file_size:
                if ((file_size - f.tell()) <= CHUNK_SIZE):
                    print(dbx.files_upload_session_finish(f.read(CHUNK_SIZE),
                                                    cursor,
                                                    commit))
                else:
                    dbx.files_upload_session_append(f.read(CHUNK_SIZE),
                                                    cursor.session_id,
                                                    cursor.offset)
                    cursor.offset = f.tell()
    
    except ApiError as err:
        # This checks for the specific error where a user doesn't have
        # enough Dropbox space quota to upload this file
        if (err.error.is_path() and
                err.error.get_path().reason.is_insufficient_space()):
            if settings.DEBUG:
                print(err)
            else:
                mail_admins(u'Erro em Preparar backup', 'ERROR: Cannot back up; insufficient space.')
            return
        elif err.user_message_text:
            if settings.DEBUG:
                print(err.user_message_text)
            else:
                mail_admins(u'Erro em Preparar backup', err.user_message_text)
            return
        else:
            if settings.DEBUG:
                print(err)
            else:
                mail_admins(u'Erro em Preparar backup', err)
            return
    
    
    f.close()
    # Apagar arquivo
    os.remove(file_path)
    