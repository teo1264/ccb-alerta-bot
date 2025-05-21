#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Funções utilitárias para o CCB Alerta Bot
"""

import os
import re
from datetime import datetime
import pytz
import shutil
import logging
from config import DATA_DIR

# Importar funções do módulo de banco de dados
from utils.database import (
    verificar_admin, adicionar_admin, 
    verificar_cadastro_existente as db_verificar_cadastro_existente,
    salvar_responsavel, buscar_responsavel_por_id,
    buscar_responsaveis_por_codigo, listar_todos_responsaveis,
    remover_responsavel, remover_responsavel_especifico
)

# Configurar logger
logger = logging.getLogger("CCB-Alerta-Bot.utils")

# Funções adaptadas para usar o banco de dados

def verificar_formato_cadastro(texto):
    """
    Verifica se o texto está no formato esperado para cadastro
    
    Args:
        texto (str): Texto a ser verificado
        
    Returns:
        bool: True se estiver no formato correto, False caso contrário
    """
    # Padrão esperado: BR21-0000 / Nome / Função
    padrao = r'^(BR\d{2}-\d{4})\s*\/\s*(.+?)\s*\/\s*(.+)$'
    return bool(re.match(padrao, texto, re.IGNORECASE))

def extrair_dados_cadastro(texto):
    """
    Extrai os dados de cadastro do texto
    
    Args:
        texto (str): Texto no formato de cadastro
        
    Returns:
        tuple: (codigo, nome, funcao) ou (None, None, None) se inválido
    """
    if not verificar_formato_cadastro(texto):
        return None, None, None
    
    # Extrair dados pelo delimitador "/"
    partes = [p.strip() for p in texto.split('/')]
    
    # Garantir que temos pelo menos 3 partes (código, nome, função)
    if len(partes) >= 3:
        codigo_casa = partes[0].strip()
        nome = partes[1].strip()
        funcao = partes[2].strip()
        return codigo_casa, nome, funcao
    
    return None, None, None

def fazer_backup_planilha():
    """
    Cria um backup do banco de dados
    
    Returns:
        str: Nome do arquivo de backup
    """
    try:
        from utils.database import get_db_path
        db_path = get_db_path()
        
        if not os.path.exists(db_path):
            logger.warning(f"Banco de dados não encontrado para backup: {db_path}")
            return None
            
        # Criar nome para backup
        fuso_horario = pytz.timezone('America/Sao_Paulo')
        agora = datetime.now(fuso_horario)
        timestamp = agora.strftime("%Y%m%d%H%M%S")
        
        # Diretório de backup
        backup_dir = os.path.join(DATA_DIR, "backup")
        os.makedirs(backup_dir, exist_ok=True)
        
        # Nome do arquivo
        backup_file = os.path.join(backup_dir, f"alertas_bot_{timestamp}.db")
        
        # Criar cópia física do arquivo
        shutil.copy2(db_path, backup_file)
        
        logger.info(f"Backup do banco de dados criado: {backup_file}")
        return backup_file
    except Exception as e:
        logger.error(f"Erro ao fazer backup: {e}")
        return None

def verificar_cadastro_existente(codigo, nome, funcao):
    """
    Verifica se já existe um cadastro com os mesmos dados
    
    Args:
        codigo (str): Código da casa
        nome (str): Nome do responsável
        funcao (str): Função do responsável
        
    Returns:
        bool: True se existir, False caso contrário
    """
    return db_verificar_cadastro_existente(codigo, nome, funcao)

def salvar_cadastro(codigo, nome, funcao, user_id, username):
    """
    Salva os dados do cadastro no banco de dados
    
    Args:
        codigo (str): Código da casa
        nome (str): Nome do responsável
        funcao (str): Função do responsável
        user_id (int): ID do usuário no Telegram
        username (str): Username do usuário no Telegram
        
    Returns:
        tuple: (sucesso, status)
    """
    return salvar_responsavel(codigo, nome, funcao, user_id, username)

# Funções de pesquisa para compatibilidade com o código existente
def buscar_usuario_por_id(user_id):
    """
    Busca um usuário pelo ID do Telegram
    
    Args:
        user_id (int): ID do usuário
        
    Returns:
        dict: Dados do usuário ou None se não encontrado
    """
    return buscar_responsavel_por_id(user_id)

def buscar_usuarios_por_codigo(codigo_casa):
    """
    Busca usuários pelo código da casa
    
    Args:
        codigo_casa (str): Código da casa
        
    Returns:
        list: Lista de dicionários com dados dos usuários
    """
    return buscar_responsaveis_por_codigo(codigo_casa)

def buscar_todos_usuarios():
    """
    Retorna todos os usuários cadastrados
    
    Returns:
        list: Lista de dicionários com dados dos usuários
    """
    return listar_todos_responsaveis()

def atualizar_cadastro(user_id, dados_novos):
    """
    Atualiza os dados de um cadastro existente
    
    Args:
        user_id (int): ID do usuário no Telegram
        dados_novos (dict): Dados novos a serem atualizados
        
    Returns:
        bool: True se atualizado com sucesso, False caso contrário
    """
    try:
        # Buscar registro atual
        responsavel = buscar_responsavel_por_id(user_id)
        if not responsavel:
            logger.warning(f"Usuário não encontrado para atualização: {user_id}")
            return False
        
        # Obter ID do registro
        id_registro = responsavel['id']
        
        # Atualizar data de modificação
        from datetime import datetime
        import pytz
        fuso_horario = pytz.timezone('America/Sao_Paulo')
        agora = datetime.now(fuso_horario).strftime("%d/%m/%Y %H:%M:%S")
        dados_novos['ultima_atualizacao'] = agora
        
        # Atualizar registro usando a função do módulo database.py
        from utils.database import editar_responsavel
        return editar_responsavel(id_registro, dados_novos)
        
    except Exception as e:
        logger.error(f"Erro ao atualizar cadastro: {e}")
        return False

def remover_cadastro(user_id):
    """
    Remove um cadastro da planilha
    
    Args:
        user_id (int): ID do usuário no Telegram
        
    Returns:
        bool: True se removido com sucesso, False caso contrário
    """
    try:
        sucesso, _ = remover_responsavel(user_id)
        return sucesso
    except Exception as e:
        logger.error(f"Erro ao remover cadastro: {e}")
        return False

def criar_pasta_temporaria():
    """
    Cria uma pasta temporária para armazenar arquivos
    
    Returns:
        str: Caminho da pasta temporária
    """
    try:
        # Criar pasta temporária no diretório compartilhado
        import tempfile
        from config import TEMP_DIR
        
        # Garantir que o diretório existe
        os.makedirs(TEMP_DIR, exist_ok=True)
        
        # Criar pasta temporária dentro do diretório compartilhado
        pasta_temp = tempfile.mkdtemp(dir=TEMP_DIR, prefix="ccb_alerta_")
        logger.info(f"Pasta temporária criada: {pasta_temp}")
        return pasta_temp
    except Exception as e:
        logger.error(f"Erro ao criar pasta temporária: {e}")
        return None

def remover_pasta_temporaria(pasta_temp):
    """
    Remove uma pasta temporária e seu conteúdo
    
    Args:
        pasta_temp (str): Caminho da pasta temporária
        
    Returns:
        bool: True se removida com sucesso, False caso contrário
    """
    try:
        # Verificar se existe
        if not os.path.exists(pasta_temp):
            return True
            
        # Remover pasta e conteúdo
        shutil.rmtree(pasta_temp)
        logger.info(f"Pasta temporária removida: {pasta_temp}")
        return True
    except Exception as e:
        logger.error(f"Erro ao remover pasta temporária: {e}")
        return False

def registrar_consentimento_lgpd(user_id, detalhes=None):
    """
    Registra o consentimento do usuário para LGPD
    
    Args:
        user_id (int): ID do usuário
        detalhes (str, optional): Detalhes adicionais
        
    Returns:
        bool: True se registrado com sucesso, False caso contrário
    """
    try:
        from utils.database import registrar_consentimento_lgpd as db_registrar_consentimento
        return db_registrar_consentimento(user_id, detalhes=detalhes)
    except Exception as e:
        logger.error(f"Erro ao registrar consentimento LGPD: {e}")
        return False

def verificar_consentimento_lgpd(user_id):
    """
    Verifica se o usuário deu consentimento LGPD
    
    Args:
        user_id (int): ID do usuário
        
    Returns:
        bool: True se consentiu, False caso contrário
    """
    try:
        from utils.database import verificar_consentimento_lgpd as db_verificar_consentimento
        return db_verificar_consentimento(user_id)
    except Exception as e:
        logger.error(f"Erro ao verificar consentimento LGPD: {e}")
        return False

def remover_consentimento_lgpd(user_id):
    """
    Remove o registro de consentimento LGPD do usuário
    
    Args:
        user_id (int): ID do usuário
        
    Returns:
        bool: True se removido com sucesso, False caso contrário
    """
    try:
        from utils.database import remover_consentimento_lgpd as db_remover_consentimento
        return db_remover_consentimento(user_id)
    except Exception as e:
        logger.error(f"Erro ao remover consentimento LGPD: {e}")
        return False
