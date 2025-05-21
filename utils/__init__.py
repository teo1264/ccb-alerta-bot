#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Pacote de utilitários para o CCB Alerta Bot
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
from utils.database import (
    verificar_admin,
    adicionar_admin,
    listar_admins,
    salvar_responsavel,
    buscar_responsavel_por_id,
    buscar_responsaveis_por_codigo,
    listar_todos_responsaveis,
    remover_responsavel,
    remover_responsavel_especifico
)
