#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
CCB Alerta Bot - VERSÃO SIMPLIFICADA E FUNCIONAL
"""

import logging
import os
from datetime import datetime
from telegram import Update
from telegram.ext import Application
from config import (
    TOKEN, WEBHOOK_CONFIG, PRODUCTION_CONFIG, 
    inicializar_sistema, verificar_diretorios
)
from handlers.commands import registrar_comandos_basicos
from handlers.cadastro import registrar_handlers_cadastro
from handlers.admin import registrar_handlers_admin
from handlers.mensagens import registrar_handlers_mensagens
from handlers.error import registrar_error_handler
from handlers.lgpd import registrar_handlers_lgpd

# Configurar logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger("CCB-Alerta-Bot")

def configurar_logs():
    """Configura pasta e arquivos de log"""
    if not os.path.exists("logs"):
        os.makedirs("logs")
    
    data_atual = datetime.now().strftime("%Y%m%d")
    file_handler = logging.FileHandler(f"logs/bot_{data_atual}.log")
    file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    
    logger.addHandler(file_handler)
    logger.info("Sistema de logs configurado")

def main():
    """Função principal - MODO SIMPLES"""
    logger.info("=" * 50)
    logger.info("Inicializando o CCB Alerta Bot...")
    logger.info("=" * 50)
    
    # Configurar sistema de logs
    configurar_logs()
    
    # Garantir que os diretórios existam
    verificar_diretorios()
    
    # Inicializar sistema
    inicializar_sistema()
    
    try:
        # Criar a aplicação
        application = Application.builder().token(TOKEN).build()
        
        # Registrar handlers
        registrar_comandos_basicos(application)
        registrar_handlers_admin(application)
        registrar_handlers_lgpd(application)
        registrar_handlers_cadastro(application)     # ← MOVER PARA PENÚLTIMO
        registrar_handlers_mensagens(application)    # ← DEIXAR POR ÚLTIMO
        registrar_error_handler(application)
        
        # FORÇAR MODO WEBHOOK SIMPLES
        if WEBHOOK_CONFIG['usar_webhook']:
            logger.info("Modo WEBHOOK SIMPLES")
            
            # Usar o webhook built-in do python-telegram-bot
            application.run_webhook(
                listen="0.0.0.0",
                port=WEBHOOK_CONFIG['porta'],
                webhook_url=WEBHOOK_CONFIG['webhook_url'],
                allowed_updates=PRODUCTION_CONFIG['allowed_updates'],
                drop_pending_updates=PRODUCTION_CONFIG['drop_pending_updates']
            )
        else:
            logger.info("Modo POLLING")
            # Usar polling
            application.run_polling(
                drop_pending_updates=PRODUCTION_CONFIG['drop_pending_updates'],
                allowed_updates=PRODUCTION_CONFIG['allowed_updates'],
                poll_interval=1.0
            )
            
    except Exception as e:
        logger.error(f"Erro fatal ao iniciar o bot: {e}")
        raise
        
if __name__ == "__main__":
    main()
