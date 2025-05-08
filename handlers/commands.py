#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Handlers para funções administrativas do CCB Alerta Bot
"""

import os
import pandas as pd
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, CallbackQueryHandler, ContextTypes

from config import EXCEL_FILE, ADMIN_IDS
from utils import verificar_admin, adicionar_admin, fazer_backup_planilha

async def exportar_planilha(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Envia a planilha de cadastros como um arquivo (apenas para administradores)"""
    # Verificar se o usuário é administrador
    if not verificar_admin(update.effective_user.id):
        await update.message.reply_text(
            "🕊️ *A Santa Paz de Deus!*\n\n"
            "⚠️ *Acesso Negado*\n\n"
            "Você não tem permissão para acessar esta função.\n\n"
            "_Deus te abençoe!_ 🙏",
            parse_mode='Markdown'
        )
        return
    
    try:
        if not os.path.exists(EXCEL_FILE):
            await update.message.reply_text(
                "🕊️ *A Santa Paz de Deus!*\n\n"
                "❌ Nenhum arquivo de cadastro encontrado.\n\n"
                "_Deus te abençoe!_ 🙏",
                parse_mode='Markdown'
            )
            return
            
        # Enviar o arquivo
        await update.message.reply_document(
            document=open(EXCEL_FILE, 'rb'),
            filename=EXCEL_FILE,
            caption="🕊️ *A Santa Paz de Deus!*\n\nAqui está o arquivo com todos os cadastros de responsáveis.\n\n_Deus te abençoe!_ 🙏",
            parse_mode='Markdown'
        )
        
        print(f"Planilha enviada para o administrador: {update.effective_user.id} - {update.effective_user.username}")
        
    except Exception as e:
        await update.message.reply_text(
            "🕊️ *A Santa Paz de Deus!*\n\n"
            f"❌ Erro ao enviar planilha: {str(e)}\n\n"
            "_Deus te abençoe!_ 🙏",
            parse_mode='Markdown'
        )

async def listar_cadastros(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Lista todos os cadastros (apenas para administradores)"""
    # Verificar se o usuário é administrador
    if not verificar_admin(update.effective_user.id):
        await update.message.reply_text(
            "🕊️ *A Santa Paz de Deus!*\n\n"
            "⚠️ *Acesso Negado*\n\n"
            "Você não tem permissão para acessar esta função.\n\n"
            "_Deus te abençoe!_ 🙏",
            parse_mode='Markdown'
        )
        return
    
    try:
        if not os.path.exists(EXCEL_FILE):
            await update.message.reply_text(
                "🕊️ *A Santa Paz de Deus!*\n\n"
                "❌ Nenhum cadastro encontrado.\n\n"
                "_Deus te abençoe!_ 🙏",
                parse_mode='Markdown'
            )
            return
            
        df = pd.read_excel(EXCEL_FILE)
        
        if df.empty:
            await update.message.reply_text(
                "🕊️ *A Santa Paz de Deus!*\n\n"
                "❌ Nenhum cadastro encontrado.\n\n"
                "_Deus te abençoe!_ 🙏",
                parse_mode='Markdown'
            )
            return
        
        # Formatar mensagem com os cadastros
        mensagem = "🕊️ *A Santa Paz de Deus!*\n\n"
        mensagem += "📋 *Lista de Cadastros:*\n\n"
        
        for i, row in df.iterrows():
            mensagem += f"📍 *{row['Codigo_Casa']}*\n"
            mensagem += f"👤 Nome: {row['Nome']}\n"
            mensagem += f"🔧 Função: {row['Funcao']}\n"
            mensagem += f"📅 Data: {row['Data_Cadastro']}\n\n"
        
        # Enviar mensagem (possivelmente dividida se for muito grande)
        if len(mensagem) > 4096:
            partes = [mensagem[i:i+4096] for i in range(0, len(mensagem), 4096)]
            for parte in partes:
                await update.message.reply_text(parte, parse_mode='Markdown')
        else:
            await update.message.reply_text(mensagem, parse_mode='Markdown')
            
    except Exception as e:
        await update.message.reply_text(
            "🕊️ *A Santa Paz de Deus!*\n\n"
            f"❌ Erro ao listar cadastros: {str(e)}\n\n"
            "_Deus te abençoe!_ 🙏",
            parse_mode='Markdown'
        )

async def limpar_cadastros(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Remove todos os cadastros (apenas para administradores)"""
    # Verificar se o usuário é administrador
    if not verificar_admin(update.effective_user.id):
        await update.message.reply_text(
            "🕊️ *A Santa Paz de Deus!*\n\n"
            "⚠️ *Acesso Negado*\n\n"
            "Você não tem permissão para acessar esta função.\n\n"
            "_Deus te abençoe!_ 🙏",
            parse_mode='Markdown'
        )
        return
    
    # Confirmar ação com botões
    keyboard = [
        [
            InlineKeyboardButton("⚠️ Sim, limpar tudo", callback_data="confirmar_limpar"),
            InlineKeyboardButton("❌ Cancelar", callback_data="cancelar_limpar")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "🕊️ *A Santa Paz de Deus!*\n\n"
        "⚠️ *ATENÇÃO!*\n\n"
        "Você está prestes a *APAGAR TODOS OS CADASTROS*.\n"
        "Esta ação NÃO pode ser desfeita!\n\n"
        "Tem certeza que deseja continuar?",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def processar_callback_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Processa callbacks dos botões inline para comandos administrativos"""
    query = update.callback_query
    await query.answer()
    
    # Verificar se o usuário é administrador
    if not verificar_admin(update.effective_user.id):
        await query.edit_message_text(
            "🕊️ *A Santa Paz de Deus!*\n\n"
            "⚠️ *Acesso Negado*\n\n"
            "Você não tem permissão para acessar esta função.\n\n"
            "_Deus te abençoe!_ 🙏",
            parse_mode='Markdown'
        )
        return
    
    if query.data == "confirmar_limpar":
        try:
            if os.path.exists(EXCEL_FILE):
                # Fazer backup antes de limpar
                backup_file = fazer_backup_planilha()
                
                # Criar planilha vazia
                df = pd.DataFrame(columns=[
                    'Codigo_Casa', 'Nome', 'Funcao', 
                    'User_ID', 'Username', 'Data_Cadastro',
                    'Ultima_Atualizacao'
                ])
                df.to_excel(EXCEL_FILE, index=False)
                
                await query.edit_message_text(
                    "🕊️ *A Santa Paz de Deus!*\n\n"
                    "✅ *Todos os cadastros foram removidos!*\n\n"
                    f"Um backup foi criado como: `{backup_file}`\n\n"
                    "_Deus te abençoe!_ 🙏",
                    parse_mode='Markdown'
                )
            else:
                await query.edit_message_text(
                    "🕊️ *A Santa Paz de Deus!*\n\n"
                    "ℹ️ Nenhum cadastro encontrado para remover.\n\n"
                    "_Deus te abençoe!_ 🙏",
                    parse_mode='Markdown'
                )
        except Exception as e:
            await query.edit_message_text(
                "🕊️ *A Santa Paz de Deus!*\n\n"
                f"❌ Erro ao limpar cadastros: {str(e)}\n\n"
                "_Deus te abençoe!_ 🙏",
                parse_mode='Markdown'
            )
    
    elif query.data == "cancelar_limpar":
        await query.edit_message_text(
            "🕊️ *A Santa Paz de Deus!*\n\n"
            "✅ *Operação cancelada!*\n\n"
            "Nenhum cadastro foi removido.\n\n"
            "_Deus te abençoe!_ 🙏",
            parse_mode='Markdown'
        )

async def adicionar_admin_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Adiciona um novo administrador (apenas para administradores)"""
    # Verificar se o usuário é administrador
    if not verificar_admin(update.effective_user.id):
        await update.message.reply_text(
            "🕊️ *A Santa Paz de Deus!*\n\n"
            "⚠️ *Acesso Negado*\n\n"
            "Você não tem permissão para acessar esta função.\n\n"
            "_Deus te abençoe!_ 🙏",
            parse_mode='Markdown'
        )
        return
    
    # Verificar se há argumentos
    args = context.args
    if not args or not args[0].isdigit():
        await update.message.reply_text(
            "🕊️ *A Santa Paz de Deus!*\n\n"
            "❌ *Formato inválido!*\n\n"
            "Use: `/admin_add ID_DO_USUARIO`\n"
            "Exemplo: `/admin_add 123456789`\n\n"
            "_Deus te abençoe!_ 🙏",
            parse_mode='Markdown'
        )
        return
    
    # Obter ID do novo administrador
    novo_admin_id = int(args[0])
    
    # Adicionar como administrador
    sucesso, status = adicionar_admin(novo_admin_id)
    
    if not sucesso and status == "já é admin":
        await update.message.reply_text(
            "🕊️ *A Santa Paz de Deus!*\n\n"
            "ℹ️ Este usuário já é um administrador.\n\n"
            "_Deus te abençoe!_ 🙏",
            parse_mode='Markdown'
        )
        return
    
    if sucesso:
        await update.message.reply_text(
            "🕊️ *A Santa Paz de Deus!*\n\n"
            f"✅ Administrador adicionado com sucesso: `{novo_admin_id}`\n\n"
            "_Deus te abençoe!_ 🙏",
            parse_mode='Markdown'
        )
    else:
        await update.message.reply_text(
            "🕊️ *A Santa Paz de Deus!*\n\n"
            f"❌ Erro ao adicionar administrador: {status}\n\n"
            "_Deus te abençoe!_ 🙏",
            parse_mode='Markdown'
        )

def registrar_handlers_admin(application):
    """Registra handlers para funções administrativas"""
    application.add_handler(CommandHandler("exportar", exportar_planilha))
    application.add_handler(CommandHandler("listar", listar_cadastros))
    application.add_handler(CommandHandler("limpar", limpar_cadastros))
    application.add_handler(CommandHandler("admin_add", adicionar_admin_cmd))
    
    # Handler para os callbacks de confirmação nas funções administrativas
    application.add_handler(CallbackQueryHandler(
        processar_callback_admin, 
        pattern='^(confirmar_limpar|cancelar_limpar)$'
    ))