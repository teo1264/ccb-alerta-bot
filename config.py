#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Configurações globais para o CCB Alerta Bot
Adaptado para usar SQLite e disco persistente no Render
VERSÃO CORRIGIDA: Webhook/Polling automático + configurações existentes
"""
import os
import logging

# Configurar o log
logger = logging.getLogger("CCB-Alerta-Bot")

# ==================== DETECÇÃO DE AMBIENTE ====================

def detectar_ambiente():
    """
    Detecta se está rodando no Render ou localmente
    
    Returns:
        dict: Informações do ambiente detectado
    """
    ambiente = {
        'plataforma': 'local',
        'usar_webhook': False,
        'porta': 8000,
        'host': '0.0.0.0',
        'url_base': None,
        'webhook_url': None
    }
    
    # Detectar Render
    if os.environ.get('RENDER'):
        ambiente['plataforma'] = 'render'
        ambiente['usar_webhook'] = True
        
        # Porta fornecida pelo Render
        ambiente['porta'] = int(os.environ.get('PORT', 10000))
        
        # URL base do serviço no Render
        render_service_name = os.environ.get('RENDER_SERVICE_NAME')
        if render_service_name:
            ambiente['url_base'] = f"https://{render_service_name}.onrender.com"
            ambiente['webhook_url'] = f"{ambiente['url_base']}/webhook"
    
    # Verificar se URL foi fornecida manualmente
    webhook_url_manual = os.environ.get('WEBHOOK_URL')
    if webhook_url_manual:
        ambiente['usar_webhook'] = True
        ambiente['webhook_url'] = webhook_url_manual
        ambiente['url_base'] = webhook_url_manual.replace('/webhook', '')
    
    return ambiente

# ==================== CONFIGURAÇÕES PRINCIPAIS (SUAS) ====================

# Token do Bot (MANTENDO SEU TOKEN + variável de ambiente)
TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN', "7773179413:AAHqJp-NBPPs6YrSV1kB5-q4vkV3tjDFyy4")

# Detectar ambiente atual (NOVO)
AMBIENTE = detectar_ambiente()

# Configurações do webhook (NOVO)
WEBHOOK_CONFIG = {
    'usar_webhook': AMBIENTE['usar_webhook'],
    'webhook_url': AMBIENTE['webhook_url'],
    'webhook_path': '/webhook',
    'porta': AMBIENTE['porta'],
    'host': AMBIENTE['host']
}

# Log das configurações detectadas (NOVO)
logger.info(f"Ambiente detectado: {AMBIENTE['plataforma'].upper()}")
logger.info(f"Usar webhook: {AMBIENTE['usar_webhook']}")
if AMBIENTE['webhook_url']:
    logger.info(f"Webhook URL: {AMBIENTE['webhook_url']}")

# ==================== SUAS CONFIGURAÇÕES ORIGINAIS ====================

# Caminho para o disco persistente no Render (MANTIDO)
RENDER_DISK_PATH = os.environ.get("RENDER_DISK_PATH", "/opt/render/project/disk")

# Diretório de dados compartilhado (MANTIDO)
DATA_DIR = os.path.join(RENDER_DISK_PATH, "shared_data")

# Caminho para o banco de dados SQLite (MANTIDO)
DATABASE_PATH = os.path.join(DATA_DIR, "ccb_alerta_bot.db")

# IDs de administradores (MANTIDO)
ADMIN_IDS = [5876346562]  # Adicione aqui os IDs dos administradores

# Diretório temporário (MANTIDO)
TEMP_DIR = os.path.join(DATA_DIR, "temp")

# Estados para a conversa de cadastro em etapas (MANTIDO)
CODIGO, NOME, FUNCAO, CONFIRMAR = range(4)

def verificar_diretorios():
    """Garante que os diretórios necessários existam (MANTIDO)"""
    # Garantir que o diretório de dados existe
    os.makedirs(DATA_DIR, exist_ok=True)
    
    # Criar subdiretórios necessários
    os.makedirs(os.path.join(DATA_DIR, "logs"), exist_ok=True)
    os.makedirs(TEMP_DIR, exist_ok=True)
    os.makedirs(os.path.join(DATA_DIR, "backup"), exist_ok=True)
    
    logger.info(f"Diretórios verificados e criados em: {DATA_DIR}")
    logger.info(f"Banco de dados será armazenado em: {DATABASE_PATH}")

def inicializar_sistema():
    """Inicializa todos os componentes do sistema (MANTIDO + melhorado)"""
    global ADMIN_IDS
    
    # Garantir que os diretórios existam antes de inicializar
    verificar_diretorios()  
    
    # Importamos aqui para evitar importação circular
    from utils.database import init_database, listar_admins, inicializar_admins_padrao
    
    # Inicializar banco de dados SQLite
    logger.info("Inicializando banco de dados SQLite...")
    if init_database():
        logger.info(f"Banco de dados inicializado com sucesso em {DATABASE_PATH}")
    else:
        logger.error(f"Falha ao inicializar banco de dados em {DATABASE_PATH}")
    
    # Inicializar administradores padrão
    logger.info("Configurando administradores...")
    try:
        count = inicializar_admins_padrao(ADMIN_IDS)
        logger.info(f"{count} administradores padrão configurados")
    
        # Carregar lista atual de administradores
        admins = listar_admins()
        if admins:
            ADMIN_IDS = admins
            logger.info(f"Total de administradores: {len(ADMIN_IDS)}")
        else:
            logger.warning("Não foi possível carregar administradores do banco de dados")
    except Exception as e:
        logger.error(f"Erro ao configurar administradores: {str(e)}")

# ==================== CONFIGURAÇÕES ADICIONAIS (NOVO) ====================

# Configurações para produção
PRODUCTION_CONFIG = {
    'allowed_updates': ["message", "callback_query", "edited_message"],
    'drop_pending_updates': True,
    'read_timeout': 30,
    'write_timeout': 30,
    'connect_timeout': 30,
    'pool_timeout': 30
}

logger.info("Configurações carregadas com sucesso")
