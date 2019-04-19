# -*- coding: utf-8 -*-
from smashLadder import settings


def nome_site(context):
    return {'NOME_SITE': settings.NOME_SITE}

def prod(context):
    return {'PROD': (not settings.DEBUG)}