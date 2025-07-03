#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Handlers para o processo de cadastro do CCB Alerta Bot
VERSÃO CORRIGIDA COMPLETA - Fix navegação + cancelar
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
        verificar_cadastro_existente_detalhado,
        salvar_responsavel as inserir_cadastro,
        obter_cadastros_por_user_id as obter_cadastro_por_user_id
    )
except ImportError:
    import sys
    import os
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
    from utils.database import (
        verificar_cadastro_existente_detalhado,
        salvar_responsavel as inserir_cadastro,
        obter_cadastros_por_user_id as obter_cadastro_por_user_id
    )

from handlers.data import (
    IGREJAS, FUNCOES, agrupar_igrejas, agrupar_funcoes, 
    obter_igreja_por_codigo, detectar_funcao_similar
)

logger = logging.getLogger(__name__)

# Estados para navegação
SELECIONAR_IGREJA, SELECIONAR_FUNCAO = range(4, 6)

# ==================== FUNÇÃO CANCELAR CORRIGIDA ====================
async def cancelar_cadastro(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """CORRIGIDO: Cancela o cadastro em qualquer etapa"""
    
    # Limpar dados do contexto
    if 'cadastro_temp' in context.user_data:
        del context.user_data['cadastro_temp']
    
    # Verificar se é callback ou comando
    if hasattr(update, 'callback_query') and update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(
            "*A Santa Paz de Deus!*\n\n"
            "❌ *Cadastro cancelado!*\n\n"
            "Envie qualquer mensagem para iniciar novamente.\n\n"
            "_Deus te abençoe!_ 🙏",
            parse_mode='Markdown'
        )
    else:
        await update.message.reply_text(
            "*A Santa Paz de Deus!*\n\n"
            "❌ *Cadastro cancelado!*\n\n"
            "Envie qualquer mensagem para iniciar novamente.\n\n"
            "_Deus te abençoe!_ 🙏",
            parse_mode='Markdown'
        )
    
    return ConversationHandler.END

# ==================== FUNÇÕES DE INICIALIZAÇÃO ====================
async def iniciar_cadastro_etapas(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Inicia o processo de cadastro passo a passo"""
    usuario_aceitou_lgpd = context.user_data.get('aceitou_lgpd', False)
    
    if not usuario_aceitou_lgpd:
        keyboard = [
            [InlineKeyboardButton("✅ Aceito os termos", callback_data="aceitar_lgpd_cadastro")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "*A Paz de Deus, irmão!*\n\n"
            "Antes de prosseguir com o cadastro, informamos que este canal coleta *seu nome*, *função* e *ID do Telegram*.\n\n"
            "Esses dados são utilizados **exclusivamente para comunicação administrativa e operacional** "
            "das Casas de Oração da nossa região.\n\n"
            "Eles **não serão compartilhados com terceiros** e são tratados conforme a "
            "**Lei Geral de Proteção de Dados (LGPD – Lei nº 13.709/2018)**.\n\n"
            "Ao continuar, você autoriza o uso dessas informações para envio de mensagens "
            "relacionadas à sua função ou responsabilidade.\n\n"
            "Você pode solicitar a exclusão dos seus dados a qualquer momento usando o comando:\n"
            "*/remover*\n\n"
            "Para ver a política de privacidade completa, use o comando */privacidade*\n\n"
            "Se estiver de acordo, clique no botão abaixo para continuar com o cadastro.",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        return ConversationHandler.END
    
    # Limpar dados pendentes
    if 'cadastro_temp' in context.user_data:
        del context.user_data['cadastro_temp']
    
    context.user_data['cadastro_temp'] = {'pagina_igreja': 0}
    
    logger.info(f"Iniciando cadastro para usuário {update.effective_user.id}")
    await mostrar_menu_igrejas(update, context)
    return SELECIONAR_IGREJA

async def processar_aceite_lgpd_cadastro(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Processa o aceite dos termos de LGPD para cadastro"""
    query = update.callback_query
    await query.answer()
    
    if query.data == "aceitar_lgpd_cadastro":
        context.user_data['aceitou_lgpd'] = True
        
        await query.edit_message_text(
            "*A Santa Paz de Deus!*\n\n"
            "✅ *Agradecemos por aceitar os termos!*\n\n"
            "Agora podemos prosseguir com seu cadastro.\n"
            "Por favor, use o comando /cadastrar novamente para iniciar o processo.\n\n"
            "_Deus te abençoe!_ 🙏",
            parse_mode='Markdown'
        )

async def cadastro_comando(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Redireciona para o cadastro em etapas"""
    return await iniciar_cadastro_etapas(update, context)

# ==================== FUNÇÕES DE MENU ====================
async def mostrar_menu_igrejas(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Mostra o menu de seleção de igrejas paginado"""
    igrejas_paginadas = agrupar_igrejas()
    pagina_atual = context.user_data['cadastro_temp'].get('pagina_igreja', 0)
    
    if pagina_atual >= len(igrejas_paginadas):
        pagina_atual = 0
    elif pagina_atual < 0:
        pagina_atual = len(igrejas_paginadas) - 1
    
    context.user_data['cadastro_temp']['pagina_igreja'] = pagina_atual
    
    keyboard = []
    for igreja in igrejas_paginadas[pagina_atual]:
        callback_data = f"igreja_{igreja['codigo']}"
        keyboard.append([InlineKeyboardButton(
            f"{igreja['codigo']} - {igreja['nome']}", 
            callback_data=callback_data
        )])
    
    # Botões de navegação
    nav_buttons = []
    if len(igrejas_paginadas) > 1:
        nav_buttons.append(InlineKeyboardButton("⬅️ Anterior", callback_data="igreja_anterior"))
        nav_buttons.append(InlineKeyboardButton("Próxima ➡️", callback_data="igreja_proxima"))
    keyboard.append(nav_buttons)
    
    # Botão CANCELAR
    keyboard.append([InlineKeyboardButton("❌ Cancelar", callback_data="cancelar_cadastro")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    texto_mensagem = (
        "*A Santa Paz de Deus!*\n\n"
        "Vamos iniciar o cadastro da Casa de Oração.\n\n"
        "Por favor, selecione a Casa de Oração:\n\n"
        f"📄 *Página {pagina_atual + 1}/{len(igrejas_paginadas)}*"
    )
    
    if isinstance(update, Update):
        await update.message.reply_text(texto_mensagem, reply_markup=reply_markup, parse_mode='Markdown')
    else:
        await update.edit_message_text(texto_mensagem, reply_markup=reply_markup, parse_mode='Markdown')

async def mostrar_menu_funcoes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Mostra o menu de seleção de funções"""
    funcoes_paginadas = agrupar_funcoes()
    pagina_atual = context.user_data['cadastro_temp'].get('pagina_funcao', 0)
    
    if pagina_atual >= len(funcoes_paginadas):
        pagina_atual = 0
    elif pagina_atual < 0:
        pagina_atual = len(funcoes_paginadas) - 1
    
    context.user_data['cadastro_temp']['pagina_funcao'] = pagina_atual
    
    keyboard = []
    for funcao in funcoes_paginadas[pagina_atual]:
        callback_data = f"funcao_{funcao}"
        keyboard.append([InlineKeyboardButton(funcao, callback_data=callback_data)])
    
    # Botões de navegação
    nav_buttons = []
    if len(funcoes_paginadas) > 1:
        nav_buttons.append(InlineKeyboardButton("⬅️ Anterior", callback_data="funcao_anterior"))
        nav_buttons.append(InlineKeyboardButton("Próxima ➡️", callback_data="funcao_proxima"))
    keyboard.append(nav_buttons)
    
    # Botão "Outra Função"
    keyboard.append([InlineKeyboardButton("🔄 Outra Função", callback_data="funcao_outra")])
    
    # Botão CANCELAR
    keyboard.append([InlineKeyboardButton("❌ Cancelar", callback_data="cancelar_cadastro")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    texto_mensagem = (
        "*A Paz de Deus!*\n\n"
        f"✅ Nome registrado: *{context.user_data['cadastro_temp']['nome']}*\n\n"
        "Agora, selecione a função do responsável:\n\n"
        f"📄 *Página {pagina_atual + 1}/{len(funcoes_paginadas)}*"
    )
    
    if isinstance(update, Update):
        await update.message.reply_text(texto_mensagem, reply_markup=reply_markup, parse_mode='Markdown')
    else:
        await update.edit_message_text(texto_mensagem, reply_markup=reply_markup, parse_mode='Markdown')

# ==================== HANDLERS DE CALLBACK CORRIGIDOS ====================
async def processar_callback_igreja(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """CORRIGIDO: Processa todos os callbacks relacionados a igrejas"""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    logger.info(f"Callback igreja recebido: {data}")
    
    if data == "cancelar_cadastro":
        return await cancelar_cadastro(update, context)
    
    elif data == "igreja_anterior":
        context.user_data['cadastro_temp']['pagina_igreja'] -= 1
        await mostrar_menu_igrejas(query, context)
        return SELECIONAR_IGREJA
    
    elif data == "igreja_proxima":
        context.user_data['cadastro_temp']['pagina_igreja'] += 1
        await mostrar_menu_igrejas(query, context)
        return SELECIONAR_IGREJA
    
    elif data.startswith("igreja_BR"):
        codigo_igreja = data.replace("igreja_", "")
        igreja = obter_igreja_por_codigo(codigo_igreja)
        
        if igreja:
            context.user_data['cadastro_temp']['codigo'] = igreja['codigo']
            context.user_data['cadastro_temp']['nome_igreja'] = igreja['nome']
            
            logger.info(f"Igreja selecionada: {igreja['codigo']} - {igreja['nome']}")
            
            await query.edit_message_text(
                f"*A Paz de Deus!*\n\n"
                f"✅ Casa de Oração selecionada: *{igreja['codigo']} - {igreja['nome']}*\n\n"
                f"Agora, DIGITE O NOME DO RESPONSÁVEL:",
                parse_mode='Markdown'
            )
            return NOME
    
    # Fallback
    logger.warning(f"Callback igreja não reconhecido: {data}")
    await mostrar_menu_igrejas(query, context)
    return SELECIONAR_IGREJA

async def processar_callback_funcao(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """CORRIGIDO: Processa todos os callbacks relacionados a funções"""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    logger.info(f"Callback função recebido: {data}")
    
    if data == "cancelar_cadastro":
        return await cancelar_cadastro(update, context)
    
    elif data == "funcao_anterior":
        context.user_data['cadastro_temp']['pagina_funcao'] -= 1
        await mostrar_menu_funcoes(query, context)
        return SELECIONAR_FUNCAO
    
    elif data == "funcao_proxima":
        context.user_data['cadastro_temp']['pagina_funcao'] += 1
        await mostrar_menu_funcoes(query, context)
        return SELECIONAR_FUNCAO
    
    elif data == "funcao_outra":
        await query.edit_message_text(
            "*A Santa Paz de Deus!*\n\n"
            "✍️ **DIGITE A FUNÇÃO QUE VOCÊ EXERCE NA CASA DE ORAÇÃO:**\n\n"
            "*(Exemplo: Patrimônio, Encarregado da Limpeza, Tesoureiro, Secretário, etc.)*\n\n"
            "📝 *Observação:* Se sua função já estiver disponível nos botões acima, "
            "será solicitado que você a selecione pelos botões.",
            parse_mode='Markdown'
        )
        return FUNCAO
    
    elif data.startswith("funcao_") and not data.endswith(("_anterior", "_proxima", "_outra")):
        funcao = data.replace("funcao_", "")
        
        if funcao not in FUNCOES:
            logger.warning(f"Função não reconhecida: {funcao}")
            await mostrar_menu_funcoes(query, context)
            return SELECIONAR_FUNCAO
        
        context.user_data['cadastro_temp']['funcao'] = funcao
        logger.info(f"Função selecionada: {funcao}")
        
        # Mostrar confirmação
        codigo = context.user_data['cadastro_temp']['codigo']
        nome = context.user_data['cadastro_temp']['nome']
        nome_igreja = context.user_data['cadastro_temp']['nome_igreja']
        
        keyboard = [
            [
                InlineKeyboardButton("✅ Confirmar Cadastro", callback_data="confirmar_etapas"),
                InlineKeyboardButton("❌ Cancelar", callback_data="cancelar_etapas")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "*A Santa Paz de Deus!*\n\n"
            "📝 *Confirme os dados do cadastro:*\n\n"
            f"📍 *Código:* `{codigo}`\n"
            f"🏢 *Casa:* `{nome_igreja}`\n"
            f"👤 *Nome:* `{nome}`\n"
            f"🔧 *Função:* `{funcao}`\n\n"
            "Os dados estão corretos?",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        return CONFIRMAR
    
    # Fallback
    logger.warning(f"Callback função não reconhecido: {data}")
    await mostrar_menu_funcoes(query, context)
    return SELECIONAR_FUNCAO

# ==================== HANDLERS DE ENTRADA DE TEXTO ====================
async def receber_nome(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Recebe o nome e solicita a função"""
    nome = update.message.text.strip()
    
    if len(nome) < 3:
        await update.message.reply_text("❌ Por favor, digite um nome válido com pelo menos 3 caracteres.")
        return NOME
    
    context.user_data['cadastro_temp']['nome'] = nome
    logger.info(f"Nome recebido: {nome}")
    
    context.user_data['cadastro_temp']['pagina_funcao'] = 0
    await mostrar_menu_funcoes(update, context)
    return SELECIONAR_FUNCAO

async def receber_funcao(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Recebe a função digitada manualmente"""
    funcao = update.message.text.strip()
    
    if len(funcao) < 3:
        await update.message.reply_text("❌ Por favor, digite uma função válida com pelo menos 3 caracteres.")
        return FUNCAO
    
    if not re.search(r'[a-zA-ZÀ-ÿ]', funcao):
        await update.message.reply_text("❌ Por favor, digite uma função válida que contenha letras.")
        return FUNCAO
    
    # Validação inteligente
    funcao_similar_encontrada, funcao_oficial = detectar_funcao_similar(funcao)
    
    if funcao_similar_encontrada:
        keyboard = [
            [InlineKeyboardButton("🔄 Voltar ao Menu de Funções", callback_data="voltar_menu_funcoes")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            f"⚠️ *Função já disponível nos botões!*\n\n"
            f"Você digitou: *\"{funcao}\"*\n\n"
            f"Esta função é similar a: *\"{funcao_oficial}\"*\n"
            f"que já está disponível nos botões do menu.\n\n"
            f"🔹 *Por favor, use o botão do menu para selecionar* *\"{funcao_oficial}\"*",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        return FUNCAO
    
    context.user_data['cadastro_temp']['funcao'] = funcao
    logger.info(f"Função digitada aprovada: {funcao}")
    
    # Mostrar confirmação
    keyboard = [
        [
            InlineKeyboardButton("✅ Confirmar Cadastro", callback_data="confirmar_etapas"),
            InlineKeyboardButton("❌ Cancelar", callback_data="cancelar_etapas")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    codigo = context.user_data['cadastro_temp']['codigo']
    nome = context.user_data['cadastro_temp']['nome']
    nome_igreja = context.user_data['cadastro_temp']['nome_igreja']
    
    await update.message.reply_text(
        "*A Paz de Deus!*\n\n"
        "📝 *Confirme os dados do cadastro:*\n\n"
        f"📍 *Código:* `{codigo}`\n"
        f"🏢 *Casa:* `{nome_igreja}`\n"
        f"👤 *Nome:* `{nome}`\n"
        f"🔧 *Função:* `{funcao}`\n\n"
        "Os dados estão corretos?",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )
    return CONFIRMAR

async def processar_voltar_menu_funcoes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Processa volta ao menu de funções"""
    query = update.callback_query
    await query.answer()
    
    if 'cadastro_temp' in context.user_data:
        context.user_data['cadastro_temp'].pop('funcao_digitada_similar', None)
        context.user_data['cadastro_temp']['pagina_funcao'] = 0
    
    await mostrar_menu_funcoes(query, context)
    return SELECIONAR_FUNCAO

# ==================== CONFIRMAÇÃO FINAL ====================
async def confirmar_etapas(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Processa a confirmação do cadastro"""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    logger.info(f"Callback confirmação: {data}")
    
    if data == "cancelar_etapas":
        return await cancelar_cadastro(update, context)
    
    if data == "confirmar_etapas":
        # Processar cadastro
        codigo = context.user_data['cadastro_temp'].get('codigo', '')
        nome = context.user_data['cadastro_temp'].get('nome', '')
        funcao = context.user_data['cadastro_temp'].get('funcao', '')
        nome_igreja = context.user_data['cadastro_temp'].get('nome_igreja', '')
        user_id = update.effective_user.id
        username = update.effective_user.username or ""
        
        # Verificar cadastro existente
        cadastro_existente = verificar_cadastro_existente_detalhado(codigo, nome)
        
        if cadastro_existente and cadastro_existente['user_id'] != user_id:
            await query.edit_message_text(
                "*A Paz de Deus!*\n\n"
                "⚠️ *Nome já cadastrado nesta igreja!*\n\n"
                f"📍 *Código:* `{codigo}`\n"
                f"🏢 *Casa:* `{nome_igreja}`\n"
                f"👤 *Nome:* `{nome}`\n"
                f"🔧 *Função já cadastrada:* `{cadastro_existente['funcao']}`\n\n"
                "❌ *Não é possível cadastrar o mesmo nome duas vezes na mesma igreja.*\n\n"
                "Se você é realmente esta pessoa, entre em contato com o administrador.\n\n"
                "_Deus te abençoe!_ 🙏",
                parse_mode='Markdown'
            )
            
            if 'cadastro_temp' in context.user_data:
                del context.user_data['cadastro_temp']
            return ConversationHandler.END
        
        # Salvar cadastro
        try:
            sucesso, status = inserir_cadastro(codigo, nome, funcao, user_id, username)
            
            if sucesso:
                if status.startswith("funcao_atualizada"):
                    partes = status.split("|")
                    funcao_antiga = partes[1] if len(partes) > 1 else "Desconhecida"
                    funcao_nova = partes[2] if len(partes) > 2 else funcao
                    
                    await query.edit_message_text(
                        f"*Projeto Débito Automático*\n\n"
                        f"✅ *Função atualizada com sucesso!*\n\n"
                        f"📍 *Código:* `{codigo}`\n"
                        f"🏢 *Casa:* `{nome_igreja}`\n"
                        f"👤 *Nome:* `{nome}`\n"
                        f"🔧 *Função anterior:* `{funcao_antiga}`\n"
                        f"🔧 *Nova função:* `{funcao_nova}`\n\n"
                        f"📢 Os alertas automáticos de consumo continuarão sendo enviados para você.\n\n"
                        f"_Deus te abençoe!_ 🙌",
                        parse_mode='Markdown'
                    )
                else:
                    await query.edit_message_text(
                        f"*Projeto Débito Automático*\n\n"
                        f"✅ *Cadastro recebido com sucesso:*\n\n"
                        f"📍 *Código:* `{codigo}`\n"
                        f"🏢 *Casa:* `{nome_igreja}`\n"
                        f"👤 *Nome:* `{nome}`\n"
                        f"🔧 *Função:* `{funcao}`\n\n"
                        f"🗂️ Estamos em *fase de cadastro* dos irmãos responsáveis pelo acompanhamento das Contas de Consumo.\n"
                        f"📢 Assim que esta fase for concluída, os *alertas automáticos de consumo* começarão a ser enviados.\n\n"
                        f"_Deus te abençoe!_ 🙌",
                        parse_mode='Markdown'
                    )
            else:
                await query.edit_message_text(
                    "*A Paz de Deus!*\n\n"
                    "❌ *Houve um problema ao processar seu cadastro!*\n\n"
                    "Por favor, tente novamente mais tarde ou entre em contato com o administrador.\n\n"
                    "_Deus te abençoe!_ 🙏",
                    parse_mode='Markdown'
                )
        except Exception as e:
            logger.error(f"Erro ao salvar cadastro: {str(e)}")
            await query.edit_message_text(
                "*A Paz de Deus!*\n\n"
                "❌ *Houve um problema ao processar seu cadastro!*\n\n"
                "Por favor, tente novamente mais tarde ou entre em contato com o administrador.\n\n"
                "_Deus te abençoe!_ 🙏",
                parse_mode='Markdown'
            )
        
        # Limpar contexto
        if 'cadastro_temp' in context.user_data:
            del context.user_data['cadastro_temp']
        
        return ConversationHandler.END

# ==================== REGISTRO DOS HANDLERS CORRIGIDO ====================
def registrar_handlers_cadastro(application):
    """Registra handlers relacionados ao cadastro - VERSÃO CORRIGIDA"""
    
    # Handler para comando cadastro
    application.add_handler(CommandHandler("cadastro", cadastro_comando))
    
    # Handler para aceite LGPD
    application.add_handler(CallbackQueryHandler(
        processar_aceite_lgpd_cadastro, 
        pattern='^aceitar_lgpd_cadastro$'
    ))
    
    # ConversationHandler CORRIGIDO
    cadastro_handler = ConversationHandler(
        entry_points=[
            CommandHandler("cadastrar", iniciar_cadastro_etapas),
            MessageHandler(filters.Regex(r"^(🖋️ Cadastrar Responsável|📝 CADASTRAR RESPONSÁVEL 📝)$"), iniciar_cadastro_etapas)
        ],
        states={
            SELECIONAR_IGREJA: [
                # CORRIGIDO: Callbacks específicos para cada ação
                CallbackQueryHandler(processar_callback_igreja, pattern=r'^igreja_anterior$'),
                CallbackQueryHandler(processar_callback_igreja, pattern=r'^igreja_proxima$'),
                CallbackQueryHandler(processar_callback_igreja, pattern=r'^igreja_BR'),
                CallbackQueryHandler(processar_callback_igreja, pattern=r'^cancelar_cadastro$'),
            ],
            NOME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receber_nome)
            ],
            SELECIONAR_FUNCAO: [
                # CORRIGIDO: Callbacks específicos para cada ação
                CallbackQueryHandler(processar_callback_funcao, pattern=r'^funcao_anterior$'),
                CallbackQueryHandler(processar_callback_funcao, pattern=r'^funcao_proxima$'),
                CallbackQueryHandler(processar_callback_funcao, pattern=r'^funcao_outra$'),
                CallbackQueryHandler(processar_callback_funcao, pattern=r'^funcao_(?!anterior|proxima|outra)'),
                CallbackQueryHandler(processar_callback_funcao, pattern=r'^cancelar_cadastro$'),
            ],
            FUNCAO: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receber_funcao),
                CallbackQueryHandler(processar_voltar_menu_funcoes, pattern=r'^voltar_menu_funcoes$')
            ],
            CONFIRMAR: [
                CallbackQueryHandler(confirmar_etapas, pattern=r'^(confirmar|cancelar)_etapas$')
            ]
        },
        fallbacks=[
            CommandHandler("cancelar", cancelar_cadastro),
            CallbackQueryHandler(cancelar_cadastro, pattern=r'^cancelar_cadastro$')
        ],
        name="cadastro_conversation",
        persistent=False
    )
    
    application.add_handler(cadastro_handler)
    logger.info("✅ Handlers de cadastro registrados - NAVEGAÇÃO CORRIGIDA")v
