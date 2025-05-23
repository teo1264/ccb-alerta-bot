"""
Configurações globais para o Bot de Alertas de Água via Telegram
Corrigido para evitar conflitos com outros bots que compartilham a mesma base de dados
"""
import os
import logging
from pathlib import Path

# CONFIGURAÇÃO ESPECÍFICA PARA BOT DE ALERTAS
BOT_NAME = "AlertaAgua-Bot"
BOT_VERSION = "2.0.0"

# Token específico do Bot de Alertas (DEVE SER DIFERENTE do bot de cadastro)
TOKEN = os.environ.get("TELEGRAM_BOT_ALERTAS_TOKEN", os.environ.get("TELEGRAM_BOT_TOKEN", "SEU_TOKEN_AQUI"))

# Verificação de segurança para evitar conflito de tokens
if not TOKEN or TOKEN == "SEU_TOKEN_AQUI":
    raise ValueError(
        "ERRO CRÍTICO: Token do bot não configurado!\n"
        "Configure a variável de ambiente 'TELEGRAM_BOT_ALERTAS_TOKEN' no Render\n"
        "com um token diferente do bot de cadastro."
    )

# IDs de administradores (lista inicial)
ADMIN_IDS = [5876346562]  # Adicione aqui os IDs dos administradores

# Configurações para sistema de alertas
CONSUMO_MINIMO_SIGNIFICATIVO = 10  # Consumo mínimo em m³ para alertas graves

# Configuração de diretórios
BASE_DIR = Path(__file__).resolve().parent
LOGS_DIR = os.path.join(BASE_DIR, "logs")

# Caminho para o disco persistente no Render
RENDER_DISK_PATH = os.environ.get("RENDER_DISK_PATH", "/opt/render/project/disk")

# Diretório de dados compartilhado (APENAS O BANCO É COMPARTILHADO)
DATA_DIR = os.path.join(RENDER_DISK_PATH, "shared_data")

# Caminho para o banco de dados SQLite compartilhado
DATABASE_PATH = os.path.join(DATA_DIR, "alertas_bot.db")

# CONFIGURAÇÕES ESPECÍFICAS PARA EVITAR CONFLITOS
POLLING_CONFIG = {
    "timeout": 10,
    "poll_interval": 2.0,
    "drop_pending_updates": True,
    "allowed_updates": ["message", "callback_query", "edited_message"],
    "read_timeout": 20,
    "write_timeout": 20,
    "connect_timeout": 20
}

# Configuração de logging específica para Bot de Alertas
def configurar_logging():
    """Configura o sistema de logs específico para o Bot de Alertas"""
    # Criar pastas necessárias
    os.makedirs(LOGS_DIR, exist_ok=True)
    
    # Configuração básica com identificação específica
    logging.basicConfig(
        format=f'%(asctime)s - {BOT_NAME} - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO,
        force=True  # Força reconfiguração se já existir
    )
    
    # Logger principal com nome específico
    logger = logging.getLogger(BOT_NAME)
    
    # Limpar handlers existentes para evitar duplicação
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Adicionar handler para arquivo com nome específico
    from datetime import datetime
    data_atual = datetime.now().strftime("%Y%m%d")
    arquivo_log = f"{LOGS_DIR}/alertas_bot_{data_atual}.log"
    
    try:
        file_handler = logging.FileHandler(arquivo_log, encoding='utf-8')
        file_handler.setFormatter(
            logging.Formatter(f'%(asctime)s - {BOT_NAME} - %(name)s - %(levelname)s - %(message)s')
        )
        logger.addHandler(file_handler)
        
        # Handler para console
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(
            logging.Formatter(f'{BOT_NAME} - %(levelname)s - %(message)s')
        )
        logger.addHandler(console_handler)
        
    except Exception as e:
        print(f"Erro ao configurar arquivo de log: {e}")
    
    # Configurar nível de log para bibliotecas externas
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("telegram").setLevel(logging.WARNING)
    
    return logger

# Inicializar logger
logger = configurar_logging()

def verificar_diretorios():
    """Garante que os diretórios necessários existam"""
    try:
        # Diretórios de trabalho locais
        os.makedirs(os.path.join(BASE_DIR, "data"), exist_ok=True)
        os.makedirs(os.path.join(BASE_DIR, "temp"), exist_ok=True)
        os.makedirs(os.path.join(BASE_DIR, "uploads"), exist_ok=True)
        
        # Diretório compartilhado no disco persistente do Render
        os.makedirs(DATA_DIR, exist_ok=True)
        
        logger.info(f"Diretórios verificados - Base: {BASE_DIR}")
        logger.info(f"Dados compartilhados: {DATA_DIR}")
        logger.info(f"Banco compartilhado: {DATABASE_PATH}")
        
    except Exception as e:
        logger.error(f"Erro ao verificar diretórios: {e}")
        raise

def verificar_token_unico():
    """Verifica se o token é específico e não conflita com outros bots"""
    try:
        # Log do token mascarado para debug (apenas primeiros/últimos caracteres)
        if len(TOKEN) > 10:
            token_masked = f"{TOKEN[:8]}...{TOKEN[-4:]}"
            logger.info(f"Token configurado: {token_masked}")
        
        # Verificar se não é o token padrão
        tokens_invalidos = ["SEU_TOKEN_AQUI", "TOKEN_EXAMPLE", ""]
        if TOKEN in tokens_invalidos:
            raise ValueError("Token inválido configurado")
            
        return True
        
    except Exception as e:
        logger.error(f"Erro na verificação do token: {e}")
        return False

def inicializar_sistema():
    """Inicializa os componentes do sistema com verificações específicas"""
    logger.info("=" * 60)
    logger.info(f"{BOT_NAME} v{BOT_VERSION} - INICIALIZANDO")
    logger.info("=" * 60)
    
    try:
        # Verificar token
        if not verificar_token_unico():
            raise ValueError("Falha na verificação do token")
        
        # Verificar diretórios
        verificar_diretorios()
        
        # Verificar banco de dados compartilhado
        if not os.path.exists(DATABASE_PATH):
            logger.warning(f"Banco compartilhado não encontrado: {DATABASE_PATH}")
            logger.warning("Certifique-se que o bot de cadastro criou o banco")
        else:
            logger.info(f"Banco compartilhado localizado: {DATABASE_PATH}")
        
        # Carregar administradores do banco
        try:
            from utils.database import listar_admins, init_database
            
            # Inicializar conexão com banco
            if init_database():
                global ADMIN_IDS
                admins = listar_admins()
                if admins:
                    ADMIN_IDS = admins
                    logger.info(f"Administradores carregados: {len(ADMIN_IDS)}")
                else:
                    logger.warning("Nenhum administrador encontrado no banco")
            else:
                logger.warning("Falha ao conectar com banco - usando admins padrão")
                
        except Exception as e:
            logger.error(f"Erro ao carregar administradores: {e}")
            logger.info("Usando lista padrão de administradores")
        
        # Log de configurações
        logger.info(f"Configurações de polling: {POLLING_CONFIG}")
        logger.info("Sistema inicializado com sucesso")
        
        return True
        
    except Exception as e:
        logger.error(f"ERRO CRÍTICO na inicialização: {e}")
        raise

def obter_info_sistema():
    """Retorna informações do sistema para debug"""
    return {
        "bot_name": BOT_NAME,
        "version": BOT_VERSION,
        "token_configured": bool(TOKEN and TOKEN != "SEU_TOKEN_AQUI"),
        "database_path": DATABASE_PATH,
        "database_exists": os.path.exists(DATABASE_PATH),
        "admin_count": len(ADMIN_IDS),
        "data_dir": DATA_DIR,
        "base_dir": str(BASE_DIR)
    }
