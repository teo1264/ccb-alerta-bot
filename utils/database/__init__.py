#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Submódulo de acesso ao banco de dados para o CCB Alerta Bot
"""

# Importar todas as funções para o namespace do pacote
from .database import (
    get_db_path,
    get_connection,
    init_database,
    fazer_backup_banco,
    salvar_responsavel,
    verificar_cadastro_existente,
    obter_cadastros_por_user_id,
    remover_cadastros_por_user_id,
    buscar_responsaveis_por_codigo,
    buscar_responsavel_por_id,
    listar_todos_responsaveis,
    remover_responsavel,
    remover_responsavel_especifico,
    editar_responsavel,
    verificar_admin,
    listar_admins,
    adicionar_admin,
    remover_admin,
    registrar_consentimento_lgpd,
    verificar_consentimento_lgpd,
    remover_consentimento_lgpd,
    registrar_alerta_enviado,
    listar_alertas_enviados,
    obter_estatisticas_alertas,
    inicializar_admins_padrao
)
