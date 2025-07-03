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
            "📋 *INFORMAÇÃO IMPORTANTE:*\n\n"
            "Para seu cadastro, vamos precisar do seu:\n"
            "• *Nome completo*\n"
            "• *Função na Casa de Oração*\n"
            "• *ID do Telegram*\n\n"
            "🔒 *Seus dados são protegidos conforme a Lei de Proteção de Dados (LGPD).*\n\n"
            "❌ *Não compartilhamos com terceiros*\n"
            "✅ *Usado apenas para alertas da nossa região*\n\n"
            "🗑️ *Pode solicitar remoção a qualquer momento com o comando:*\n"
            "*/remover*\n\n"
            "🤝 *Se concorda, clique no botão abaixo para iniciar seu cadastro:*",
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
                "✅ *Obrigado por aceitar os termos!*\n\n"
                "📝 *Iniciando seu cadastro...*",
                parse_mode='Markdown'
            )
            
            # Inicializar dados do cadastro no contexto
            context.user_data['cadastro_temp'] = {'pagina_igreja': 0}
            
            # Enviar menu de igrejas diretamente
            from handlers.cadastro import mostrar_menu_igrejas
            await mostrar_menu_igrejas(query.message, context, is_new_message=True)
            
            # Retornar o estado do conversation handler
            from config import SELECIONAR_IGREJA
            return SELECIONAR_IGREJA
    
    # Registrar o callback handler
    application.add_handler(CallbackQueryHandler(
        processar_aceite_lgpd_auto, 
        pattern='^aceitar_lgpd_cadastro_auto$'
    ))
