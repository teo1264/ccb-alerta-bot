#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Handlers para tratamento de erros do CCB Alerta Bot
"""

import traceback
import html
import json
import logging
from datetime import datetime
from telegram import Update
from telegram.ext import ContextTypes, ApplicationHandlerStop

from config import ADMIN_IDS

# Configurar logger
logger = logging.getLogger(__name__)

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Tratamento de erros global para todas as atualizações
    
    Este handler captura todas as exceções não tratadas nas funções do bot e as
    registra em um arquivo de log, além de notificar os administradores.
    """
    # Obter informações do erro
    tb_list = traceback.format_exception(None, context.error, context.error.__traceback__)
    tb_string = "".join(tb_list)
    
    # Registrar o erro com todas as informações disponíveis
    error_message = (
        f"Exception while handling an update:\n"
        f"update = {html.escape(json.dumps(update.to_dict(), indent=2, ensure_ascii=False))}\n\n"
        f"context.chat_data = {html.escape(str(context.chat_data))}\n\n"
        f"context.user_data = {html.escape(str(context.user_data))}\n\n"
        f"{html.escape(tb_string)}"
    )
    
    # Registrar no log
    logger.error(error_message)
    
    # Salvar em arquivo de log de erros
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    error_file = f"error_{timestamp}.log"
    try:
        with open(error_file, "w", encoding="utf-8") as f:
            f.write(error_message)
    except Exception as e:
        logger.error(f"Failed to write error to file: {e}")
    
    # Enviar mensagem simplificada para os administradores
    error_text = f"❌ *Erro no bot!*\n\n"
    error_text += f"Tipo: `{type(context.error).__name__}`\n"
    error_text += f"Mensagem: `{str(context.error)}`\n\n"
    
    # Adicionar informações de contexto se disponíveis
    update_str = "Sem informações"
    if update and update.effective_message:
        update_str = f"Mensagem de {update.effective_message.from_user.id}"
        if update.effective_message.text:
            update_str += f": {update.effective_message.text[:50]}..."
    
    error_text += f"Contexto: {update_str}\n"
    error_text += f"Hora: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n"
    error_text += f"Log salvo como: `{error_file}`"
    
    # Enviar notificação para todos os administradores
    for admin_id in ADMIN_IDS:
        try:
            await context.bot.send_message(
                chat_id=admin_id, 
                text=error_text,
                parse_mode='Markdown'
            )
        except Exception as e:
            logger.error(f"Failed to notify admin {admin_id}: {e}")
    
    # Re-levantar o erro se for crítico, ou parar o processamento
    if isinstance(context.error, (KeyboardInterrupt, SystemExit)):
        raise context.error
    
    raise ApplicationHandlerStop()

def registrar_error_handler(application):
    """Registra o handler de erros global"""
    application.add_error_handler(error_handler)