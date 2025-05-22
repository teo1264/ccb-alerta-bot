#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Pacote de utilitários para o CCB Alerta Bot
Versão corrigida para compatibilidade com SQLite
"""

# Importar todas as funções necessárias para disponibilizar no namespace do pacote
from .utils import (
    verificar_formato_cadastro,
    extrair_dados_cadastro,
    fazer_backup_planilha,
    verificar_cadastro_existente,
    salvar_cadastro,
    buscar_usuario_por_id,
    buscar_usuarios_por_codigo,
    buscar_todos_usuarios,
    atualizar_cadastro,
    remover_cadastro,
    criar_pasta_temporaria,
    remover_pasta_temporaria,
    registrar_consentimento_lgpd,
    verificar_consentimento_lgpd,
    remover_consentimento_lgpd
)

# Importar funções do banco de dados diretamente para o namespace do utils
from .database import (
    # Funções principais do banco
    get_db_path,
    get_connection,
    init_database,
    fazer_backup_banco,
    
    # Funções de administradores
    verificar_admin,
    adicionar_admin,
    listar_admins,
    remover_admin,
    inicializar_admins_padrao,
    
    # Funções de responsáveis/cadastros
    salvar_responsavel,
    verificar_cadastro_existente as db_verificar_cadastro_existente,
    buscar_responsavel_por_id,
    buscar_responsaveis_por_codigo,
    listar_todos_responsaveis,
    remover_responsavel,
    remover_responsavel_especifico,
    editar_responsavel,
    limpar_todos_responsaveis,
    
    # Funções para LGPD
    obter_cadastros_por_user_id,
    remover_cadastros_por_user_id,
    registrar_consentimento_lgpd as db_registrar_consentimento_lgpd,
    verificar_consentimento_lgpd as db_verificar_consentimento_lgpd,
    remover_consentimento_lgpd as db_remover_consentimento_lgpd,
    
    # Funções para alertas
    registrar_alerta_enviado,
    listar_alertas_enviados,
    obter_estatisticas_alertas
)

# Criar aliases para manter compatibilidade com código existente
inserir_cadastro = salvar_responsavel  # Alias principal para compatibilidade
obter_cadastro_por_user_id = obter_cadastros_por_user_id  # Alias para LGPD

# Aliases adicionais para funções que podem ter nomes diferentes
fazer_backup_planilha = fazer_backup_banco  # Manter compatibilidade com código antigo

# Lista de todas as funções disponíveis no namespace (para debug)
__all__ = [
    # Funções utilitárias básicas
    'verificar_formato_cadastro',
    'extrair_dados_cadastro',
    'fazer_backup_planilha',
    'verificar_cadastro_existente',
    'salvar_cadastro',
    'buscar_usuario_por_id',
    'buscar_usuarios_por_codigo',
    'buscar_todos_usuarios',
    'atualizar_cadastro',
    'remover_cadastro',
    'criar_pasta_temporaria',
    'remover_pasta_temporaria',
    
    # Funções do banco de dados
    'get_db_path',
    'get_connection',
    'init_database',
    'fazer_backup_banco',
    
    # Administradores
    'verificar_admin',
    'adicionar_admin',
    'listar_admins',
    'remover_admin',
    'inicializar_admins_padrao',
    
    # Responsáveis/cadastros
    'salvar_responsavel',
    'inserir_cadastro',  # Alias
    'buscar_responsavel_por_id',
    'buscar_responsaveis_por_codigo',
    'listar_todos_responsaveis',
    'remover_responsavel',
    'remover_responsavel_especifico',
    'editar_responsavel',
    'limpar_todos_responsaveis',
    
    # LGPD
    'obter_cadastros_por_user_id',
    'obter_cadastro_por_user_id',  # Alias
    'remover_cadastros_por_user_id',
    'registrar_consentimento_lgpd',
    'verificar_consentimento_lgpd',
    'remover_consentimento_lgpd',
    
    # Alertas
    'registrar_alerta_enviado',
    'listar_alertas_enviados',
    'obter_estatisticas_alertas',
]
