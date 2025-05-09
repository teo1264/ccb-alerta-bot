#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Handlers para comandos básicos do CCB Alerta Bot
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import CommandHandler, ContextTypes

# Adicionar esta importação
from utils import verificar_admin

async def mensagem_boas_vindas(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Responde a qualquer mensagem com uma saudação e instruções"""
    # Criar botões de menu principal
    keyboard = [
        # Botão de cadastro maior e destacado
        [KeyboardButton("📝 CADASTRAR RESPONSÁVEL 📝")],
        [KeyboardButton("ℹ️ Ajuda"), KeyboardButton("🆔 Meu ID")]
    ]
    reply_markup = ReplyKeyboardMarkup(
        keyboard,
        resize_keyboard=True,  # Torna os botões menores e mais agradáveis
        one_time_keyboard=False  # Menu permanece disponível
    )
    
    await update.message.reply_text(
        " *A Santa Paz de Deus!*\n\n"
        "📢 *Bem-vindo ao sistema de alertas automáticos da CCB ADM Mauá!*\n\n"
        "⚙️ Este serviço está em *fase de desenvolvimento* e funcionará de forma gratuita, auxiliando na gestão das Casas de Oração.\n\n"
        "🔔 *Você receberá alertas sobre:*\n"
        "• 💧 Consumo excessivo de água (BRK)\n"
        "• ⚡ Consumo fora do padrão de energia (ENEL)\n"
        "• ☀️ Relatórios mensais de compensação (para casas com sistema fotovoltaico)\n\n"
        "📝 *Utilize o botão abaixo para cadastrar ou o menu de ajuda para mais informações.*\n\n"
        "👥 Destinado a:\n"
        "✅ Cooperadores\n"
        "✅ Encarregados de Manutenção\n"
        "✅ Responsáveis pela Escrita\n"
        "✅ E demais irmãos do ministério\n\n"
        "_Deus te abençoe!_ 🙏",
        parse_mode='Markdown',
        reply_markup=reply_markup
    )

async def mostrar_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Mostra o ID do usuário que enviou a mensagem"""
    user_id = update.effective_user.id
    username = update.effective_user.username or "Sem username"
    first_name = update.effective_user.first_name or "Sem nome"
    
    await update.message.reply_text(
        f" *A Paz de Deus!*\n\n"
        f"📋 *Suas informações:*\n\n"
        f"🆔 *Seu ID:* `{user_id}`\n"
        f"👤 *Username:* @{username}\n"
        f"📝 *Nome:* {first_name}\n\n"
        f"_Guarde seu ID para configurar como administrador!_",
        parse_mode='Markdown'
    )

async def mostrar_ajuda(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Exibe a lista de comandos disponíveis"""
    # Verificar se é administrador para mostrar comandos administrativos
    is_admin = verificar_admin(update.effective_user.id)
    
    # Mensagem básica de ajuda para todos os usuários
    mensagem_ajuda = (
        " *A Paz de Deus!*\n\n"
        "📋 *Lista de Comandos Disponíveis:*\n\n"
        "*/start* - Exibe a mensagem de boas-vindas\n"
        "*/cadastrar* - Inicia o processo de cadastro passo a passo\n"
        "*/meu_id* - Mostra seu ID do Telegram\n"
        "*/ajuda* - Exibe esta lista de comandos\n\n"
    )
    
    # Adicionar comandos administrativos se for administrador
    if is_admin:
        mensagem_ajuda += (
            "*Comandos para Administradores:*\n"
            "*/exportar* - Exporta a planilha de cadastros\n"
            "*/listar* - Lista todos os cadastros\n"
            "*/editar_buscar TERMO* - Busca cadastros para edição\n"
            "*/editar CODIGO CAMPO VALOR* - Edita um cadastro existente\n"
            "*/excluir CODIGO NOME* - Exclui um cadastro específico\n"
            "*/limpar* - Remove todos os cadastros (com confirmação)\n"
            "*/admin_add ID* - Adiciona um novo administrador\n\n"
        )
    
    mensagem_ajuda += (
        "*Você também pode usar os botões do menu para acessar as funções principais.*\n\n"
        "_Deus te abençoe!_ 🙏"
    )
    
    await update.message.reply_text(
        mensagem_ajuda,
        parse_mode='Markdown'
    )

def registrar_comandos_basicos(application):
    """Registra handlers para comandos básicos"""
    application.add_handler(CommandHandler("start", mensagem_boas_vindas))
    application.add_handler(CommandHandler("meu_id", mostrar_id))
    application.add_handler(CommandHandler("ajuda", mostrar_ajuda))
    application.add_handler(CommandHandler("help", mostrar_ajuda))
