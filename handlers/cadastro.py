#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Handlers para o processo de cadastro do CCB Alerta Bot
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
from utils import salvar_cadastro, verificar_cadastro_existente
from handlers.data import IGREJAS, FUNCOES, agrupar_igrejas, agrupar_funcoes, obter_igreja_por_codigo

# Logger
logger = logging.getLogger(__name__)

# Estados adicionais para a navegação nos menus
SELECIONAR_IGREJA, SELECIONAR_FUNCAO = range(4, 6)

async def iniciar_cadastro_etapas(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Inicia o processo de cadastro passo a passo"""
    # Limpar qualquer dado pendente do contexto
    if 'cadastro_temp' in context.user_data:
        del context.user_data['cadastro_temp']
    
    context.user_data['cadastro_temp'] = {'pagina_igreja': 0}
    
    logger.info(f"Iniciando cadastro para usuário {update.effective_user.id}")
    await mostrar_menu_igrejas(update, context)
    return SELECIONAR_IGREJA

async def mostrar_menu_igrejas(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Mostra o menu de seleção de igrejas paginado"""
    # Agrupar igrejas em páginas
    igrejas_paginadas = agrupar_igrejas()
    pagina_atual = context.user_data['cadastro_temp'].get('pagina_igreja', 0)
    
    # Verificar limites da página
    if pagina_atual >= len(igrejas_paginadas):
        pagina_atual = 0
    elif pagina_atual < 0:
        pagina_atual = len(igrejas_paginadas) - 1
    
    context.user_data['cadastro_temp']['pagina_igreja'] = pagina_atual
    
    # Preparar botões para a página atual
    keyboard = []
    for igreja in igrejas_paginadas[pagina_atual]:
        # Criar callback data para este botão
        callback_data = f"igreja_{igreja['codigo']}"
        
        # Log para depuração
        logger.info(f"Criando botão com callback_data: {callback_data}")
        
        keyboard.append([InlineKeyboardButton(
            f"{igreja['codigo']} - {igreja['nome']}", 
            callback_data=callback_data
        )])
    
    # Adicionar botões de navegação
    nav_buttons = []
    if len(igrejas_paginadas) > 1:
        nav_buttons.append(InlineKeyboardButton("⬅️ Anterior", callback_data="igreja_anterior"))
        nav_buttons.append(InlineKeyboardButton("Próxima ➡️", callback_data="igreja_proxima"))
    keyboard.append(nav_buttons)
    
    # Botão para cancelar
    keyboard.append([InlineKeyboardButton("❌ Cancelar", callback_data="cancelar_cadastro")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Criar ou editar mensagem dependendo do contexto
    texto_mensagem = (
        "🕊️ *A Santa Paz de Deus!*\n\n"
        "Vamos iniciar o cadastro da Casa de Oração.\n\n"
        "Por favor, selecione a Casa de Oração:\n\n"
        f"📄 *Página {pagina_atual + 1}/{len(igrejas_paginadas)}*"
    )
    
    # Verificar se é atualização ou primeira exibição
    if isinstance(update, Update):
        # Primeira exibição
        await update.message.reply_text(
            texto_mensagem,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    else:
        # Atualização via callback
        await update.edit_message_text(
            texto_mensagem,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )

async def processar_selecao_igreja(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Processa a seleção ou navegação no menu de igrejas"""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    logger.info(f"Callback recebido: {data}")
    
    if data == "cancelar_cadastro":
        # Limpar dados do contexto
        if 'cadastro_temp' in context.user_data:
            del context.user_data['cadastro_temp']
        
        await query.edit_message_text(
            "🕊️ *A Santa Paz de Deus!*\n\n"
            "❌ *Cadastro cancelado!*\n\n"
            "Você pode iniciar novamente quando quiser usando /cadastrar.\n\n"
            "_Deus te abençoe!_ 🙏",
            parse_mode='Markdown'
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
            
            # Continuar para a próxima etapa (nome do responsável)
            await query.edit_message_text(
                f"🕊️ *A Santa Paz de Deus!*\n\n"
                f"✅ Casa de Oração selecionada: *{igreja['codigo']} - {igreja['nome']}*\n\n"
                f"Agora, digite o nome do responsável:",
                parse_mode='Markdown'
            )
            return NOME
    
    # Fallback - mostrar menu novamente
    logger.warning(f"Callback data não reconhecido: {data}")
    await mostrar_menu_igrejas(query, context)
    return SELECIONAR_IGREJA

async def receber_nome(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Recebe o nome e solicita a função"""
    nome = update.message.text.strip()
    
    # Validação básica
    if len(nome) < 3:
        await update.message.reply_text(
            "❌ Por favor, digite um nome válido com pelo menos 3 caracteres."
        )
        return NOME
    
    # Armazenar temporariamente
    context.user_data['cadastro_temp']['nome'] = nome
    logger.info(f"Nome recebido: {nome}")
    
    # Preparar e mostrar menu de funções
    context.user_data['cadastro_temp']['pagina_funcao'] = 0
    await mostrar_menu_funcoes(update, context)
    return SELECIONAR_FUNCAO

async def mostrar_menu_funcoes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Mostra o menu de seleção de funções"""
    # Agrupar funções em páginas
    funcoes_paginadas = agrupar_funcoes()
    pagina_atual = context.user_data['cadastro_temp'].get('pagina_funcao', 0)
    
    # Verificar limites da página
    if pagina_atual >= len(funcoes_paginadas):
        pagina_atual = 0
    elif pagina_atual < 0:
        pagina_atual = len(funcoes_paginadas) - 1
    
    context.user_data['cadastro_temp']['pagina_funcao'] = pagina_atual
    
    # Preparar botões para a página atual
    keyboard = []
    for funcao in funcoes_paginadas[pagina_atual]:
        callback_data = f"funcao_{funcao}"
        logger.info(f"Criando botão de função com callback_data: {callback_data}")
        
        keyboard.append([InlineKeyboardButton(
            funcao,
            callback_data=callback_data
        )])
    
    # Adicionar botões de navegação
    nav_buttons = []
    if len(funcoes_paginadas) > 1:
        nav_buttons.append(InlineKeyboardButton("⬅️ Anterior", callback_data="funcao_anterior"))
        nav_buttons.append(InlineKeyboardButton("Próxima ➡️", callback_data="funcao_proxima"))
    keyboard.append(nav_buttons)
    
    # Botão para outras funções
    keyboard.append([InlineKeyboardButton("🔄 Outra Função", callback_data="funcao_outra")])
    
    # Botão para cancelar
    keyboard.append([InlineKeyboardButton("❌ Cancelar", callback_data="cancelar_cadastro")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Criar ou editar mensagem dependendo do contexto
    texto_mensagem = (
        "🕊️ *A Santa Paz de Deus!*\n\n"
        f"✅ Nome registrado: *{context.user_data['cadastro_temp']['nome']}*\n\n"
        "Agora, selecione a função do responsável:\n\n"
        f"📄 *Página {pagina_atual + 1}/{len(funcoes_paginadas)}*"
    )
    
    # Verificar se é atualização ou primeira exibição
    if isinstance(update, Update):
        # Primeira exibição
        await update.message.reply_text(
            texto_mensagem,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    else:
        # Atualização via callback
        await update.edit_message_text(
            texto_mensagem,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )

async def processar_selecao_funcao(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Processa a seleção ou navegação no menu de funções"""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    logger.info(f"Callback de função recebido: {data}")
    
    if data == "cancelar_cadastro":
        # Limpar dados do contexto
        if 'cadastro_temp' in context.user_data:
            del context.user_data['cadastro_temp']
        
        await query.edit_message_text(
            "🕊️ *A Santa Paz de Deus!*\n\n"
            "❌ *Cadastro cancelado!*\n\n"
            "Você pode iniciar novamente quando quiser usando /cadastrar.\n\n"
            "_Deus te abençoe!_ 🙏",
            parse_mode='Markdown'
        )
        return ConversationHandler.END
    
    if data == "funcao_anterior":
        # Navegar para a página anterior
        context.user_data['cadastro_temp']['pagina_funcao'] -= 1
        await mostrar_menu_funcoes(query, context)
        return SELECIONAR_FUNCAO
    
    if data == "funcao_proxima":
        # Navegar para a próxima página
        context.user_data['cadastro_temp']['pagina_funcao'] += 1
        await mostrar_menu_funcoes(query, context)
        return SELECIONAR_FUNCAO
    
    if data == "funcao_outra":
        # Solicitar entrada manual da função
        await query.edit_message_text(
            f"🕊️ *A Santa Paz de Deus!*\n\n"
            f"Por favor, digite a função do responsável (Exemplo: Cooperador, Diácono, etc.):",
            parse_mode='Markdown'
        )
        return FUNCAO
    
    # Selecionar função
    if data.startswith("funcao_"):
        funcao = data.replace("funcao_", "")
        
        # Armazenar função
        context.user_data['cadastro_temp']['funcao'] = funcao
        logger.info(f"Função selecionada: {funcao}")
        
        # Continuar para confirmação
        codigo = context.user_data['cadastro_temp']['codigo']
        nome = context.user_data['cadastro_temp']['nome']
        nome_igreja = context.user_data['cadastro_temp']['nome_igreja']
        
        # Preparar botões de confirmação
        keyboard = [
            [
                InlineKeyboardButton("✅ Confirmar Cadastro", callback_data="confirmar_etapas"),
                InlineKeyboardButton("❌ Cancelar", callback_data="cancelar_etapas")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "🕊️ *A Santa Paz de Deus!*\n\n"
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
    
    # Fallback - mostrar menu novamente
    logger.warning(f"Callback de função não reconhecido: {data}")
    await mostrar_menu_funcoes(query, context)
    return SELECIONAR_FUNCAO

async def receber_funcao(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Recebe a função digitada manualmente e mostra resumo para confirmação"""
    funcao = update.message.text.strip()
    
    # Validação básica
    if len(funcao) < 3:
        await update.message.reply_text(
            "❌ Por favor, digite uma função válida com pelo menos 3 caracteres."
        )
        return FUNCAO
    
    # Armazenar temporariamente
    context.user_data['cadastro_temp']['funcao'] = funcao
    logger.info(f"Função digitada: {funcao}")
    
    # Preparar botões de confirmação
    keyboard = [
        [
            InlineKeyboardButton("✅ Confirmar Cadastro", callback_data="confirmar_etapas"),
            InlineKeyboardButton("❌ Cancelar", callback_data="cancelar_etapas")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Extrair dados do cadastro
    codigo = context.user_data['cadastro_temp']['codigo']
    nome = context.user_data['cadastro_temp']['nome']
    nome_igreja = context.user_data['cadastro_temp']['nome_igreja']
    
    await update.message.reply_text(
        "🕊️ *A Santa Paz de Deus!*\n\n"
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

async def confirmar_etapas(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Processa a confirmação do cadastro em etapas"""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    logger.info(f"Callback de confirmação: {data}")
    
    if data == "cancelar_etapas":
        # Limpar dados do contexto
        if 'cadastro_temp' in context.user_data:
            del context.user_data['cadastro_temp']
        
        await query.edit_message_text(
            "🕊️ *A Santa Paz de Deus!*\n\n"
            "❌ *Cadastro cancelado!*\n\n"
            "Você pode iniciar novamente quando quiser usando /cadastrar.\n\n"
            "_Deus te abençoe!_ 🙏",
            parse_mode='Markdown'
        )
        return ConversationHandler.END
    
    # Obter dados do contexto
    codigo = context.user_data['cadastro_temp'].get('codigo', '')
    nome = context.user_data['cadastro_temp'].get('nome', '')
    funcao = context.user_data['cadastro_temp'].get('funcao', '')
    nome_igreja = context.user_data['cadastro_temp'].get('nome_igreja', '')
    
    # Verificar se já existe cadastro exatamente igual
    if verificar_cadastro_existente(codigo, nome, funcao):
        await query.edit_message_text(
            "🕊️ *A Santa Paz de Deus!*\n\n"
            "⚠️ *Atenção!*\n\n"
            f"Já existe um cadastro para a Casa de Oração *{codigo}* com o nome *{nome}* e função *{funcao}*.\n\n"
            "Por favor, verifique os dados ou entre em contato com o administrador.\n\n"
            "_Deus te abençoe!_ 🙏",
            parse_mode='Markdown'
        )
        # Limpar dados do contexto
        if 'cadastro_temp' in context.user_data:
            del context.user_data['cadastro_temp']
        return ConversationHandler.END
    
    # Salvar cadastro
    sucesso, status = salvar_cadastro(codigo, nome, funcao, 
                                     update.effective_user.id, 
                                     update.effective_user.username or "")
    
    if not sucesso:
        await query.edit_message_text(
            "🕊️ *A Santa Paz de Deus!*\n\n"
            "❌ *Houve um problema ao processar seu cadastro!*\n\n"
            "Por favor, tente novamente mais tarde ou entre em contato com o administrador.\n\n"
            "_Deus te abençoe!_ 🙏",
            parse_mode='Markdown'
        )
        # Limpar dados do contexto
        if 'cadastro_temp' in context.user_data:
            del context.user_data['cadastro_temp']
        return ConversationHandler.END
    
    # Sucesso
    await query.edit_message_text(
        f"🕊️ *A Santa Paz de Deus!*\n\n"
        f"✅ *Cadastro recebido com sucesso:*\n\n"
        f"📍 *Código:* `{codigo}`\n"
        f"🏢 *Casa:* `{nome_igreja}`\n"
        f"👤 *Nome:* `{nome}`\n"
        f"🔧 *Função:* `{funcao}`\n\n"
        f"🗂️ Estamos em *fase de cadastro* dos irmãos responsáveis pelo acompanhamento.\n"
        f"📢 Assim que esta fase for concluída, os *alertas automáticos de consumo* começarão a ser enviados.\n\n"
        f"_Deus te abençoe!_ 🙌",
        parse_mode='Markdown'
    )
    
    # Limpar dados do contexto
    if 'cadastro_temp' in context.user_data:
        del context.user_data['cadastro_temp']
    return ConversationHandler.END

async def cancelar_cadastro(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancela o cadastro em qualquer etapa"""
    # Limpar dados do contexto
    if 'cadastro_temp' in context.user_data:
        del context.user_data['cadastro_temp']
    
    # Verificar se é callback ou comando
    if hasattr(update, 'callback_query'):
        await update.callback_query.edit_message_text(
            "🕊️ *A Santa Paz de Deus!*\n\n"
            "❌ *Cadastro cancelado!*\n\n"
            "Você pode iniciar novamente quando quiser usando /cadastrar.\n\n"
            "_Deus te abençoe!_ 🙏",
            parse_mode='Markdown'
        )
    else:
        await update.message.reply_text(
            "🕊️ *A Santa Paz de Deus!*\n\n"
            "❌ *Cadastro cancelado!*\n\n"
            "Você pode iniciar novamente quando quiser usando /cadastrar.\n\n"
            "_Deus te abençoe!_ 🙏",
            parse_mode='Markdown'
        )
    return ConversationHandler.END

async def cadastro_comando(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Processa cadastro enviado via comando /cadastro"""
    texto = update.message.text.replace('/cadastro', '').strip()
    
    # Verificar se há dados após o comando
    if not texto:
        await update.message.reply_text(
            "🕊️ *A Santa Paz de Deus!*\n\n"
            "📝 *Cadastro Manual*\n\n"
            "Para cadastrar manualmente, envie no formato:\n"
            "`/cadastro BR21-0000 / Nome Completo / Função`\n\n"
            "Exemplo:\n"
            "`/cadastro BR21-0270 / João Silva / Cooperador`\n\n"
            "Ou utilize o comando */cadastrar* para o processo guiado passo a passo.\n\n"
            "_Deus te abençoe!_ 🙏",
            parse_mode='Markdown'
        )
        return
    
    # Verificar formato
    if not verificar_formato_cadastro(texto):
        await update.message.reply_text(
            "🕊️ *A Santa Paz de Deus!*\n\n"
            "❌ *Formato inválido!*\n\n"
            "📝 Por favor, use o formato correto:\n"
            "`BR21-0000 / Seu Nome Completo / Sua Função`\n\n"
            "📌 *Exemplo:*\n"
            "`BR21-0270 / João Silva / Cooperador`\n\n"
            "_Deus te abençoe!_ 🙏",
            parse_mode='Markdown'
        )
        return
    
    # Extrair dados
    codigo, nome, funcao = extrair_dados_cadastro(texto)
    
    if not codigo or not nome or not funcao:
        await update.message.reply_text(
            "🕊️ *A Santa Paz de Deus!*\n\n"
            "❌ *Não foi possível processar os dados!*\n\n"
            "Por favor, verifique o formato e tente novamente.\n\n"
            "_Deus te abençoe!_ 🙏",
            parse_mode='Markdown'
        )
        return
    
    # Verificar se já existe cadastro exatamente igual
    if verificar_cadastro_existente(codigo, nome, funcao):
        await update.message.reply_text(
            "🕊️ *A Santa Paz de Deus!*\n\n"
            "⚠️ *Atenção!*\n\n"
            f"Já existe um cadastro para a Casa de Oração *{codigo}* com o nome *{nome}* e função *{funcao}*.\n\n"
            "Por favor, verifique os dados ou entre em contato com o administrador.\n\n"
            "_Deus te abençoe!_ 🙏",
            parse_mode='Markdown'
        )
        return
    
    # Salvar cadastro
    sucesso, status = salvar_cadastro(codigo, nome, funcao, 
                                     update.effective_user.id, 
                                     update.effective_user.username or "")
    
    if sucesso:
        # Obter nome da igreja
        igreja = obter_igreja_por_codigo(codigo)
        nome_igreja = igreja['nome'] if igreja else "Desconhecida"
        
        await update.message.reply_text(
            f"🕊️ *A Santa Paz de Deus!*\n\n"
            f"✅ *Cadastro recebido com sucesso:*\n\n"
            f"📍 *Código:* `{codigo}`\n"
            f"🏢 *Casa:* `{nome_igreja}`\n"
            f"👤 *Nome:* `{nome}`\n"
            f"🔧 *Função:* `{funcao}`\n\n"
            f"🗂️ Estamos em *fase de cadastro* dos irmãos responsáveis pelo acompanhamento.\n"
            f"📢 Assim que esta fase for concluída, os *alertas automáticos de consumo* começarão a ser enviados.\n\n"
            f"_Deus te abençoe!_ 🙌",
            parse_mode='Markdown'
        )
    else:
        await update.message.reply_text(
            "🕊️ *A Santa Paz de Deus!*\n\n"
            "❌ *Houve um problema ao processar seu cadastro!*\n\n"
            "Por favor, tente novamente mais tarde ou entre em contato com o administrador.\n\n"
            "_Deus te abençoe!_ 🙏",
            parse_mode='Markdown'
        )

def registrar_handlers_cadastro(application):
    """Registra handlers relacionados ao cadastro"""
    # Handler para cadastro manual via comando
    application.add_handler(CommandHandler("cadastro", cadastro_comando))
    
    # Handler para cadastro em etapas (conversation)
    cadastro_handler = ConversationHandler(
        entry_points=[
            CommandHandler("cadastrar", iniciar_cadastro_etapas),
            # Adicionar MessageHandler para processar clique no botão de menu (com ambos os formatos)
            MessageHandler(filters.Regex(r"^(🖋️ Cadastrar Responsável|📝 CADASTRAR RESPONSÁVEL 📝)$"), iniciar_cadastro_etapas)
        ],
        states={
            SELECIONAR_IGREJA: [
                # Ajustar padrão para reconhecer todos os tipos de callback de igreja
                CallbackQueryHandler(processar_selecao_igreja, pattern=r'^igreja_')
            ],
            NOME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receber_nome)
            ],
            SELECIONAR_FUNCAO: [
                CallbackQueryHandler(processar_selecao_funcao, pattern=r'^funcao_')
            ],
            FUNCAO: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receber_funcao)
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
