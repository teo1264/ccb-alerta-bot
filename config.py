#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Configurações globais para o CCB Alerta Bot
ATUALIZADO: Suporte a OneDrive compartilhado + fallback local
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

# ==================== CONFIGURAÇÕES ONEDRIVE (NOVAS) ====================

# Configurações Microsoft para OneDrive
MICROSOFT_CLIENT_ID = os.environ.get('MICROSOFT_CLIENT_ID')
MICROSOFT_TENANT_ID = os.environ.get('MICROSOFT_TENANT_ID', 'consumers')

# ID da pasta 'Alerta' no OneDrive (opcional - será descoberto automaticamente)
ONEDRIVE_ALERTA_ID = os.environ.get('ONEDRIVE_ALERTA_ID')

# Feature flags para OneDrive
ONEDRIVE_DATABASE_ENABLED = os.environ.get('ONEDRIVE_DATABASE_ENABLED', 'false').lower() == 'true'

# Log das configurações OneDrive
if MICROSOFT_CLIENT_ID:
    logger.info("✅ Microsoft Client ID configurado")
    logger.info(f"   Tenant: {MICROSOFT_TENANT_ID}")
    logger.info(f"   OneDrive Database: {'✅ Habilitado' if ONEDRIVE_DATABASE_ENABLED else '❌ Desabilitado'}")
    if ONEDRIVE_ALERTA_ID:
        logger.info(f"   Pasta Alerta ID: Configurado")
    else:
        logger.info("   Pasta Alerta ID: Será descoberto automaticamente")
else:
    logger.info("📁 Microsoft Client ID não configurado - usando storage local")

# ==================== CONFIGURAÇÕES DE ARMAZENAMENTO ====================

# Caminho para o disco persistente no Render
RENDER_DISK_PATH = os.environ.get("RENDER_DISK_PATH", "/opt/render/project/disk")

# Diretório de dados compartilhado (fallback local)
DATA_DIR = os.path.join(RENDER_DISK_PATH, "shared_data")

# Caminho para o banco de dados SQLite (será determinado dinamicamente)
# A função get_db_path() no database.py decidirá se usa OneDrive ou local
DATABASE_PATH = None  # Será determinado dinamicamente

# Diretório temporário
TEMP_DIR = os.path.join(DATA_DIR, "temp")

# Estados para a conversa de cadastro em etapas
CODIGO, NOME, FUNCAO, CONFIRMAR = range(4)

def verificar_diretorios():
    """Garante que os diretórios necessários existam (fallback local)"""
    # Garantir que o diretório de dados existe
    os.makedirs(DATA_DIR, exist_ok=True)
    
    # Criar subdiretórios necessários
    os.makedirs(os.path.join(DATA_DIR, "logs"), exist_ok=True)
    os.makedirs(TEMP_DIR, exist_ok=True)
    os.makedirs(os.path.join(DATA_DIR, "backup"), exist_ok=True)
    
    logger.info(f"Diretórios locais verificados: {DATA_DIR}")

def inicializar_sistema():
    """
    Inicializa todos os componentes do sistema
    ATUALIZADO: Suporte a OneDrive + fallback local
    """
    global ADMIN_IDS, DATABASE_PATH
    
    # Garantir que os diretórios existem antes de inicializar
    verificar_diretorios()  
    
    # NOVO: Inicializar OneDriveManager se habilitado
    if ONEDRIVE_DATABASE_ENABLED and MICROSOFT_CLIENT_ID:
        logger.info("🌐 Inicializando integração OneDrive...")
        try:
            from utils.database.database import inicializar_onedrive_manager
            inicializar_onedrive_manager()
            logger.info("✅ OneDrive integrado com sucesso")
        except Exception as e:
            logger.error(f"❌ Erro inicializando OneDrive: {e}")
            logger.info("📁 Continuando com storage local")
    else:
        logger.info("📁 OneDrive desabilitado - usando storage local")
    
    # Importar funções de database após inicialização OneDrive
    from utils.database import init_database, listar_admins, inicializar_admins_padrao
    
    # Inicializar banco de dados (OneDrive ou local)
    logger.info("🔧 Inicializando banco de dados...")
    if init_database():
        from utils.database.database import get_db_path
        DATABASE_PATH = get_db_path()
        logger.info(f"✅ Banco de dados inicializado: {DATABASE_PATH}")
    else:
        logger.error("❌ Falha ao inicializar banco de dados")
    
    # Inicializar administradores padrão (se houver)
    if ADMIN_IDS:
        logger.info("👥 Configurando administradores...")
        try:
            count = inicializar_admins_padrao(ADMIN_IDS)
            logger.info(f"✅ {count} administradores padrão configurados")
        
            # Carregar lista atual de administradores
            admins = listar_admins()
            if admins:
                ADMIN_IDS = admins
                logger.info(f"📊 Total de administradores: {len(ADMIN_IDS)}")
            else:
                logger.warning("⚠️ Não foi possível carregar administradores do banco de dados")
        except Exception as e:
            logger.error(f"❌ Erro ao configurar administradores: {str(e)}")
    else:
        logger.info("👥 Nenhum administrador configurado via ADMIN_IDS")

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

# ==================== VALIDAÇÃO DE DEPENDÊNCIAS ONEDRIVE ====================

def validar_configuracao_onedrive():
    """
    Valida se a configuração OneDrive está completa
    
    Returns:
        dict: Status da configuração OneDrive
    """
    status = {
        'habilitado': ONEDRIVE_DATABASE_ENABLED,
        'client_id_configurado': bool(MICROSOFT_CLIENT_ID),
        'tenant_configurado': bool(MICROSOFT_TENANT_ID),
        'pasta_id_configurada': bool(ONEDRIVE_ALERTA_ID),
        'token_disponivel': False,
        'pronto_para_uso': False
    }
    
    if ONEDRIVE_DATABASE_ENABLED and MICROSOFT_CLIENT_ID:
        try:
            from auth.microsoft_auth import MicrosoftAuth
            auth = MicrosoftAuth()
            status['token_disponivel'] = bool(auth.access_token)
            status['pronto_para_uso'] = status['token_disponivel']
        except Exception as e:
            logger.debug(f"Erro validando token OneDrive: {e}")
    
    return status

# Log final das configurações
logger.info("🔧 Configurações carregadas com sucesso")

# Se OneDrive habilitado, mostrar status
if ONEDRIVE_DATABASE_ENABLED:
    status_onedrive = validar_configuracao_onedrive()
    logger.info(f"🌐 Status OneDrive: {'✅ Pronto' if status_onedrive['pronto_para_uso'] else '⚠️ Configuração incompleta'}")
