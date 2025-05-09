#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
CCB Alerta Bot - Bot do Telegram para gerenciamento de casas de oração
"""

import logging
import os
from datetime import datetime
from telegram.ext import Application
from config import TOKEN, inicializar_sistema, verificar_diretorios
from handlers.commands import registrar_comandos_basicos
from handlers.cadastro import registrar_handlers_cadastro
from handlers.admin import registrar_handlers_admin
from handlers.mensagens import registrar_handlers_mensagens
from handlers.error import registrar_error_handler

# Configurar logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger("CCB-Alerta-Bot")

def configurar_logs():
    """Configura pasta e arquivos de log"""
    # Criar pasta de logs se não existir
    if not os.path.exists("logs"):
        os.makedirs("logs")
    
    # Adicionar log para arquivo
    data_atual = datetime.now().strftime("%Y%m%d")
    file_handler = logging.FileHandler(f"logs/bot_{data_atual}.log")
    file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    
    logger.addHandler(file_handler)
    
    logger.info("Sistema de logs configurado")

def main():
    """Função principal para iniciar o bot"""
    logger.info("=" * 50)
    logger.info("Inicializando o CCB Alerta Bot...")
    logger.info("=" * 50)
    
    # Configurar sistema de logs
    configurar_logs()
    
    # Garantir que os diretórios existam
    verificar_diretorios()
    
    # Inicializar sistema (planilha, carregar administradores, etc.)
    inicializar_sistema()
    
    try:
        # Criar a aplicação
        application = Application.builder().token(TOKEN).build()
        
        # Configurações específicas para evitar conflitos de polling
        allowed_updates = ["message", "callback_query", "edited_message"]
        
        # Registrar handlers
        registrar_comandos_basicos(application)
        registrar_handlers_cadastro(application)
        registrar_handlers_admin(application)
        registrar_handlers_mensagens(application)
        registrar_error_handler(application)
        
        # Iniciar o bot com configurações ajustadas
        logger.info("Bot iniciado! Pressione Ctrl+C para parar.")
        
        # Configuração ajustada para evitar conflitos, compatível com versão atual
        application.run_polling(
            drop_pending_updates=True,     # Descarta atualizações pendentes
            allowed_updates=allowed_updates,  # Limita tipos de atualizações
            poll_interval=1.0              # Intervalo maior entre polls
        )
    except Exception as e:
        logger.error(f"Erro fatal ao iniciar o bot: {e}")
        raise
        
if __name__ == "__main__":
    main()
