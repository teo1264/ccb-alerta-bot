#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Handlers para processamento de mensagens de texto do CCB Alerta Bot
"""

import re
import random
from telegram import Update
from telegram.ext import MessageHandler, filters, ContextTypes

from handlers.commands import mensagem_boas_vindas

# Expressões de louvor e suas respostas
EXPRESSOES_LOUVOR = [
    # Amém e variações
    r'\bamem\b',
    r'\bamén\b',
    r'\bamen\b',
    r'\bglória\b', 
    r'\bgloria\b',
    r'\bglória a deus\b',
    r'\bgloria a deus\b',
    r'\baleluia\b',
    r'\baleluya\b',
    r'\baleluiah\b',
    r'\bpaz de deus\b',
    r'\bsanta paz\b',
    r'\bpaz do senhor\b',
    r'\bdeus seja louvado\b',
    r'\bdeus é bom\b',
    r'\bdeus é fiel\b'
]

# Respostas inspiradoras com emojis
RESPOSTAS_LOUVOR = [
    "🕊️ Glória a Deus! ✨",
    "🙌 Amém, irmão(ã)! Deus é bom o tempo todo!",
    "✝️ A Paz de Deus! Que o Senhor te abençoe.",
    "🙏 Aleluia! Louvado seja o Senhor!",
    "🕊️ A Santa Paz! Deus seja louvado.",
    "✨ Glória a Deus nas alturas!",
    "🌿 Paz seja contigo! O Senhor te guarde.",
    "🌟 Deus é fiel! Que Ele te abençoe sempre.",
    "🙏 Amém! Que a graça do Senhor esteja contigo.",
    "🕊️ Aleluia! A paz do Senhor Jesus."
]

async def processar_mensagem(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Processa mensagens de texto e orienta o usuário
    
    Esta função é chamada quando o usuário envia uma mensagem que não é um comando.
    Verifica se o texto parece uma expressão de louvor, uma tentativa de cadastro, ou
    outra mensagem, e responde apropriadamente.
    """
    texto = update.message.text.strip().lower()
    
    # Mostrar ID do usuário para ajudar na depuração
    user_id = update.effective_user.id
    print(f"Mensagem recebida do usuário ID: {user_id}, Username: @{update.effective_user.username}")
    
    # Verificar se é uma expressão de louvor
    for padrao in EXPRESSOES_LOUVOR:
        if re.search(padrao, texto, re.IGNORECASE):
            # Escolher uma resposta aleatória
            resposta = random.choice(RESPOSTAS_LOUVOR)
            await update.message.reply_text(resposta)
            return
    
    # Se parece com uma tentativa de cadastro no formato antigo
    if "/" in texto and ("BR" in texto.upper() or "-" in texto):
        await update.message.reply_text(
            "🕊️ *A Santa Paz de Deus!*\n\n"
            "📝 *Nova forma de cadastro!*\n\n"
            "Temos um processo mais simples para cadastro.\n\n"
            "Por favor, digite */cadastrar* e siga as instruções passo a passo.\n\n"
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
