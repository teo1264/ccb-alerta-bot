#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Configurações globais para o CCB Alerta Bot
Adaptado para usar SQLite e disco persistente no Render
"""
import os
import logging
from utils.database import init_database, verificar_admin, listar_admins, inicializar_admins_padrao

# Token do Bot (coloque aqui seu token)
TOKEN = "7773179413:AAHqJp-NBPPs6YrSV1kB5-q4vkV3tjDFyy4"

# Configurar o log
logger = logging.getLogger("CCB-Alerta-Bot")

# Caminho para o disco persistente no Render
RENDER_DISK_PATH = os.environ.get("RENDER_DISK_PATH", "/opt/render/project/disk")

# Diretório de dados compartilhado
DATA_DIR = os.path.join(RENDER_DISK_PATH, "shared_data")

# Caminho para o banco de dados SQLite
DATABASE_PATH = os.path.join(DATA_DIR, "ccb_alerta_bot.db")

# IDs de administradores (lista inicial)
ADMIN_IDS = [5876346562]  # Adicione aqui os IDs dos administradores

def verificar_diretorios():
    """Garante que os diretórios necessários existam"""
    # Garantir que o diretório de dados existe
    os.makedirs(DATA_DIR, exist_ok=True)
    
    # Criar subdiretórios necessários
    os.makedirs(os.path.join(DATA_DIR, "logs"), exist_ok=True)
    os.makedirs(os.path.join(DATA_DIR, "temp"), exist_ok=True)
    os.makedirs(os.path.join(DATA_DIR, "backup"), exist_ok=True)
    
    logger.info(f"Diretórios verificados e criados em: {DATA_DIR}")
    logger.info(f"Banco de dados será armazenado em: {DATABASE_PATH}")

# Estados para a conversa de cadastro em etapas
CODIGO, NOME, FUNCAO, CONFIRMAR = range(4)

def inicializar_sistema():
    """Inicializa todos os componentes do sistema"""
    global ADMIN_IDS  # Declaração global movida para o início da função
    
    # Garantir que os diretórios existam antes de inicializar
    verificar_diretorios()  
    
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
