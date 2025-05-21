#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Script para testar a configuração e operação do banco de dados SQLite
"""

import logging
import os
import sys
from datetime import datetime

# Configurar logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger("DatabaseTest")

# Adicionar o diretório atual ao path para importações
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def main():
    """Função principal para testar o banco de dados"""
    logger.info("=" * 60)
    logger.info("TESTE DE CONFIGURAÇÃO DO BANCO DE DADOS SQLITE")
    logger.info("=" * 60)
    
    # Importar módulo de banco de dados
    try:
        from utils.database import (
            init_database, get_db_path, salvar_responsavel, 
            buscar_responsaveis_por_codigo, listar_todos_responsaveis,
            verificar_admin, adicionar_admin, listar_admins,
            registrar_consentimento_lgpd, verificar_consentimento_lgpd,
            registrar_alerta_enviado, listar_alertas_enviados,
            obter_estatisticas_alertas
        )
        logger.info("✅ Módulo de banco de dados importado com sucesso")
    except ImportError as e:
        logger.error(f"❌ Erro ao importar módulo de banco de dados: {e}")
        sys.exit(1)
    
    # Obter o caminho do banco de dados
    db_path = get_db_path()
    logger.info(f"📁 Caminho do banco de dados: {db_path}")
    
    # Verificar diretório de dados
    dir_path = os.path.dirname(db_path)
    if os.path.exists(dir_path):
        logger.info(f"✅ Diretório de dados existe: {dir_path}")
    else:
        logger.error(f"❌ Diretório de dados não existe: {dir_path}")
        logger.info("Tentando criar diretório...")
        try:
            os.makedirs(dir_path, exist_ok=True)
            logger.info("✅ Diretório criado com sucesso")
        except Exception as e:
            logger.error(f"❌ Erro ao criar diretório: {e}")
    
    # Inicializar banco de dados
    logger.info("🔄 Inicializando banco de dados...")
    if init_database():
        logger.info("✅ Banco de dados inicializado com sucesso")
        
        # Verificar se o arquivo foi criado
        if os.path.exists(db_path):
            logger.info(f"✅ Arquivo do banco de dados criado: {db_path}")
            logger.info(f"   Tamanho: {os.path.getsize(db_path)} bytes")
        else:
            logger.error(f"❌ Arquivo do banco de dados não foi criado: {db_path}")
    else:
        logger.error("❌ Falha ao inicializar banco de dados")
        sys.exit(1)
    
    # Testar inserção de dados
    logger.info("\n🔄 Testando inserção de dados...")
    
    # Criar dados de teste
    user_id_teste = 9999999  # ID que não vai conflitar com usuários reais
    codigo_teste = "BR21-9999"
    nome_teste = f"Usuário de Teste {datetime.now().strftime('%H:%M:%S')}"
    funcao_teste = "Teste Automatizado"
    
    # Salvar responsável
    logger.info(f"🔄 Salvando responsável de teste: {nome_teste}")
    sucesso, status = salvar_responsavel(
        codigo_teste, nome_teste, funcao_teste, user_id_teste, "usuario_teste"
    )
    
    if sucesso:
        logger.info(f"✅ Responsável salvo com sucesso. Status: {status}")
    else:
        logger.error(f"❌ Erro ao salvar responsável: {status}")
    
    # Testar consulta de dados
    logger.info("\n🔄 Testando consulta de dados...")
    
    # Buscar responsáveis pelo código
    responsaveis = buscar_responsaveis_por_codigo(codigo_teste)
    if responsaveis:
        logger.info(f"✅ Encontrados {len(responsaveis)} responsáveis para o código {codigo_teste}")
        for i, resp in enumerate(responsaveis, 1):
            logger.info(f"   {i}. {resp['nome']} ({resp['funcao']})")
    else:
        logger.error(f"❌ Nenhum responsável encontrado para o código {codigo_teste}")
    
    # Listar todos os responsáveis
    todos = listar_todos_responsaveis()
    logger.info(f"📊 Total de responsáveis no banco: {len(todos)}")
    
    # Testar administradores
    logger.info("\n🔄 Testando administradores...")
    
    # Adicionar admin de teste
    logger.info(f"🔄 Adicionando admin de teste: {user_id_teste}")
    sucesso, status = adicionar_admin(user_id_teste)
    
    if sucesso:
        logger.info(f"✅ Admin adicionado com sucesso. Status: {status}")
    else:
        logger.info(f"ℹ️ Admin não adicionado: {status}")
    
    # Verificar se é admin
    if verificar_admin(user_id_teste):
        logger.info(f"✅ Usuario {user_id_teste} é admin")
    else:
        logger.error(f"❌ Usuario {user_id_teste} não é admin")
    
    # Listar administradores
    admins = listar_admins()
    logger.info(f"📊 Total de administradores: {len(admins)}")
    logger.info(f"   Administradores: {admins}")
    
    # Testar LGPD
    logger.info("\n🔄 Testando consentimento LGPD...")
    
    # Registrar consentimento
    if registrar_consentimento_lgpd(user_id_teste):
        logger.info(f"✅ Consentimento LGPD registrado para {user_id_teste}")
    else:
        logger.error(f"❌ Erro ao registrar consentimento LGPD para {user_id_teste}")
    
    # Verificar consentimento
    if verificar_consentimento_lgpd(user_id_teste):
        logger.info(f"✅ Usuário {user_id_teste} deu consentimento LGPD")
    else:
        logger.error(f"❌ Usuário {user_id_teste} não deu consentimento LGPD")
    
    # Testar alertas
    logger.info("\n🔄 Testando registro de alertas...")
    
    # Registrar alerta
    message = f"Mensagem de teste enviada em {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}"
    if registrar_alerta_enviado(codigo_teste, "Teste", message, user_id_teste):
        logger.info(f"✅ Alerta registrado com sucesso")
    else:
        logger.error(f"❌ Erro ao registrar alerta")
    
    # Listar alertas
    alertas = listar_alertas_enviados(user_id_teste)
    logger.info(f"📊 Alertas encontrados para o usuário {user_id_teste}: {len(alertas)}")
    
    # Estatísticas de alertas
    stats = obter_estatisticas_alertas()
    logger.info(f"📊 Estatísticas de alertas:")
    logger.info(f"   Total de alertas: {stats['total']}")
    logger.info(f"   Por tipo: {stats['por_tipo']}")
    logger.info(f"   Por período: {stats['por_periodo']}")
    
    # Conclusão
    logger.info("\n" + "=" * 60)
    logger.info("✅ TESTE CONCLUÍDO COM SUCESSO!")
    logger.info("=" * 60)

if __name__ == "__main__":
    main()
