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
from handlers.cadastro import iniciar_cadastro_etapas

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
# Respostas inspiradoras com emojis apropriados
RESPOSTAS_LOUVOR = [
    "Glória a Deus!",
    "🙌 Amém, irmão(ã)! Deus é bom o tempo todo!",
    "A Paz de Deus! Que o Senhor te abençoe.",
    "🙏 Aleluia! Louvado seja o Senhor!",
    "A Santa Paz! Deus seja louvado.",
    "Glória a Deus nas alturas!",
    "A Paz de Deus! O Senhor te guarde.",
    "🙏 Deus é fiel! Que Ele te abençoe sempre.",
    "🙏 Amém! Que a graça do Senhor esteja contigo.",
    "A Paz de Deus!"
]

async def processar_mensagem(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Processa mensagens de texto e orienta o usuário
    
    Esta função é chamada quando o usuário envia uma mensagem que não é um comando.
    Verifica se é um botão do menu, uma expressão de louvor, tentativa de cadastro, etc.
    """
    texto = update.message.text.strip()
    
    # Mostrar ID do usuário para ajudar na depuração
    user_id = update.effective_user.id
    print(f"Mensagem recebida do usuário ID: {user_id}, Username: @{update.effective_user.username}")
    
    # Verificar se é um clique em botão do menu
    if texto == "📝 CADASTRAR RESPONSÁVEL 📝" or texto == "🖋️ Cadastrar Responsável":
        # Inicia o fluxo de cadastro como se o usuário tivesse usado o comando /cadastrar
        return await iniciar_cadastro_etapas(update, context)
    
    elif texto == "ℹ️ Ajuda":
        # Executa o comando de ajuda
        from handlers.commands import mostrar_ajuda
        return await mostrar_ajuda(update, context)
    
    elif texto == "🆔 Meu ID":
        # Executa o comando para mostrar ID
        from handlers.commands import mostrar_id
        return await mostrar_id(update, context)
    
    # Verificar se é uma expressão de louvor (versão em minúsculas para comparação)
    texto_lower = texto.lower()
    for padrao in EXPRESSOES_LOUVOR:
        if re.search(padrao, texto_lower):
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
            "Por favor, clique no botão *📝 CADASTRAR RESPONSÁVEL 📝* ou digite */cadastrar* para iniciar o processo passo a passo.\n\n"
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
