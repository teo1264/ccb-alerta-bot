#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Handlers relacionados à LGPD para o CCB Alerta Bot
Adaptado para usar SQLite para armazenamento persistente
"""

import logging
from datetime import datetime
import pytz
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, ContextTypes, CallbackQueryHandler

from utils.database import (
    obter_cadastros_por_user_id,
    remover_cadastros_por_user_id,
    fazer_backup_banco
)

# Configurar logger
logger = logging.getLogger(__name__)

async def remover_dados(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Remove os dados do usuário do sistema (atendendo à LGPD)"""
    user_id = update.effective_user.id
    logger.info(f"Solicitação de remoção de dados do usuário ID: {user_id}")
    
    try:
        # Obter cadastros do usuário do banco de dados
        cadastros = obter_cadastros_por_user_id(user_id)
        
        if not cadastros or len(cadastros) == 0:
            await update.message.reply_text(
                "*A Santa Paz de Deus!*\n\n"
                "❓ *Não encontramos nenhum cadastro associado ao seu ID em nosso sistema.*\n\n"
                "_Deus te abençoe!_ 🙏",
                parse_mode='Markdown'
            )
            return
            
        # Criar mensagem com os cadastros encontrados para confirmação
        mensagem = (
            "*A Santa Paz de Deus!*\n\n"
            "🔍 *Encontramos os seguintes cadastros associados ao seu ID:*\n\n"
        )
        
        for i, cadastro in enumerate(cadastros, 1):
            mensagem += (
                f"*{i}. {cadastro['codigo_casa']} - {cadastro['nome']}*\n"
                f"   *Função:* {cadastro['funcao']}\n\n"
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

async def processar_callback_remocao(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Processa as respostas dos botões de confirmação de remoção"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    
    if query.data == "cancelar_remocao":
        logger.info(f"Usuário ID {user_id} cancelou a remoção de dados")
        await query.edit_message_text(
            "*A Santa Paz de Deus!*\n\n"
            "✅ *Operação cancelada!*\n\n"
            "*Seus dados foram mantidos em nosso sistema.*\n\n"
            "_Deus te abençoe!_ 🙏",
            parse_mode='Markdown'
        )
        return
        
    elif query.data == "confirmar_remocao":
        logger.info(f"Processando remoção de dados do usuário ID {user_id}")
        try:
            # Obter cadastros do usuário para registro em log
            cadastros = obter_cadastros_por_user_id(user_id)
            total_cadastros = len(cadastros)
            
            # Registrar dados sendo removidos (para log)
            for cadastro in cadastros:
                logger.info(f"Removendo cadastro: {cadastro['codigo_casa']} - {cadastro['nome']} ({cadastro['funcao']})")
            
            # Fazer backup antes da remoção
            backup_file = fazer_backup_banco()
            logger.info(f"Backup criado antes da remoção: {backup_file}")
            
            # Remover os dados do usuário
            removidos = remover_cadastros_por_user_id(user_id)
            
            # Limpar indicador de aceite da LGPD
            if 'aceitou_lgpd' in context.user_data:
                del context.user_data['aceitou_lgpd']
            
            logger.info(f"Remoção concluída: {removidos} cadastros removidos para o usuário ID {user_id}")
            
            await query.edit_message_text(
                "*A Santa Paz de Deus!*\n\n"
                "✅ *Seus dados foram removidos com sucesso!*\n\n"
                f"*Total de {total_cadastros} cadastros removidos.*\n\n"
                "*Você não receberá mais alertas ou comunicados relativos às casas de oração.*\n\n"
                "*Caso deseje se cadastrar novamente no futuro, utilize o comando /cadastrar.*\n\n"
                "_Deus te abençoe!_ 🙏",
                parse_mode='Markdown'
            )
        except Exception as e:
            logger.error(f"Erro durante a remoção de dados: {e}")
            await query.edit_message_text(
                "*A Santa Paz de Deus!*\n\n"
                f"❌ *Ocorreu um erro ao remover seus dados:* {str(e)}\n\n"
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

def registrar_handlers_lgpd(application):
    """Registra os handlers relacionados à LGPD"""
    application.add_handler(CommandHandler("remover", remover_dados))
    application.add_handler(CommandHandler("privacidade", mostrar_politica_privacidade))
    application.add_handler(CallbackQueryHandler(
        processar_callback_remocao, 
        pattern='^(confirmar_remocao|cancelar_remocao)$'
    ))
