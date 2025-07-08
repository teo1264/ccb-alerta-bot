#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Handlers para processamento de mensagens de texto do CCB Alerta Bot
VERSÃO CORRIGIDA: Sistema de respostas automáticas + auto-cadastro
COMPATÍVEL COM: Sistema de callbacks diretos
"""

import re
import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import MessageHandler, filters, ContextTypes

from handlers.cadastro import iniciar_cadastro_etapas

# Expressões de louvor e suas respostas
EXPRESSOES_LOUVOR = [
    # Amém e variações
    r'\bamem\b',
    r'\bamén\b',
    r'\bamen\b',
    r'\bamém\b',
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
    "A Santa Paz de Deus! 🙏\n\nGlória a Deus!",
    "A Paz de Deus! 🙌\n\nAmém, irmão(ã)! Deus é bom o tempo todo!",
    "A Santa Paz! ✨\n\nQue o Senhor te abençoe.",
    "A Paz de Deus! 🙏\n\nAleluia! Louvado seja o Senhor!",
    "A Santa Paz de Deus! ✨\n\nDeus seja louvado.",
    "A Paz! 🙌\n\nGlória a Deus nas alturas!",
    "A Santa Paz! ✨\n\nO Senhor te guarde.",
    "A Paz de Deus! 🙏\n\nDeus é fiel! Que Ele te abençoe sempre.",
    "A Santa Paz! 🙌\n\nAmém! Que a graça do Senhor esteja contigo.",
    "A Paz de Deus! 🙏"
]

# Saudações gerais
SAUDACOES_GERAIS = [
    r'\bola\b',
    r'\boi\b',
    r'\bboa tarde\b',
    r'\bboa noite\b',
    r'\bbom dia\b',
    r'\btudo bem\b',
    r'\btudo bom\b',
    r'\bcomo vai\b'
]

RESPOSTAS_SAUDACOES = [
    "Olá! A Santa Paz de Deus! 😊",
    "A Paz de Deus! Seja bem-vindo(a)! 🙏",
    "A Santa Paz! Como vai, irmão(ã)? ✨",
    "A Paz! Que alegria ter você aqui! 🙌",
    "A Santa Paz de Deus! Tudo bem? 😊"
]

async def processar_mensagem(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Processa mensagens e inicia cadastro automaticamente
    VERSÃO CORRIGIDA - compatível com sistema callbacks diretos
    """
    # Verificar se já está em processo de cadastro ativo
    if 'cadastro' in context.user_data:
        # Se está em cadastro, não processar aqui - deixar o cadastro.py lidar
        return
    
    texto = update.message.text.strip()
    
    # Log para debug
    user_id = update.effective_user.id
    username = update.effective_user.username or "sem_username"
    
    # Verificar se é um clique em botão do menu
    if texto == "📝 CADASTRAR RESPONSÁVEL 📝" or texto == "🖋️ Cadastrar Responsável":
        return await iniciar_cadastro_etapas(update, context)
    
    elif texto == "ℹ️ Ajuda":
        from handlers.commands import mostrar_ajuda
        return await mostrar_ajuda(update, context)
    
    elif texto == "🆔 Meu ID":
        from handlers.commands import mostrar_id
        return await mostrar_id(update, context)
    
    # Verificar se é uma expressão de louvor
    texto_lower = texto.lower()
    
    # Respostas para expressões de louvor
    for padrao in EXPRESSOES_LOUVOR:
        if re.search(padrao, texto_lower):
            resposta = random.choice(RESPOSTAS_LOUVOR)
            await update.message.reply_text(resposta)
            
            # Após resposta de louvor, sugerir cadastro
            await update.message.reply_text(
                "📝 Para se cadastrar no sistema de alertas automáticos, use /cadastrar"
            )
            return
    
    # Respostas para saudações gerais
    for padrao in SAUDACOES_GERAIS:
        if re.search(padrao, texto_lower):
            resposta = random.choice(RESPOSTAS_SAUDACOES)
            await update.message.reply_text(resposta)
            
            # Após saudação, iniciar cadastro automaticamente
            await update.message.reply_text(
                "😊 Que bom ter você aqui!\n\n"
                "📱 Este é o sistema de alertas automáticos da CCB Região de Mauá.\n\n"
                "Vamos iniciar seu cadastro?"
            )
            
            # Iniciar cadastro automaticamente
            return await iniciar_cadastro_etapas(update, context)
    
    # Para qualquer outra mensagem, iniciar cadastro automaticamente
    await update.message.reply_text(
        "A Santa Paz de Deus! 🙏\n\n"
        "😊 Que alegria ter você aqui!\n\n"
        "📱 Este é o sistema de alertas automáticos da CCB Região de Mauá.\n\n"
        "Vamos iniciar seu cadastro automaticamente..."
    )
    
    # Pequena pausa para o usuário ler
    import asyncio
    await asyncio.sleep(1)
    
    # Iniciar cadastro
    return await iniciar_cadastro_etapas(update, context)

def registrar_handlers_mensagens(application):
    """
    Registra handlers para mensagens de texto
    VERSÃO CORRIGIDA - sem duplicatas de handlers
    """
    # Handler para mensagens de texto que não são comandos
    # IMPORTANTE: Colocar com group maior para ter prioridade MENOR que cadastro
    application.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND, 
        processar_mensagem
    ), group=5)  # Group maior = prioridade menor
    
    # REMOVIDO: Handler LGPD duplicado (já existe em cadastro.py)
    # Sem conflitos de handlers!
