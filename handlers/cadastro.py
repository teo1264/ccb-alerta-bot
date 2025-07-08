#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Handlers para o processo de cadastro do CCB Alerta Bot
VERSÃO CORRIGIDA - SEM parse_mode='Markdown'
"""

import re
import math
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    CommandHandler, MessageHandler, CallbackQueryHandler,
    ConversationHandler, ContextTypes, filters
)

from config import CODIGO, NOME, FUNCAO, CONFIRMAR
try:
    from utils.database import (
        verificar_cadastro_existente,
        salvar_responsavel,
        obter_cadastros_por_user_id,
        verificar_consentimento_lgpd,
        registrar_consentimento_lgpd
    )
except ImportError:
    import sys
    import os
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
    from utils.database import (
        verificar_cadastro_existente,
        salvar_responsavel,
        obter_cadastros_por_user_id,
        verificar_consentimento_lgpd,
        registrar_consentimento_lgpd
    )

from handlers.data import (
    IGREJAS, FUNCOES, agrupar_igrejas, agrupar_funcoes, 
    obter_igreja_por_codigo, detectar_funcao_similar
)

# Logger
logger = logging.getLogger(__name__)

# Estados simplificados
SELECIONAR_IGREJA, SELECIONAR_FUNCAO = range(4, 6)

async def iniciar_cadastro_etapas(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Inicia o processo de cadastro - VERSÃO CORRIGIDA"""
    user_id = update.effective_user.id
    
    # Verificar LGPD no banco
    usuario_aceitou_lgpd = verificar_consentimento_lgpd(user_id)
    
    if not usuario_aceitou_lgpd:
        # Exibir LGPD
        keyboard = [
            [InlineKeyboardButton("✅ Aceito os termos", callback_data="aceitar_lgpd_cadastro")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "*A Paz de Deus!*\n\n"
            "Antes de prosseguir, informamos que coletamos *seu nome*, *função* e *ID do Telegram*.\n\n"
            "Esses dados são para comunicação administrativa das Casas de Oração.\n\n"
            "**Não são compartilhados** e seguem a **LGPD**.\n\n"
            "Para remover seus dados: */remover*\n\n"
            "Se estiver de acordo:",
            reply_markup=reply_markup
        )
        return ConversationHandler.END
    
    # Limpar contexto
    context.user_data['cadastro_temp'] = {'pagina_igreja': 0}
    
    logger.info(f"🚀 INICIANDO cadastro usuário {user_id}")
    await mostrar_menu_igrejas(update, context)
    return SELECIONAR_IGREJA

async def processar_aceite_lgpd_cadastro(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Processa aceite LGPD"""
    query = update.callback_query
    await query.answer()
    
    if query.data == "aceitar_lgpd_cadastro":
        # Salvar no banco
        registrar_consentimento_lgpd(query.from_user.id)
        
        await query.edit_message_text(
            "*A Santa Paz de Deus!*\n\n"
            "✅ *Termos aceitos!*\n\n"
            "Use /cadastrar novamente para iniciar.\n\n"
            "_Deus te abençoe!_ 🙏"
        )

async def mostrar_menu_igrejas(update, context: ContextTypes.DEFAULT_TYPE):
    """Mostra menu de igrejas - VERSÃO CORRIGIDA"""
    igrejas_paginadas = agrupar_igrejas()
    pagina_atual = context.user_data['cadastro_temp'].get('pagina_igreja', 0)
    
    if pagina_atual >= len(igrejas_paginadas):
        pagina_atual = 0
    elif pagina_atual < 0:
        pagina_atual = len(igrejas_paginadas) - 1
    
    context.user_data['cadastro_temp']['pagina_igreja'] = pagina_atual
    
    # Botões da página atual
    keyboard = []
    for igreja in igrejas_paginadas[pagina_atual]:
        callback_data = f"igreja_{igreja['codigo']}"
        keyboard.append([InlineKeyboardButton(
            f"{igreja['codigo']} - {igreja['nome']}", 
            callback_data=callback_data
        )])
    
    # Navegação
    nav_buttons = []
    if len(igrejas_paginadas) > 1:
        nav_buttons.append(InlineKeyboardButton("⬅️ Anterior", callback_data="igreja_anterior"))
        nav_buttons.append(InlineKeyboardButton("Próxima ➡️", callback_data="igreja_proxima"))
    keyboard.append(nav_buttons)
    
    keyboard.append([InlineKeyboardButton("❌ Cancelar", callback_data="cancelar_cadastro")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    texto = (
        "*A Santa Paz de Deus!*\n\n"
        "Selecione a Casa de Oração:\n\n"
        f"📄 *Página {pagina_atual + 1}/{len(igrejas_paginadas)}*"
    )
    
    # Enviar mensagem SEM parse_mode
    try:
        if hasattr(update, 'edit_message_text'):
            logger.info("🔄 Editando mensagem igrejas")
            await update.edit_message_text(texto, reply_markup=reply_markup)
        else:
            logger.info("📱 Nova mensagem igrejas")
            await update.message.reply_text(texto, reply_markup=reply_markup)
        
        logger.info("✅ Menu igrejas OK")
        
    except Exception as e:
        logger.error(f"❌ Erro menu igrejas: {e}")

async def processar_selecao_igreja(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Processa a seleção ou navegação no menu de igrejas
    CORRIGIDO: Remove botões antes de mudar estado + sem parse_mode
    """
    query = update.callback_query
    await query.answer()
    
    data = query.data
    logger.info(f"Callback recebido: {data}")
    
    if data == "cancelar_cadastro":
        # Limpar dados do contexto
        if 'cadastro_temp' in context.user_data:
            del context.user_data['cadastro_temp']
        
        await query.edit_message_text(
            " *A Paz de Deus!*\n\n"
            "❌ *Cadastro cancelado!*\n\n"
            "Você pode iniciar novamente quando quiser usando /cadastrar.\n\n"
            "_Deus te abençoe!_ 🙏"
        )
        return ConversationHandler.END
    
    if data == "igreja_anterior":
        # Navegar para a página anterior
        context.user_data['cadastro_temp']['pagina_igreja'] -= 1
        await mostrar_menu_igrejas(query, context)
        return SELECIONAR_IGREJA
    
    if data == "igreja_proxima":
        # Navegar para a próxima página
        context.user_data['cadastro_temp']['pagina_igreja'] += 1
        await mostrar_menu_igrejas(query, context)
        return SELECIONAR_IGREJA
    
    # Selecionar igreja (verificar se começa com igreja_BR)
    if data.startswith("igreja_BR"):
        codigo_igreja = data.replace("igreja_", "")
        igreja = obter_igreja_por_codigo(codigo_igreja)
        
        if igreja:
            # Armazenar código e nome da igreja
            context.user_data['cadastro_temp']['codigo'] = igreja['codigo']
            context.user_data['cadastro_temp']['nome_igreja'] = igreja['nome']
            
            logger.info(f"Igreja selecionada: {igreja['codigo']} - {igreja['nome']}")
            
            # CORREÇÃO: Remover TODOS os botões antes de mudar estado + sem parse_mode
            await query.edit_message_text(
                f" *A Paz de Deus!*\n\n"
                f"✅ Casa de Oração selecionada: *{igreja['codigo']} - {igreja['nome']}*\n\n"
                f"Agora, DIGITE O NOME DO RESPONSÁVEL:"
                # SEM reply_markup = remove todos os botões inline
                # SEM parse_mode = sem erro de parsing
            )
            return NOME
        else:
            logger.warning(f"Igreja não encontrada: {codigo_igreja}")
            await mostrar_menu_igrejas(query, context)
            return SELECIONAR_IGREJA
    
    # Fallback - mostrar menu novamente
    logger.warning(f"Callback data não reconhecido: {data}")
    await mostrar_menu_igrejas(query, context)
    return SELECIONAR_IGREJA
    
async def receber_nome(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Recebe o nome - SIMPLIFICADO"""
    nome = update.message.text.strip()
    
    if len(nome) < 3:
        await update.message.reply_text("❌ Nome deve ter pelo menos 3 caracteres.")
        return NOME
    
    context.user_data['cadastro_temp']['nome'] = nome
    logger.info(f"✅ Nome: {nome}")
    
    # Ir para funções
    context.user_data['cadastro_temp']['pagina_funcao'] = 0
    await mostrar_menu_funcoes(update, context)
    return SELECIONAR_FUNCAO

async def mostrar_menu_funcoes(update, context: ContextTypes.DEFAULT_TYPE):
    """Mostra menu de funções - VERSÃO CORRIGIDA"""
    funcoes_paginadas = agrupar_funcoes()
    pagina_atual = context.user_data['cadastro_temp'].get('pagina_funcao', 0)
    
    if pagina_atual >= len(funcoes_paginadas):
        pagina_atual = 0
    elif pagina_atual < 0:
        pagina_atual = len(funcoes_paginadas) - 1
    
    context.user_data['cadastro_temp']['pagina_funcao'] = pagina_atual
    
    # Botões da página atual
    keyboard = []
    for funcao in funcoes_paginadas[pagina_atual]:
        callback_data = f"funcao_{funcao}"
        keyboard.append([InlineKeyboardButton(funcao, callback_data=callback_data)])
    
    # Navegação
    nav_buttons = []
    if len(funcoes_paginadas) > 1:
        nav_buttons.append(InlineKeyboardButton("⬅️ Anterior", callback_data="funcao_anterior"))
        nav_buttons.append(InlineKeyboardButton("Próxima ➡️", callback_data="funcao_proxima"))
    keyboard.append(nav_buttons)
    
    keyboard.append([InlineKeyboardButton("🔄 Outra Função", callback_data="funcao_outra")])
    keyboard.append([InlineKeyboardButton("❌ Cancelar", callback_data="cancelar_cadastro")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    texto = (
        "*A Paz de Deus!*\n\n"
        f"✅ Nome: *{context.user_data['cadastro_temp']['nome']}*\n\n"
        "Selecione a função:\n\n"
        f"📄 *Página {pagina_atual + 1}/{len(funcoes_paginadas)}*"
    )
    
    # Enviar mensagem SEM parse_mode
    try:
        if hasattr(update, 'edit_message_text'):
            await update.edit_message_text(texto, reply_markup=reply_markup)
        else:
            await update.message.reply_text(texto, reply_markup=reply_markup)
        
        logger.info("✅ Menu funções OK")
        
    except Exception as e:
        logger.error(f"❌ Erro menu funções: {e}")

async def processar_selecao_funcao(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Processa seleção de função - SIMPLIFICADO"""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    logger.info(f"🔍 CALLBACK FUNÇÃO: '{data}'")
    
    if data == "funcao_anterior":
        context.user_data['cadastro_temp']['pagina_funcao'] -= 1
        await mostrar_menu_funcoes(query, context)
        return SELECIONAR_FUNCAO
    
    elif data == "funcao_proxima":
        context.user_data['cadastro_temp']['pagina_funcao'] += 1
        await mostrar_menu_funcoes(query, context)
        return SELECIONAR_FUNCAO
    
    elif data == "cancelar_cadastro":
        return await cancelar_cadastro(update, context)
    
    elif data == "funcao_outra":
        await query.edit_message_text(
            "*A Paz de Deus!*\n\n"
            "✍️ **DIGITE SUA FUNÇÃO:**\n\n"
            "*(Ex: Patrimônio, Tesoureiro, etc.)*"
        )
        return FUNCAO
    
    elif data.startswith("funcao_"):
        funcao = data.replace("funcao_", "")
        
        if funcao in FUNCOES:
            context.user_data['cadastro_temp']['funcao'] = funcao
            logger.info(f"✅ Função selecionada: {funcao}")
            
            # Ir para confirmação
            await mostrar_confirmacao(query, context)
            return CONFIRMAR
    
    return SELECIONAR_FUNCAO

async def receber_funcao(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Recebe função digitada - SIMPLIFICADO"""
    funcao = update.message.text.strip()
    
    if len(funcao) < 3:
        await update.message.reply_text("❌ Função deve ter pelo menos 3 caracteres.")
        return FUNCAO
    
    # Verificar se é similar às existentes
    funcao_similar_encontrada, funcao_oficial = detectar_funcao_similar(funcao)
    
    if funcao_similar_encontrada:
        await update.message.reply_text(
            f"⚠️ *Função similar encontrada!*\n\n"
            f"Você digitou: *\"{funcao}\"*\n"
            f"Similar a: *\"{funcao_oficial}\"*\n\n"
            f"Use /cadastrar novamente e selecione *\"{funcao_oficial}\"* no menu."
        )
        return FUNCAO
    
    context.user_data['cadastro_temp']['funcao'] = funcao
    logger.info(f"✅ Função digitada: {funcao}")
    
    # Ir para confirmação
    await mostrar_confirmacao(update, context)
    return CONFIRMAR

async def mostrar_confirmacao(update, context: ContextTypes.DEFAULT_TYPE):
    """Mostra confirmação - VERSÃO CORRIGIDA"""
    dados = context.user_data['cadastro_temp']
    
    keyboard = [
        [
            InlineKeyboardButton("✅ Confirmar", callback_data="confirmar_etapas"),
            InlineKeyboardButton("❌ Cancelar", callback_data="cancelar_etapas")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    texto = (
        "*A Paz de Deus!*\n\n"
        "📝 *Confirme os dados:*\n\n"
        f"📍 *Código:* `{dados['codigo']}`\n"
        f"🏢 *Casa:* `{dados['nome_igreja']}`\n"
        f"👤 *Nome:* `{dados['nome']}`\n"
        f"🔧 *Função:* `{dados['funcao']}`\n\n"
        "Os dados estão corretos?"
    )
    
    try:
        if hasattr(update, 'edit_message_text'):
            await update.edit_message_text(texto, reply_markup=reply_markup)
        else:
            await update.message.reply_text(texto, reply_markup=reply_markup)
    except Exception as e:
        logger.error(f"❌ Erro confirmação: {e}")

async def confirmar_etapas(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Confirma cadastro - VERSÃO CORRIGIDA"""
    query = update.callback_query
    await query.answer()
    
    if query.data == "cancelar_etapas":
        return await cancelar_cadastro(update, context)
    
    # Obter dados
    dados = context.user_data['cadastro_temp']
    user_id = update.effective_user.id
    username = update.effective_user.username or ""
    
    try:
        # Salvar no banco
        sucesso, status = salvar_responsavel(
            dados['codigo'], 
            dados['nome'], 
            dados['funcao'], 
            user_id, 
            username
        )
        
        if sucesso:
            await query.edit_message_text(
                "*Projeto Débito Automático*\n\n"
                "✅ *Cadastro realizado com sucesso!*\n\n"
                f"📍 *Código:* `{dados['codigo']}`\n"
                f"🏢 *Casa:* `{dados['nome_igreja']}`\n"
                f"👤 *Nome:* `{dados['nome']}`\n"
                f"🔧 *Função:* `{dados['funcao']}`\n\n"
                "📢 Os alertas automáticos começarão em breve.\n\n"
                "_Deus te abençoe!_ 🙌"
            )
        else:
            await query.edit_message_text(
                "*A Paz de Deus!*\n\n"
                "❌ *Erro no cadastro.*\n\n"
                "Tente novamente mais tarde.\n\n"
                "_Deus te abençoe!_ 🙏"
            )
        
    except Exception as e:
        logger.error(f"❌ Erro ao salvar: {e}")
        await query.edit_message_text(
            "*A Paz de Deus!*\n\n"
            "❌ *Erro interno.*\n\n"
            "Tente novamente.\n\n"
            "_Deus te abençoe!_ 🙏"
        )
    
    # Limpar contexto
    if 'cadastro_temp' in context.user_data:
        del context.user_data['cadastro_temp']
    
    return ConversationHandler.END

async def cancelar_cadastro(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancela cadastro - VERSÃO CORRIGIDA"""
    # Limpar contexto
    if 'cadastro_temp' in context.user_data:
        del context.user_data['cadastro_temp']
    
    if hasattr(update, 'callback_query') and update.callback_query:
        await update.callback_query.edit_message_text(
            "*A Santa Paz de Deus!*\n\n"
            "❌ *Cadastro cancelado!*\n\n"
            "Use /cadastrar para tentar novamente.\n\n"
            "_Deus te abençoe!_ 🙏"
        )
    else:
        await update.message.reply_text(
            "*A Santa Paz de Deus!*\n\n"
            "❌ *Cadastro cancelado!*\n\n"
            "Use /cadastrar para tentar novamente.\n\n"
            "_Deus te abençoe!_ 🙏"
        )
    
    return ConversationHandler.END

def registrar_handlers_cadastro(application):
    """Registra handlers - VERSÃO SIMPLIFICADA"""
    
    # Handler LGPD
    application.add_handler(CallbackQueryHandler(
        processar_aceite_lgpd_cadastro, 
        pattern='^aceitar_lgpd_cadastro$'
    ))
    
    # ConversationHandler SIMPLIFICADO
    cadastro_handler = ConversationHandler(
        entry_points=[
            CommandHandler("cadastrar", iniciar_cadastro_etapas),
        ],
        states={
            SELECIONAR_IGREJA: [
                CallbackQueryHandler(processar_selecao_igreja),
            ],
            NOME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receber_nome)
            ],
            SELECIONAR_FUNCAO: [
                CallbackQueryHandler(processar_selecao_funcao),
            ],
            FUNCAO: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receber_funcao),
            ],
            CONFIRMAR: [
                CallbackQueryHandler(confirmar_etapas),
            ]
        },
        fallbacks=[
            CommandHandler("cancelar", cancelar_cadastro),
        ],
        name="cadastro_conversation",
        persistent=False,
        per_message=False
    )
    
    application.add_handler(cadastro_handler)
    logger.info("✅ Handlers cadastro CORRIGIDOS registrados")
