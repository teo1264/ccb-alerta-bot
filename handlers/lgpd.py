#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Handlers para processar callbacks LGPD e aumentar a fonte
"""

import os
import pandas as pd
import logging
from datetime import datetime
import pytz
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ParseMode
from telegram.ext import CommandHandler, ContextTypes, CallbackQueryHandler

from config import EXCEL_FILE

# Configurar logger
logger = logging.getLogger(__name__)

async def remover_dados(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Remove os dados do usuário do sistema (atendendo à LGPD)"""
    user_id = update.effective_user.id
    logger.info(f"Solicitação de remoção de dados do usuário ID: {user_id}")
    
    # Verificar se o arquivo existe
    if not os.path.exists(EXCEL_FILE):
        await update.message.reply_text(
            "*A Santa Paz de Deus!*\n\n"
            "❓ *Não encontramos nenhum cadastro em nosso sistema.*\n\n"
            "_Deus te abençoe!_ 🙏",
            parse_mode='Markdown'
        )
        return
        
    try:
        # Carregar a planilha
        df = pd.read_excel(EXCEL_FILE)
        
        # Verificar se o usuário tem cadastro
        filtro = df['User_ID'] == user_id
        
        if not filtro.any():
            await update.message.reply_text(
                "*A Santa Paz de Deus!*\n\n"
                "❓ *Não encontramos nenhum cadastro associado ao seu ID em nosso sistema.*\n\n"
                "_Deus te abençoe!_ 🙏",
                parse_mode='Markdown'
            )
            return
            
        # Encontrar todos os cadastros do usuário
        cadastros = df[filtro]
        
        # Criar mensagem com os cadastros encontrados para confirmação
        mensagem = (
            "*A Santa Paz de Deus!*\n\n"
            "🔍 *Encontramos os seguintes cadastros associados ao seu ID:*\n\n"
        )
        
        for i, (_, row) in enumerate(cadastros.iterrows(), 1):
            mensagem += (
                f"*{i}. {row['Codigo_Casa']} - {row['Nome']}*\n"
                f"   *Função:* {row['Funcao']}\n\n"
            )
            
        mensagem += (
            "⚠️ *ATENÇÃO:*\n\n"
            "*A remoção dos seus dados é irreversível e você não* "
            "*receberá mais alertas ou comunicados referentes às casas de oração.*\n\n"
            "*Deseja realmente remover todos os seus dados do sistema?*"
        )
        
        # Botões de confirmação
        keyboard = [
            [
                InlineKeyboardButton("✅ Sim, remover meus dados", callback_data="confirmar_remocao"),
                InlineKeyboardButton("❌ Não, cancelar", callback_data="cancelar_remocao")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            mensagem,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        
    except Exception as e:
        logger.error(f"Erro ao processar solicitação de remoção: {e}")
        await update.message.reply_text(
            "*A Santa Paz de Deus!*\n\n"
            f"❌ *Ocorreu um erro ao processar sua solicitação:* {str(e)}\n\n"
            "*Por favor, tente novamente mais tarde ou entre em contato com o administrador.*\n\n"
            "_Deus te abençoe!_ 🙏",
            parse_mode='Markdown'
        )

async def mostrar_politica_privacidade(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Mostra a política de privacidade completa com fonte maior"""
    await update.message.reply_text(
        "*A Santa Paz de Deus!*\n\n"
        "📋 *Política de Privacidade - CCB Alerta Bot*\n\n"
        "*1. Dados Coletados*\n"
        "*Este serviço coleta os seguintes dados:*\n"
        "• *Nome completo*\n"
        "• *Função na igreja*\n"
        "• *ID do Telegram*\n"
        "• *Nome de usuário do Telegram (se disponível)*\n\n"
        
        "*2. Finalidade do Tratamento*\n"
        "*Os dados são utilizados exclusivamente para:*\n"
        "• *Envio de alertas sobre consumo de água e energia*\n"
        "• *Comunicação administrativa sobre as Casas de Oração*\n"
        "• *Relatórios mensais de compensação para casas com sistema fotovoltaico*\n\n"
        
        "*3. Base Legal*\n"
        "*O tratamento é realizado com base no consentimento do titular (Art. 7º, I da LGPD)* "
        "*e para atender aos interesses legítimos da administração local (Art. 7º, IX da LGPD).*\n\n"
        
        "*4. Compartilhamento*\n"
        "*Os dados não são compartilhados com terceiros. O acesso é restrito aos* "
        "*administradores do sistema para fins operacionais.*\n\n"
        
        "*5. Prazo de Conservação*\n"
        "*Os dados são mantidos enquanto o titular exercer sua função na Casa de Oração* "
        "*ou até que solicite sua remoção.*\n\n"
        
        "*6. Direitos do Titular*\n"
        "*Você tem direito a:*\n"
        "• *Acessar seus dados*\n"
        "• *Solicitar exclusão (via comando /remover)*\n"
        "• *Revogar o consentimento a qualquer momento*\n\n"
        
        "*7. Controlador*\n"
        "*Administração Regional CCB Mauá*\n\n"
        
        "_Esta política foi atualizada em maio/2025 e está em conformidade com a_ "
        "_Lei Geral de Proteção de Dados (Lei nº 13.709/2018)._\n\n"
        
        "*Para mais informações ou para exercer seus direitos, utilize o comando /remover* "
        "*ou entre em contato com um administrador.*\n\n"
        
        "_Deus te abençoe!_ 🙏",
        parse_mode='Markdown'
    )
