#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
CCB Alerta Bot - VERSÃO CORRIGIDA
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
from handlers.cadastro import registrar_handlers_cadastro, registrar_teste_emergencial
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
    """Função principal - VERSÃO CORRIGIDA"""
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
        
        # TESTE EMERGENCIAL - PRIORIDADE MÁXIMA
        registrar_teste_emergencial(application)
        logger.info("🔥 TESTE EMERGENCIAL ATIVO")
        
        # Registrar handlers na ordem correta
        registrar_comandos_basicos(application)
        logger.info("1️⃣ Comandos básicos registrados")

        registrar_handlers_admin(application)
        logger.info("2️⃣ Handlers admin registrados")

        registrar_handlers_lgpd(application)
        logger.info("3️⃣ Handlers LGPD registrados")

        registrar_handlers_cadastro(application)
        logger.info("4️⃣ Handlers cadastro registrados - PRIORIDADE")

        registrar_handlers_mensagens(application)
        logger.info("5️⃣ Handlers mensagens registrados - ÚLTIMO")

        registrar_error_handler(application)
        logger.info("6️⃣ Error handler registrado")
        
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
