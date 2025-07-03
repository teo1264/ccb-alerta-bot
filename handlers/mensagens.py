#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Handlers para processamento de mensagens de texto do CCB Alerta Bot
VERSÃO PERSONALIZADA: Inicia cadastro automaticamente com saudação acolhedora
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
    "*A Santa Paz de Deus!* 🙏\n\nGlória a Deus!",
    "*A Paz de Deus!* 🙌\n\nAmém, irmão(ã)! Deus é bom o tempo todo!",
    "*A Santa Paz!* ✨\n\nQue o Senhor te abençoe.",
    "*A Paz de Deus!* 🙏\n\nAleluia! Louvado seja o Senhor!",
    "*A Santa Paz de Deus!* ✨\n\nDeus seja louvado.",
    "*A Paz!* 🙌\n\nGlória a Deus nas alturas!",
    "*A Santa Paz!* ✨\n\nO Senhor te guarde.",
    "*A Paz de Deus!* 🙏\n\nDeus é fiel! Que Ele te abençoe sempre.",
    "*A Santa Paz!* 🙌\n\nAmém! Que a graça do Senhor esteja contigo.",
    "*A Paz de Deus!* 🙏"
]

async def processar_mensagem(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    VERSÃO PERSONALIZADA: Processa mensagens e inicia cadastro automaticamente
    com saudação acolhedora especialmente pensada para irmãos idosos
    """
    texto = update.message.text.strip()
    
    # Log para depuração
    user_id = update.effective_user.id
    username = update.effective_user.username or "sem_username"
    
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
            await update.message.reply_text(resposta, parse_mode='Markdown')
            return
    
    # NOVO: Para qualquer outra mensagem, iniciar cadastro com saudação personalizada
    # Verificar se o usuário já aceitou a LGPD
    usuario_aceitou_lgpd = context.user_data.get('aceitou_lgpd', False)
    
    if not usuario_aceitou_lgpd:
        # Saudação especial + termos LGPD (texto grande e claro para idosos)
        await update.message.reply_text(
            "*A SANTA PAZ DE DEUS, IRMÃO(Ã)!*\n\n"
            "😊 *Que alegria ter você aqui!*\n\n"
            "📱 *Este é o sistema de alertas automáticos da CCB Região de Mauá.*\n\n"
            "📋 *Para seu cadastro, vamos precisar apenas de:*\n"
            "• *Seu nome completo*\n"
            "• *Sua função na Casa de Oração*\n\n"
            "🔒 *Seus dados ficam protegidos e são usados apenas para enviar alertas importantes.*\n\n"
            "🤝 *Clique no botão abaixo para concordar e iniciar:*",
            reply_markup=update.message.reply_markup,
            parse_mode='Markdown'
        )
        
        # Depois enviar botão de aceite
        from telegram import InlineKeyboardButton, InlineKeyboardMarkup
        keyboard = [
            [InlineKeyboardButton("✅ CONCORDO E QUERO ME CADASTRAR", callback_data="aceitar_lgpd_cadastro_auto")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "👆 *Clique no botão acima para continuar*",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        return
    
    # Se já aceitou LGPD, iniciar cadastro direto com saudação calorosa
    await update.message.reply_text(
        "*A SANTA PAZ DE DEUS!*\n\n"
        "😊 *Que bom ter você aqui, irmão(ã)!*\n\n"
        "📝 *Vamos iniciar seu cadastro no sistema de alertas automáticos.*\n\n"
        "🏠 *Você receberá notificações sobre:*\n"
        "• 💧 *Consumo de água*\n"
        "• ⚡ *Consumo de energia*\n"
        "• ☀️ *Relatórios fotovoltaicos*\n\n"
        "👇 *Para começar, escolha sua Casa de Oração:*",
        parse_mode='Markdown'
    )
    
    # Iniciar o cadastro diretamente
    return await iniciar_cadastro_etapas(update, context)

def registrar_handlers_mensagens(application):
    """Registra handlers para mensagens de texto"""
    # Handler para mensagens de texto que não são comandos
    application.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND, 
        processar_mensagem
    ))
    
    # NOVO: Handler para o callback de aceite LGPD automático
    from telegram.ext import CallbackQueryHandler
    
    async def processar_aceite_lgpd_auto(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Processa o aceite dos termos de LGPD para cadastro automático"""
        query = update.callback_query
        await query.answer()
        
        if query.data == "aceitar_lgpd_cadastro_auto":
            # Marcar que o usuário aceitou os termos
            context.user_data['aceitou_lgpd'] = True
            
            # Editar mensagem para confirmação
            await query.edit_message_text(
                "*A SANTA PAZ DE DEUS!*\n\n"
                "✅ *Termos aceitos com sucesso!*\n\n"
                "📝 *Agora vamos ao seu cadastro...*",
                parse_mode='Markdown'
            )
            
            # Enviar nova mensagem iniciando o cadastro diretamente
            await query.message.reply_text(
                "*📝 INICIANDO SEU CADASTRO*\n\n"
                "👇 *Escolha sua Casa de Oração:*",
                parse_mode='Markdown'
            )
            
            # Preparar dados para o cadastro
            if 'cadastro_temp' not in context.user_data:
                context.user_data['cadastro_temp'] = {'pagina_igreja': 0}
            
            # Simular envio do menu de igrejas via função direta
            from handlers.cadastro import mostrar_menu_igrejas
            
            # Criar um update "fake" simples que funciona
            fake_update = type('FakeUpdate', (), {})()
            fake_update.message = query.message
            fake_update.effective_user = query.from_user
            
            # Chamar a função de mostrar menu
            try:
                await mostrar_menu_igrejas(fake_update, context)
            except Exception as e:
                # Se der erro, pelo menos dá a instrução para continuar
                await query.message.reply_text(
                    "*Digite /cadastrar para continuar*",
                    parse_mode='Markdown'
                )
    
    # Registrar o callback handler
    application.add_handler(CallbackQueryHandler(
        processar_aceite_lgpd_auto, 
        pattern='^aceitar_lgpd_cadastro_auto$'
    ))
