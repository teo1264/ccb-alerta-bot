#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Configurações globais para o CCB Alerta Bot
Adaptado para usar SQLite e disco persistente no Render
VERSÃO SEGURA: Token apenas via variável de ambiente
"""
import os
import sys
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
    
    # FORÇAR POLLING se variável estiver definida
    if os.environ.get('FORCE_POLLING'):
        logger.info("🔄 FORCE_POLLING ativado - usando polling em vez de webhook")
        return ambiente
    
    # Detectar Render (código original)
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
    
# ==================== CONFIGURAÇÕES PRINCIPAIS (SEGURAS) ====================

# Token do Bot - APENAS variável de ambiente (SEGURO)
TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')

# Verificação obrigatória do token
if not TOKEN:
    logger.error("❌ ERRO CRÍTICO: TELEGRAM_BOT_TOKEN não configurado!")
    logger.error("Configure a variável de ambiente antes de executar o bot.")
    logger.error("No Render: Configure em Environment Variables")
    logger.error("Local: export TELEGRAM_BOT_TOKEN='seu_token_aqui'")
    sys.exit(1)

# Log de confirmação (sem mostrar o token)
logger.info("✅ Token do bot carregado da variável de ambiente")

# Detectar ambiente atual
AMBIENTE = detectar_ambiente()

# Configurações do webhook
WEBHOOK_CONFIG = {
    'usar_webhook': AMBIENTE['usar_webhook'],
    'webhook_url': AMBIENTE['webhook_url'],
    'webhook_path': '/webhook',
    'porta': AMBIENTE['porta'],
    'host': AMBIENTE['host']
}

# Log das configurações detectadas
logger.info(f"Ambiente detectado: {AMBIENTE['plataforma'].upper()}")
logger.info(f"Usar webhook: {AMBIENTE['usar_webhook']}")
if AMBIENTE['webhook_url']:
    logger.info(f"Webhook URL: {AMBIENTE['webhook_url']}")

# ==================== CONFIGURAÇÕES DE ADMINISTRADORES ====================

# IDs de administradores - também via variável de ambiente (SEGURO)
admin_ids_env = os.environ.get('ADMIN_IDS', '')
if admin_ids_env:
    try:
        ADMIN_IDS = [int(id.strip()) for id in admin_ids_env.split(',') if id.strip().isdigit()]
        logger.info(f"✅ {len(ADMIN_IDS)} administradores carregados da variável de ambiente")
    except ValueError:
        logger.warning("⚠️ Erro ao processar ADMIN_IDS. Usando lista vazia.")
        ADMIN_IDS = []
else:
    logger.warning("⚠️ ADMIN_IDS não configurado. Nenhum administrador será adicionado.")
    ADMIN_IDS = []

# ==================== CONFIGURAÇÕES DE ARMAZENAMENTO ====================

# Caminho para o disco persistente no Render
RENDER_DISK_PATH = os.environ.get("RENDER_DISK_PATH", "/opt/render/project/disk")

# Diretório de dados compartilhado
DATA_DIR = os.path.join(RENDER_DISK_PATH, "shared_data")

# Caminho para o banco de dados SQLite
DATABASE_PATH = os.path.join(DATA_DIR, "ccb_alerta_bot.db")

# Diretório temporário
TEMP_DIR = os.path.join(DATA_DIR, "temp")

# Estados para a conversa de cadastro em etapas
CODIGO, NOME, FUNCAO, CONFIRMAR = range(4)

def verificar_diretorios():
    """Garante que os diretórios necessários existam"""
    # Garantir que o diretório de dados existe
    os.makedirs(DATA_DIR, exist_ok=True)
    
    # Criar subdiretórios necessários
    os.makedirs(os.path.join(DATA_DIR, "logs"), exist_ok=True)
    os.makedirs(TEMP_DIR, exist_ok=True)
    os.makedirs(os.path.join(DATA_DIR, "backup"), exist_ok=True)
    
    logger.info(f"Diretórios verificados e criados em: {DATA_DIR}")
    logger.info(f"Banco de dados será armazenado em: {DATABASE_PATH}")

def inicializar_sistema():
    """Inicializa todos os componentes do sistema"""
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
    
    # Inicializar administradores padrão (se houver)
    if ADMIN_IDS:
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
    else:
        logger.info("Nenhum administrador configurado via ADMIN_IDS")

# ==================== CONFIGURAÇÕES ADICIONAIS ====================

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
