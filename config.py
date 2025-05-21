#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Configurações globais para o CCB Alerta Bot
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

def verificar_diretorios():
    """Garante que os diretórios necessários existam"""
    # Garantir que o diretório de dados existe
    os.makedirs(DATA_DIR, exist_ok=True)
    
    # Criar subdiretórios necessários
    os.makedirs(os.path.join(DATA_DIR, "logs"), exist_ok=True)
    os.makedirs(os.path.join(DATA_DIR, "temp"), exist_ok=True)
    os.makedirs(os.path.join(DATA_DIR, "backup"), exist_ok=True)

# IDs de administradores (lista inicial)
ADMIN_IDS = [5876346562]  # Adicione aqui os IDs dos administradores

# Estados para a conversa de cadastro em etapas
CODIGO, NOME, FUNCAO, CONFIRMAR = range(4)

def inicializar_sistema():
    """Inicializa todos os componentes do sistema"""
    verificar_diretorios()  # Garantir que os diretórios existam antes de inicializar
    
    # Inicializar banco de dados
    logger.info("Inicializando banco de dados...")
    if init_database():
        logger.info("Banco de dados inicializado com sucesso")
    else:
        logger.error("Falha ao inicializar banco de dados")
    
    # Inicializar administradores padrão
    logger.info("Configurando administradores...")
    count = inicializar_admins_padrao(ADMIN_IDS)
    logger.info(f"{count} administradores padrão configurados")
    
    # Carregar lista atual de administradores
    global ADMIN_IDS
    ADMIN_IDS = listar_admins()
    logger.info(f"Total de administradores: {len(ADMIN_IDS)}")
