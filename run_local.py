#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Script para teste local do CCB Alerta Bot
Este script verifica o ambiente e executa o bot localmente
"""

import os
import sys
import logging
from importlib import import_module

# Configurar logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger("CCB-Alerta-Bot")

def verificar_ambiente():
    """Verifica se o ambiente está configurado corretamente"""
    logger.info("Verificando ambiente de execução...")
    
    # Verificar Python
    versao = sys.version_info
    if versao.major < 3 or (versao.major == 3 and versao.minor < 8):
        logger.error("ERRO: É necessário Python 3.8 ou superior!")
        return False
    logger.info(f"✅ Python {versao.major}.{versao.minor}.{versao.micro} encontrado")
    
    # Verificar dependências
    dependencias = ["telegram", "pandas", "openpyxl", "pytz"]
    for dep in dependencias:
        try:
            import_module(dep)
            logger.info(f"✅ Biblioteca {dep} encontrada")
        except ImportError:
            logger.error(f"ERRO: Biblioteca {dep} não encontrada! Execute 'pip install -r requirements.txt'")
            return False
    
    # Verificar token do bot
    try:
        from config import TOKEN
        if not TOKEN or TOKEN == "SEU_TOKEN_AQUI":
            logger.error("ERRO: Token do bot não configurado! Edite o arquivo config.py")
            return False
        logger.info("✅ Token do bot configurado")
    except ImportError:
        logger.error("ERRO: Arquivo config.py não encontrado!")
        return False
    
    # Estrutura de pastas
    if not os.path.exists("handlers"):
        logger.error("ERRO: Pasta 'handlers' não encontrada!")
        return False
    logger.info("✅ Estrutura de pastas OK")
    
    logger.info("✅ Ambiente verificado com sucesso!")
    return True

def main():
    """Função principal"""
    logger.info("=" * 50)
    logger.info("CCB ALERTA BOT - MODO DE TESTE LOCAL")
    logger.info("=" * 50)
    
    if not verificar_ambiente():
        logger.error("Falha na verificação do ambiente. Corrigindo problemas antes de continuar.")
        sys.exit(1)
    
    logger.info("Iniciando bot...")
    try:
        # Importar e executar o bot
        import bot
        bot.main()
    except Exception as e:
        logger.error(f"Erro ao iniciar o bot: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()