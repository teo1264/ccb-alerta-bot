#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Handlers para o processo de cadastro do CCB Alerta Bot
"""

import re
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    CommandHandler, MessageHandler, CallbackQueryHandler,
    ConversationHandler, ContextTypes, filters
)

from config import CODIGO, NOME, FUNCAO, CONFIRMAR
from utils import salvar_cadastro, verificar_duplicata, verificar_formato_cadastro, extrair_dados_cadastro

async def iniciar_cadastro_etapas(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Inicia o processo de cadastro passo a passo"""
    await update.message.reply_text(
        "🕊️ *A Santa Paz de Deus!*\n\n"
        "Vamos iniciar o cadastro da Casa de Oração.\n\n"
        "Digite o número da Casa de Oração (somente números):",
        parse_mode='Markdown'
    )
    return CODIGO

async def receber_codigo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Recebe o código da casa e solicita o nome"""
    numero = update.message.text.strip()
    
    # Validar se é um número
    if not numero.isdigit():
        await update.message.reply_text(
            "❌ Por favor, digite apenas números.\n\n"
            "Digite o número da Casa de Oração:"
        )
        return CODIGO
    
    # Formatar o código no padrão desejado
    codigo_formatado = f"BR21-{numero.zfill(4)}"
    
    # Verificar duplicata
    if verificar_duplicata(codigo_formatado):
        await update.message.reply_text(
            "🕊️ *A Santa Paz de Deus!*\n\n"
            "⚠️ *Atenção!*\n\n"
            f"O código da Casa de Oração *{codigo_formatado}* já está cadastrado no sistema.\n\n"
            "Por favor, verifique o número ou entre em contato com o administrador.\n\n"
            "_Deus te abençoe!_ 🙏",
            parse_mode='Markdown'
        )
        return ConversationHandler.END
    
    # Armazenar temporariamente
    context.user_data['codigo'] = codigo_formatado
    
    await update.message.reply_text(
        f"✅ Código registrado: *{codigo_formatado}*\n\n"
        "Agora, digite o nome do responsável:",
        parse_mode='Markdown'
    )
    return NOME

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
    context.user_data['nome'] = nome
    
    await update.message.reply_text(
        f"✅ Nome registrado: *{nome}*\n\n"
        "Agora, digite a função do responsável (Exemplo: Cooperador, Diácono, etc.):",
        parse_mode='Markdown'
    )
    return FUNCAO

async def receber_funcao(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Recebe a função e mostra resumo para confirmação"""
    funcao = update.message.text.strip()
    
    # Validação básica
    if len(funcao) < 3:
        await update.message.reply_text(
            "❌ Por favor, digite uma função válida com pelo menos 3 caracteres."
        )
        return FUNCAO
    
    # Armazenar temporariamente
    context.user_data['funcao'] = funcao
    
    # Preparar botões de confirmação
    keyboard = [
        [
            InlineKeyboardButton("✅ Confirmar Cadastro", callback_data="confirmar_etapas"),
            InlineKeyboardButton("❌ Cancelar", callback_data="cancelar_etapas")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "🕊️ *A Santa Paz de Deus!*\n\n"
        "📝 *Confirme os dados do cadastro:*\n\n"
        f"📍 *Código:* `{context.user_data['codigo']}`\n"
        f"👤 *Nome:* `{context.user_data['nome']}`\n"
        f"🔧 *Função:* `{context.user_data['funcao']}`\n\n"
        "Os dados estão corretos?",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )
    return CONFIRMAR

async def confirmar_etapas(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Processa a confirmação do cadastro em etapas"""
    query = update.callback_query
    await query.answer()
    
    if query.data == "cancelar_etapas":
        # Limpar dados do contexto
        context.user_data.clear()
        
        await query.edit_message_text(
            "🕊️ *A Santa Paz de Deus!*\n\n"
            "❌ *Cadastro cancelado!*\n\n"
            "Você pode iniciar novamente quando quiser usando /cadastrar.\n\n"
            "_Deus te abençoe!_ 🙏",
            parse_mode='Markdown'
        )
        return ConversationHandler.END
    
    # Obter dados do contexto
    codigo = context.user_data.get('codigo', '')
    nome = context.user_data.get('nome', '')
    funcao = context.user_data.get('funcao', '')
    
    # Salvar cadastro
    sucesso, status = salvar_cadastro(codigo, nome, funcao, 
                                     update.effective_user.id, 
                                     update.effective_user.username or "")
    
    if not sucesso and status == "duplicado":
        await query.edit_message_text(
            "🕊️ *A Santa Paz de Deus!*\n\n"
            "⚠️ *Atenção!*\n\n"
            f"O código da Casa de Oração *{codigo}* já está cadastrado no sistema.\n\n"
            "Por favor, verifique o número ou entre em contato com o administrador.\n\n"
            "_Deus te abençoe!_ 🙏",
            parse_mode='Markdown'
        )
        context.user_data.clear()
        return ConversationHandler.END
    
    if sucesso:
        await query.edit_message_text(
            f"🕊️ *A Santa Paz de Deus!*\n\n"
            f"✅ *Cadastro recebido com sucesso:*\n\n"
            f"📍 *Código:* `{codigo}`\n"
            f"👤 *Nome:* `{nome}`\n"
            f"🔧 *Função:* `{funcao}`\n\n"
            f"🗂️ Estamos em *fase de cadastro* dos irmãos responsáveis pelo acompanhamento.\n"
            f"📢 Assim que esta fase for concluída, os *alertas automáticos de consumo* começarão a ser enviados.\n\n"
            f"_Deus te abençoe!_ 🙌",
            parse_mode='Markdown'
        )
    else:
        await query.edit_message_text(
            "🕊️ *A Santa Paz de Deus!*\n\n"
            "❌ *Houve um problema ao processar seu cadastro!*\n\n"
            "Por favor, tente novamente mais tarde ou entre em contato com o administrador.\n\n"
            "_Deus te abençoe!_ 🙏",
            parse_mode='Markdown'
        )
    
    # Limpar dados do contexto
    context.user_data.clear()
    return ConversationHandler.END

async def cancelar_cadastro(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancela o cadastro em qualquer etapa"""
    # Limpar dados do contexto
    context.user_data.clear()
    
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
    
    # Salvar cadastro
    sucesso, status = salvar_cadastro(codigo, nome, funcao, 
                                     update.effective_user.id, 
                                     update.effective_user.username or "")
    
    if not sucesso and status == "duplicado":
        await update.message.reply_text(
            "🕊️ *A Santa Paz de Deus!*\n\n"
            "⚠️ *Atenção!*\n\n"
            f"O código da Casa de Oração já está cadastrado no sistema.\n\n"
            "Se precisar atualizar as informações, entre em contato com o administrador.\n\n"
            "_Deus te abençoe!_ 🙏",
            parse_mode='Markdown'
        )
        return
    
    if sucesso:
        await update.message.reply_text(
            f"🕊️ *A Santa Paz de Deus!*\n\n"
            f"✅ *Cadastro recebido com sucesso:*\n\n"
            f"📍 *Código:* `{codigo}`\n"
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
        entry_points=[CommandHandler("cadastrar", iniciar_cadastro_etapas)],
        states={
            CODIGO: [MessageHandler(filters.TEXT & ~filters.COMMAND, receber_codigo)],
            NOME: [MessageHandler(filters.TEXT & ~filters.COMMAND, receber_nome)],
            FUNCAO: [MessageHandler(filters.TEXT & ~filters.COMMAND, receber_funcao)],
            CONFIRMAR: [CallbackQueryHandler(confirmar_etapas, pattern='^(confirmar_etapas|cancelar_etapas)$')]
        },
        fallbacks=[CommandHandler("cancelar", cancelar_cadastro)]
    )
    application.add_handler(cadastro_handler)
