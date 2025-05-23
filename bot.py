#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
CCB Alerta Bot - Bot do Telegram para gerenciamento de casas de oração
VERSÃO CORRIGIDA: Suporte automático a webhook/polling
"""

import logging
import os
import asyncio
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

# Importações para servidor web (webhook)
try:
    from flask import Flask, request, jsonify
    FLASK_DISPONIVEL = True
except ImportError:
    FLASK_DISPONIVEL = False
    logging.warning("Flask não disponível. Webhook não funcionará.")

# Configurar logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger("CCB-Alerta-Bot")

# Variáveis globais
app_telegram = None
flask_app = None

def configurar_logs():
    """Configura pasta e arquivos de log (MANTIDO)"""
    # Criar pasta de logs se não existir
    if not os.path.exists("logs"):
        os.makedirs("logs")
    
    # Adicionar log para arquivo
    data_atual = datetime.now().strftime("%Y%m%d")
    file_handler = logging.FileHandler(f"logs/bot_{data_atual}.log")
    file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    
    logger.addHandler(file_handler)
    logger.info("Sistema de logs configurado")

def criar_servidor_webhook():
    """Cria servidor Flask para receber webhooks"""
    if not FLASK_DISPONIVEL:
        logger.error("Flask não está disponível. Instale com: pip install flask")
        return None
    
    global flask_app
    flask_app = Flask(__name__)
    
    @flask_app.route('/webhook', methods=['POST'])
    async def webhook():
        """Endpoint para receber updates via webhook"""
        try:
            # Obter dados do request
            json_data = request.get_json()
            
            if not json_data:
                logger.warning("Webhook recebido sem dados JSON")
                return jsonify({'status': 'error', 'message': 'No JSON data'}), 400
            
            # Converter para objeto Update do Telegram
            update = Update.de_json(json_data, app_telegram.bot)
            
            # Processar update
            await app_telegram.process_update(update)
            
            logger.debug(f"Webhook processado: {update.update_id}")
            return jsonify({'status': 'ok'}), 200
            
        except Exception as e:
            logger.error(f"Erro ao processar webhook: {e}")
            return jsonify({'status': 'error', 'message': str(e)}), 500
    
    @flask_app.route('/health', methods=['GET'])
    def health_check():
        """Endpoint para verificação de saúde do serviço"""
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'bot_username': app_telegram.bot.username if app_telegram else 'N/A'
        }), 200
    
    @flask_app.route('/', methods=['GET'])
    def home():
        """Endpoint raiz com informações básicas"""
        return jsonify({
            'service': 'CCB Alerta Bot',
            'status': 'running',
            'mode': 'webhook',
            'timestamp': datetime.now().isoformat()
        }), 200
    
    return flask_app

async def configurar_webhook(application):
    """Configura o webhook do bot"""
    try:
        webhook_url = WEBHOOK_CONFIG['webhook_url']
        
        if not webhook_url:
            logger.error("URL do webhook não configurada")
            return False
        
        # Deletar webhook existente (limpar conflitos)
        logger.info("Limpando webhook anterior...")
        await application.bot.delete_webhook(drop_pending_updates=True)
        
        # Aguardar um pouco para garantir que foi limpo
        await asyncio.sleep(2)
        
        # Configurar novo webhook
        logger.info(f"Configurando webhook: {webhook_url}")
        success = await application.bot.set_webhook(
            url=webhook_url,
            allowed_updates=PRODUCTION_CONFIG['allowed_updates'],
            drop_pending_updates=PRODUCTION_CONFIG['drop_pending_updates']
        )
        
        if success:
            logger.info("Webhook configurado com sucesso")
            
            # Verificar se o webhook foi configurado
            webhook_info = await application.bot.get_webhook_info()
            logger.info(f"Webhook ativo: {webhook_info.url}")
            logger.info(f"Pending updates: {webhook_info.pending_update_count}")
            
            return True
        else:
            logger.error("Falha ao configurar webhook")
            return False
            
    except Exception as e:
        logger.error(f"Erro ao configurar webhook: {e}")
        return False

async def limpar_webhook(application):
    """Remove webhook para usar polling"""
    try:
        logger.info("Removendo webhook para usar polling...")
        await application.bot.delete_webhook(drop_pending_updates=True)
        
        # Aguardar um pouco para garantir que foi limpo
        await asyncio.sleep(2)
        
        # Verificar se foi removido
        webhook_info = await application.bot.get_webhook_info()
        if not webhook_info.url:
            logger.info("Webhook removido com sucesso")
            return True
        else:
            logger.warning(f"Webhook ainda ativo: {webhook_info.url}")
            return False
            
    except Exception as e:
        logger.error(f"Erro ao limpar webhook: {e}")
        return False

def executar_modo_webhook():
    """Executa o bot em modo webhook"""
    global app_telegram, flask_app
    
    try:
        # Criar servidor Flask
        flask_app = criar_servidor_webhook()
        if not flask_app:
            logger.error("Falha ao criar servidor webhook")
            return False
        
        # Configurar webhook (async)
        async def setup_webhook():
            webhook_ok = await configurar_webhook(app_telegram)
            if not webhook_ok:
                logger.error("Falha ao configurar webhook")
                return False
            return True
        
        # Executar configuração do webhook
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        webhook_configured = loop.run_until_complete(setup_webhook())
        
        if not webhook_configured:
            return False
        
        # Iniciar servidor Flask
        logger.info(f"Iniciando servidor webhook na porta {WEBHOOK_CONFIG['porta']}")
        flask_app.run(
            host=WEBHOOK_CONFIG['host'],
            port=WEBHOOK_CONFIG['porta'],
            debug=False,
            use_reloader=False
        )
        
        return True
        
    except Exception as e:
        logger.error(f"Erro no modo webhook: {e}")
        return False

async def executar_modo_polling():
    """Executa o bot em modo polling"""
    try:
        # Limpar webhook se existir
        await limpar_webhook(app_telegram)
        
        # Iniciar polling
        logger.info("Iniciando bot em modo polling...")
        await app_telegram.run_polling(
            drop_pending_updates=PRODUCTION_CONFIG['drop_pending_updates'],
            allowed_updates=PRODUCTION_CONFIG['allowed_updates'],
            poll_interval=1.0
        )
        
        return True
        
    except Exception as e:
        logger.error(f"Erro no modo polling: {e}")
        return False

def main():
    """Função principal para iniciar o bot (ATUALIZADA)"""
    global app_telegram
    
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
        app_telegram = Application.builder().token(TOKEN).build()
        
        # Registrar handlers (MANTIDO)
        registrar_comandos_basicos(app_telegram)
        registrar_handlers_cadastro(app_telegram)
        registrar_handlers_admin(app_telegram)
        registrar_handlers_mensagens(app_telegram)
        registrar_handlers_lgpd(app_telegram)
        registrar_error_handler(app_telegram)
        
        # Decidir modo de execução baseado na configuração
        if WEBHOOK_CONFIG['usar_webhook']:
            logger.info("Modo WEBHOOK detectado")
            
            if not FLASK_DISPONIVEL:
                logger.error("Flask não disponível para webhook. Instale com: pip install flask")
                logger.info("Tentando usar polling como fallback...")
                
                # Fallback para polling
                asyncio.run(executar_modo_polling())
            else:
                # Usar webhook
                executar_modo_webhook()
        else:
            logger.info("Modo POLLING detectado")
            
            # Usar polling
            asyncio.run(executar_modo_polling())
            
    except Exception as e:
        logger.error(f"Erro fatal ao iniciar o bot: {e}")
        raise
        
if __name__ == "__main__":
    main()
