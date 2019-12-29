# -*- coding: utf-8 -*-
"""Testa utils de Seasons"""

from django.test.testcases import TestCase
from django.urls.base import reverse

from smashLadder.management.commands.gerar_season import iniciar_lockdown, \
    encerrar_lockdown


class IniciarLockdownTestCase(TestCase):
    def testa_acesso_apos_lockdown(self):
        """Testa acesso a tela inicial durante lockdown"""
        response = self.client.get(reverse('inicio'))
        self.assertEqual(response.status_code, 200)
        iniciar_lockdown()
        response = self.client.get(reverse('inicio'))
        self.assertEqual(response.status_code, 404)

class EncerrarLockdownTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        super(EncerrarLockdownTestCase, cls).setUpTestData()
        
        iniciar_lockdown()
        
    def testa_acesso_apos_encerrar_lockdown(self):
        """Testa acesso a tela inicial durante lockdown"""
        response = self.client.get(reverse('inicio'))
        self.assertEqual(response.status_code, 404)
        encerrar_lockdown()
        response = self.client.get(reverse('inicio'))
        self.assertEqual(response.status_code, 200)