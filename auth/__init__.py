#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
📁 ARQUIVO: auth/__init__.py
💾 ONDE SALVAR: ccb-alerta-bot/auth/__init__.py
📦 FUNÇÃO: Inicializador do módulo de autenticação
🔧 DESCRIÇÃO: Centraliza acesso aos módulos de autenticação Microsoft
👨‍💼 ADAPTADO PARA: CCB Alerta Bot
"""

from .microsoft_auth import MicrosoftAuth

__version__ = "1.0.0"
__author__ = "Adaptado para CCB Alerta Bot"
__all__ = ["MicrosoftAuth"]
