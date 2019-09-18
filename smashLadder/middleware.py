# -*- coding: utf-8 -*-
from django.utils import timezone

from performance.models import PerformanceRequisicao


class PerformanceMiddleware(object):
    def __init__(self, get_response):
        self.get_response = get_response
        # One-time configuration and initialization.

    def __call__(self, request):
        data_hora_requisicao = timezone.localtime()
        
        response = self.get_response(request)
        
        # Se não houve erro, guardar performance
        if response.status_code < 400:
            user = None
            if not request.user.is_anonymous:
                user = request.user
    
            data_hora_resposta = timezone.localtime()
            
            performance = PerformanceRequisicao(data_hora_requisicao=data_hora_requisicao, data_hora_resposta=data_hora_resposta,
                                                url=request.path, user=user)
            performance.save()
        
        return response