#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Handlers para processamento de mensagens de texto do CCB Alerta Bot
"""

from telegram import Update
from telegram.ext import MessageHandler, filters, ContextTypes

from handlers.commands import mensagem_boas_vindas
from utils import verificar_formato_cadastro

async def processar_mensagem(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Processa mensagens de texto e orienta o usuário
    
    Esta função é chamada quando o usuário envia uma mensagem que não é um comando.
    Verifica se o texto parece uma tentativa de cadastro e orienta o usuário
    sobre como proceder corretamente.
    """
    texto = update.message.text.strip()
    
    # Mostrar ID do usuário para ajudar na depuração
    user_id = update.effective_user.id
    print(f"Mensagem recebida do usuário ID: {user_id}, Username: @{update.effective_user.username}")
    
    # Se parece com uma tentativa de cadastro no formato antigo
    if "/" in texto and ("BR" in texto.upper() or "-" in texto):
        await update.message.reply_text(
            "🕊️ *A Santa Paz de Deus!*\n\n"
            "📝 *Nova forma de cadastro!*\n\n"
            "Temos um processo mais simples para cadastro.\n\n"
            "Por favor, digite */cadastrar* e siga as instruções passo a passo.\n\n"
            "Ou, se preferir o formato manual, use:\n"
            "`/cadastro BR21-0000 / Nome Completo / Função`\n\n"
            "_Deus te abençoe!_ 🙏",
            parse_mode='Markdown'
        )
    else:
        # Se não parece um cadastro, envia a mensagem de boas-vindas
        await mensagem_boas_vindas(update, context)

def registrar_handlers_mensagens(application):
    """Registra handlers para mensagens de texto"""
    # Handler para mensagens de texto que não são comandos
    application.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND, 
        processar_mensagem
    ))