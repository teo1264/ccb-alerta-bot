#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Handlers para comandos básicos do CCB Alerta Bot
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import CommandHandler, ContextTypes, CallbackQueryHandler

# Usar a importação direta do módulo database para evitar problemas
from utils.database import verificar_admin

async def mensagem_boas_vindas(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Responde a qualquer mensagem com uma saudação e instruções"""
    # Verificar se o usuário já aceitou os termos da LGPD
    usuario_aceitou_lgpd = context.user_data.get('aceitou_lgpd', False)
    
    if not usuario_aceitou_lgpd:
        # Exibir mensagem de LGPD com botão de aceitação
        keyboard = [
            [InlineKeyboardButton("✅ Aceito os termos", callback_data="aceitar_lgpd")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "*A Paz de Deus, irmão!*\n\n"
            "Antes de prosseguir, informamos que este canal coleta *seu nome*, *função* e *ID do Telegram*.\n\n"
            "*Esses dados são utilizados exclusivamente para comunicação administrativa e operacional* "
            "das Casas de Oração da nossa região.\n\n"
            "Eles *não serão compartilhados com terceiros* e são tratados conforme a "
            "*Lei Geral de Proteção de Dados (LGPD – Lei nº 13.709/2018)*.\n\n"
            "Ao continuar, você autoriza o uso dessas informações para envio de mensagens "
            "relacionadas à sua função ou responsabilidade.\n\n"
            "Você pode solicitar a exclusão dos seus dados a qualquer momento usando o comando:\n"
            "*\\/remover*\n\n"
            "Se estiver de acordo, clique no botão abaixo para continuar.",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        return
    
    # Caso já tenha aceitado os termos, mostrar a mensagem normal
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
        "*A Santa Paz de Deus!*\n\n"
        "📢 *Bem-vindo ao sistema de alertas automáticos da CCB ADM Mauá!*\n\n"
        "⚙️ Este serviço está em *fase de desenvolvimento* e funcionará de forma gratuita, auxiliando na gestão das Casas de Oração.\n\n"
        "🔔 *Você receberá alertas sobre:*\n"
        "• 💧 *Consumo excessivo de água (BRK)*\n"
        "• ⚡ *Consumo fora do padrão de energia (ENEL)*\n"
        "• ☀️ *Relatórios mensais de compensação* (para casas com sistema fotovoltaico)\n\n"
        "📝 *Utilize o botão abaixo para cadastrar ou o menu de ajuda para mais informações.*\n\n"
        "👥 *Destinado a:*\n"
        "✅ *Cooperadores*\n"
        "✅ *Encarregados de Manutenção*\n"
        "✅ *Responsáveis pela Escrita*\n"
        "✅ *E demais irmãos do ministério*\n\n"
        "_Deus te abençoe!_ 🙏",
        parse_mode='Markdown',
        reply_markup=reply_markup
    )

async def processar_aceite_lgpd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Processa o aceite dos termos de LGPD"""
    query = update.callback_query
    await query.answer()
    
    if query.data == "aceitar_lgpd":
        # Marcar que o usuário aceitou os termos
        context.user_data['aceitou_lgpd'] = True
        
        # Editar a mensagem para confirmar o aceite
        await query.edit_message_text(
            "*A Santa Paz de Deus!*\n\n"
            "✅ *Agradecemos por aceitar os termos!*\n\n"
            "*Você agora pode utilizar todas as funcionalidades do bot.*\n"
            "*Use o comando /start para continuar.*\n\n"
            "_Deus te abençoe!_ 🙏",
            parse_mode='Markdown'
        )
        
        # NÃO chamar mensagem_boas_vindas aqui - isso causa o erro
        # Em vez disso, instruímos o usuário a usar /start

async def mostrar_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Mostra o ID do usuário que enviou a mensagem"""
    user_id = update.effective_user.id
    username = update.effective_user.username or "Sem username"
    first_name = update.effective_user.first_name or "Sem nome"
    
    await update.message.reply_text(
        "*A Paz de Deus!*\n\n"
        "📋 *Suas informações:*\n\n"
        "🆔 *Seu ID:* `" + str(user_id) + "`\n"
        "👤 *Username:* @" + username + "\n"
        "📝 *Nome:* " + first_name + "\n\n"
        "*Guarde seu ID para configurar como administrador!*",
        parse_mode='Markdown'
    )

async def mostrar_ajuda(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Exibe a lista de comandos disponíveis"""
    # Verificar se é administrador para mostrar comandos administrativos
    is_admin = verificar_admin(update.effective_user.id)
    
    # Mensagem básica de ajuda para todos os usuários
    mensagem_ajuda = (
        "*A Paz de Deus!*\n\n"
        "📋 *Lista de Comandos Disponíveis:*\n\n"
        "*\\/START* - Exibe a mensagem de boas-vindas\n"
        "*\\/CADASTRAR* - Inicia o processo de cadastro passo a passo\n"
        "*\\/MEU_ID* - Mostra seu ID do Telegram\n"
        "*\\/REMOVER* - Solicita a exclusão dos seus dados (LGPD)\n"
        "*\\/PRIVACIDADE* - Exibe a política de privacidade completa\n"
        "*\\/AJUDA* - Exibe esta lista de comandos\n\n"
    )
    
    # Seção de LGPD
    mensagem_ajuda += (
        "🔒 *Proteção de Dados (LGPD)*\n"
        "*Este bot coleta seu nome, função e ID do Telegram para comunicação* "
        "*administrativa das Casas de Oração. Seus dados são tratados conforme* "
        "*a Lei Geral de Proteção de Dados (Lei nº 13.709/2018).*\n\n"
    )
    
    # Adicionar comandos administrativos se for administrador
    if is_admin:
        mensagem_ajuda += (
            "*Comandos para Administradores:*\n"
            "*\\/exportar* - Exporta a planilha de cadastros\n"
            "*\\/listar* - Lista todos os cadastros\n"
            "*\\/editar_buscar TERMO* - Busca cadastros para edição\n"
            "*\\/editar CODIGO CAMPO VALOR* - Edita um cadastro existente\n"
            "*\\/excluir CODIGO NOME* - Exclui um cadastro específico\n"
            "*\\/excluir_id NUMERO* - Exclui um cadastro pelo número da listagem\n"
            "*\\/limpar* - Remove todos os cadastros (com confirmação)\n"
            "*\\/admin_add ID* - Adiciona um novo administrador\n\n"
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
    
    # Handler para o callback de aceite dos termos de LGPD
    application.add_handler(CallbackQueryHandler(
        processar_aceite_lgpd, 
        pattern='^aceitar_lgpd$'
    ))
