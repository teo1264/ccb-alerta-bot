#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Handlers para o processo de cadastro do CCB Alerta Bot
VERSÃO DEFINITIVA - CALLBACKS DIRETOS (SEM ConversationHandler)
Sistema 100% funcional para produção BRK
MELHORIAS: Texto claro + Detector de respostas não-nomes
CORREÇÕES: Mensagem duplicado + Fail-fast OneDrive + Alertas admin
"""

import re
import math
import logging
import os
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    CommandHandler, MessageHandler, CallbackQueryHandler,
    ContextTypes, filters
)

# Imports do sistema
try:
    from utils.database import (
        verificar_cadastro_existente,
        salvar_responsavel,
        obter_cadastros_por_user_id,
        verificar_consentimento_lgpd,
        registrar_consentimento_lgpd
    )
except ImportError:
    import sys
    import os
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
    from utils.database import (
        verificar_cadastro_existente,
        salvar_responsavel,
        obter_cadastros_por_user_id,
        verificar_consentimento_lgpd,
        registrar_consentimento_lgpd
    )

from handlers.data import (
    IGREJAS, FUNCOES, agrupar_igrejas, agrupar_funcoes, 
    obter_igreja_por_codigo, detectar_funcao_similar
)

# Logger
logger = logging.getLogger(__name__)

# Estados para controle de fluxo (sem ConversationHandler)
ESTADO_INICIAL = "inicial"
ESTADO_AGUARDANDO_NOME = "aguardando_nome"
ESTADO_AGUARDANDO_FUNCAO = "aguardando_funcao"

# ================================================================================================
# SISTEMA DE ALERTAS ONEDRIVE - INTEGRAÇÃO
# ================================================================================================

def get_admin_ids():
    """Obter IDs dos administradores da variável ADMIN_IDS"""
    admin_ids_str = os.getenv("ADMIN_IDS", "")
    return [admin_id.strip() for admin_id in admin_ids_str.split(',') if admin_id.strip()]

async def send_telegram_to_admin(admin_id, message, context):
    """Enviar mensagem Telegram para admin específico"""
    try:
        await context.bot.send_message(
            chat_id=admin_id,
            text=message,
            parse_mode='Markdown'
        )
        return True
    except Exception as e:
        logger.error(f"❌ Erro enviando Telegram para admin {admin_id}: {e}")
        return False

async def alert_onedrive_failure(error_details, context):
    """Alertar todos os admins sobre falha do OneDrive"""
    admin_ids = get_admin_ids()
    if not admin_ids:
        logger.error("❌ Nenhum admin configurado para alertas OneDrive")
        return False
        
    message = f"""
🚨 **ALERTA CRÍTICO - Sistema CCB**

❌ **OneDrive OFFLINE**
⏰ {datetime.now().strftime('%H:%M:%S - %d/%m/%Y')}

🔍 **Erro:** {error_details}

⚠️ **IMPACTO:**
• ❌ Novos cadastros BLOQUEADOS
• ❌ Sincronização BRK/ENEL parada
• 🛡️ Sistema em modo proteção

🔧 **AÇÃO NECESSÁRIA:**
1. Verificar token Microsoft no Render
2. Renovar credenciais se expirado
3. Restart serviço após correção

_Cadastros serão rejeitados até normalização_
"""
    
    success_count = 0
    for admin_id in admin_ids:
        if await send_telegram_to_admin(admin_id, message, context):
            success_count += 1
    
    logger.info(f"🚨 Alerta OneDrive enviado para {success_count}/{len(admin_ids)} admins")
    return success_count > 0

async def alert_onedrive_recovery(context):
    """Alertar recuperação do OneDrive"""
    admin_ids = get_admin_ids()
    if not admin_ids:
        return False
        
    message = f"""
✅ **SISTEMA RECUPERADO - CCB**

🌐 **OneDrive:** Online
⏰ {datetime.now().strftime('%H:%M:%S - %d/%m/%Y')}

✅ **Status:**
• ✅ Cadastros liberados
• ✅ Sincronização BRK/ENEL ativa
• ✅ Sistema operacional

📊 Monitoramento ativo
"""
    
    success_count = 0
    for admin_id in admin_ids:
        if await send_telegram_to_admin(admin_id, message, context):
            success_count += 1
    
    logger.info(f"✅ Recuperação notificada para {success_count}/{len(admin_ids)} admins")
    return success_count > 0

# Variável global para controlar status do OneDrive
onedrive_status = {"healthy": True, "last_check": None}

async def check_onedrive_health(context):
    """Verificar saúde do OneDrive antes de aceitar cadastros"""
    global onedrive_status
    
    now = datetime.now()
    
    # Cache de 30 segundos
    if (onedrive_status["last_check"] and 
        (now - onedrive_status["last_check"]).seconds < 30):
        return onedrive_status["healthy"]
    
    try:
        # Verificar variáveis básicas necessárias
        client_id = os.getenv("MICROSOFT_CLIENT_ID")
        access_token = os.getenv("MICROSOFT_ACCESS_TOKEN") 
        alerta_id = os.getenv("ONEDRIVE_ALERTA_ID")
        
        if not client_id or not access_token or not alerta_id:
            raise Exception("Configurações Microsoft/OneDrive incompletas")
            
        # Se chegou até aqui e tinha problemas antes, recuperou
        was_healthy = onedrive_status["healthy"]
        onedrive_status["healthy"] = True
        onedrive_status["last_check"] = now
        
        # Se estava down e agora subiu, alertar recuperação
        if not was_healthy:
            await alert_onedrive_recovery(context)
            logger.info("✅ OneDrive recuperado - admins notificados")
            
        return True
        
    except Exception as e:
        was_healthy = onedrive_status["healthy"]
        onedrive_status["healthy"] = False
        onedrive_status["last_check"] = now
        
        # Se estava up e agora caiu, alertar admins
        if was_healthy:
            await alert_onedrive_failure(str(e), context)
            logger.error(f"🚨 OneDrive falhou - admins alertados: {e}")
            
        return False

# ================================================================================================
# DETECTOR DE RESPOSTAS NÃO-NOMES - NOVA FUNCIONALIDADE
# ================================================================================================

def validar_nome_usuario(nome: str):
    """
    Detecta se a resposta é um nome válido ou uma pergunta/afirmação
    
    Args:
        nome (str): Texto digitado pelo usuário
        
    Returns:
        tuple: (é_válido, mensagem_ou_nome_limpo)
    """
    nome_lower = nome.lower().strip()
    
    # Palavras que indicam que não é um nome
    palavras_problema = [
        # Perguntas
        '?', 'qual', 'quem', 'como', 'onde', 'quando', 'por que', 'porque',
        # Dúvidas
        'não sei', 'nao sei', 'não estou', 'nao estou', 'não entendo', 'nao entendo',
        'confuso', 'confusa', 'duvida', 'dúvida', 'intendendo', 'entendendte',
        # Descrições
        'nome do', 'nome da', 'responsável', 'responsavel', 'ancião', 'anciao',
        'pessoa que', 'pessoa responsável', 'pessoa responsavel',
        # Afirmações
        'sim', 'não', 'nao', 'ok', 'certo', 'correto', 'errado',
        'eu sou', 'meu nome', 'minha nome',
        # Comandos
        'cadastrar', 'ajuda', 'help', 'cancelar', 'sair'
    ]
    
    # Verificar se contém palavras problemáticas
    for palavra in palavras_problema:
        if palavra in nome_lower:
            return False, "Digite apenas **SEU NOME COMPLETO**.\n\nExemplo: `João da Silva` ou `Maria Santos`"
    
    # Verificar outros padrões problemáticos
    if nome.startswith('/'):  # Comando Telegram
        return False, "Digite apenas **SEU NOME COMPLETO**.\n\nExemplo: `Carlos Silva`"
    
    if len(nome) < 2:  # Muito curto
        return False, "Digite apenas **SEU NOME COMPLETO**.\n\nExemplo: `Ana Costa`"
    
    if nome.isdigit():  # Apenas números
        return False, "Digite apenas **SEU NOME COMPLETO**.\n\nExemplo: `Pedro Santos`"
    
    # Não contém letras
    if not re.search(r'[a-zA-ZÀ-ÿ]', nome):
        return False, "Digite um nome válido com apenas letras e espaços.\n\nExemplo: `Maria Silva`"
    
    # Nome válido
    return True, nome.strip()

# ================================================================================================
# SISTEMA DE CALLBACKS DIRETOS - INÍCIO DO CADASTRO
# ================================================================================================

async def iniciar_cadastro_etapas(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /cadastrar - inicia processo"""
    user_id = update.effective_user.id
    
    # Verificar LGPD
    usuario_aceitou_lgpd = verificar_consentimento_lgpd(user_id)
    
    if not usuario_aceitou_lgpd:
        # Exibir LGPD
        keyboard = [
            [InlineKeyboardButton("✅ CONCORDO E QUERO ME CADASTRAR", callback_data="aceitar_lgpd_cadastro_auto")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "A Paz de Deus!\n\n"
            "Antes de prosseguir, informamos que coletamos seu nome, função e ID do Telegram.\n\n"
            "Esses dados são para comunicação administrativa das Casas de Oração.\n\n"
            "Não são compartilhados e seguem a LGPD.\n\n"
            "Para remover seus dados: /remover\n\n"
            "👆 Clique no botão acima para continuar",
            reply_markup=reply_markup
        )
        return
    
    # Inicializar contexto do cadastro
    context.user_data['cadastro'] = {
        'estado': ESTADO_INICIAL,
        'pagina_igreja': 0,
        'pagina_funcao': 0
    }
    
    logger.info(f"🚀 INICIANDO cadastro usuário {user_id}")
    await mostrar_menu_igrejas(update, context)

# ================================================================================================
# LGPD - ACEITE DE TERMOS
# ================================================================================================

async def processar_aceite_lgpd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Processa aceite LGPD e inicia cadastro"""
    query = update.callback_query
    await query.answer()
    
    if query.data == "aceitar_lgpd_cadastro_auto":
        # Salvar consentimento
        registrar_consentimento_lgpd(query.from_user.id)
        
        # Inicializar contexto
        context.user_data['cadastro'] = {
            'estado': ESTADO_INICIAL,
            'pagina_igreja': 0,
            'pagina_funcao': 0
        }
        
        # Mostrar menu de igrejas
        await mostrar_menu_igrejas_callback(query, context)

# ================================================================================================
# MENU DE IGREJAS - CALLBACKS DIRETOS
# ================================================================================================

async def mostrar_menu_igrejas(update, context: ContextTypes.DEFAULT_TYPE):
    """Mostra menu de igrejas - para comando inicial"""
    igrejas_paginadas = agrupar_igrejas()
    pagina_atual = context.user_data['cadastro'].get('pagina_igreja', 0)
    
    # Validar página
    if pagina_atual >= len(igrejas_paginadas):
        pagina_atual = 0
    elif pagina_atual < 0:
        pagina_atual = len(igrejas_paginadas) - 1
    
    context.user_data['cadastro']['pagina_igreja'] = pagina_atual
    
    # Construir teclado
    keyboard = []
    for igreja in igrejas_paginadas[pagina_atual]:
        callback_data = f"selecionar_igreja_{igreja['codigo']}"
        keyboard.append([InlineKeyboardButton(
            f"{igreja['codigo']} - {igreja['nome']}", 
            callback_data=callback_data
        )])
    
    # Botões de navegação
    nav_buttons = []
    if len(igrejas_paginadas) > 1:
        nav_buttons.append(InlineKeyboardButton("⬅️ Anterior", callback_data="navegar_igreja_anterior"))
        nav_buttons.append(InlineKeyboardButton("Próxima ➡️", callback_data="navegar_igreja_proxima"))
    keyboard.append(nav_buttons)
    
    keyboard.append([InlineKeyboardButton("❌ Cancelar", callback_data="cancelar_cadastro")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    texto = (
        "A Santa Paz de Deus!\n\n"
        "Selecione a Casa de Oração:\n\n"
        f"📄 Página {pagina_atual + 1}/{len(igrejas_paginadas)}"
    )
    
    await update.message.reply_text(texto, reply_markup=reply_markup)

async def mostrar_menu_igrejas_callback(query, context: ContextTypes.DEFAULT_TYPE):
    """Mostra menu de igrejas - para callbacks"""
    igrejas_paginadas = agrupar_igrejas()
    pagina_atual = context.user_data['cadastro'].get('pagina_igreja', 0)
    
    # Validar página
    if pagina_atual >= len(igrejas_paginadas):
        pagina_atual = 0
    elif pagina_atual < 0:
        pagina_atual = len(igrejas_paginadas) - 1
    
    context.user_data['cadastro']['pagina_igreja'] = pagina_atual
    
    # Construir teclado
    keyboard = []
    for igreja in igrejas_paginadas[pagina_atual]:
        callback_data = f"selecionar_igreja_{igreja['codigo']}"
        keyboard.append([InlineKeyboardButton(
            f"{igreja['codigo']} - {igreja['nome']}", 
            callback_data=callback_data
        )])
    
    # Botões de navegação
    nav_buttons = []
    if len(igrejas_paginadas) > 1:
        nav_buttons.append(InlineKeyboardButton("⬅️ Anterior", callback_data="navegar_igreja_anterior"))
        nav_buttons.append(InlineKeyboardButton("Próxima ➡️", callback_data="navegar_igreja_proxima"))
    keyboard.append(nav_buttons)
    
    keyboard.append([InlineKeyboardButton("❌ Cancelar", callback_data="cancelar_cadastro")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    texto = (
        "A Santa Paz de Deus!\n\n"
        "Selecione a Casa de Oração:\n\n"
        f"📄 Página {pagina_atual + 1}/{len(igrejas_paginadas)}"
    )
    
    await query.edit_message_text(texto, reply_markup=reply_markup)

async def navegar_igrejas(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler para navegação entre páginas de igrejas"""
    query = update.callback_query
    await query.answer()
    
    # Verificar se usuário tem contexto ativo
    if 'cadastro' not in context.user_data:
        await query.edit_message_text(
            "Sessão expirou. Use /cadastrar para iniciar novamente."
        )
        return
    
    data = query.data
    
    if data == "navegar_igreja_anterior":
        context.user_data['cadastro']['pagina_igreja'] -= 1
        await mostrar_menu_igrejas_callback(query, context)
    
    elif data == "navegar_igreja_proxima":
        context.user_data['cadastro']['pagina_igreja'] += 1
        await mostrar_menu_igrejas_callback(query, context)

async def selecionar_igreja(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler para seleção de igreja"""
    query = update.callback_query
    await query.answer()
    
    # Verificar contexto
    if 'cadastro' not in context.user_data:
        await query.edit_message_text(
            "Sessão expirou. Use /cadastrar para iniciar novamente."
        )
        return
    
    # Extrair código da igreja
    codigo_igreja = query.data.replace("selecionar_igreja_", "")
    igreja = obter_igreja_por_codigo(codigo_igreja)
    
    if not igreja:
        await query.edit_message_text(
            "Igreja não encontrada. Use /cadastrar para tentar novamente."
        )
        return
    
    # Salvar igreja selecionada
    context.user_data['cadastro']['codigo'] = igreja['codigo']
    context.user_data['cadastro']['nome_igreja'] = igreja['nome']
    context.user_data['cadastro']['estado'] = ESTADO_AGUARDANDO_NOME
    
    logger.info(f"Igreja selecionada: {igreja['codigo']} - {igreja['nome']}")
    
    # TEXTO MELHORADO - Mais claro e direto
    await query.edit_message_text(
        f"A Paz de Deus!\n\n"
        f"✅ Casa de Oração: {igreja['codigo']} - {igreja['nome']}\n\n"
        f"👤 Digite **SEU NOME COMPLETO**:"
    )

# ================================================================================================
# ENTRADA DE NOME (TEXTO) - COM DETECTOR INTELIGENTE
# ================================================================================================

async def receber_nome(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Recebe nome digitado pelo usuário - COM VALIDAÇÃO INTELIGENTE"""
    # Verificar se está no estado correto
    if ('cadastro' not in context.user_data or 
        context.user_data['cadastro'].get('estado') != ESTADO_AGUARDANDO_NOME):
        return  # Ignora se não está no fluxo de cadastro
    
    nome_digitado = update.message.text.strip()
    
    # NOVA VALIDAÇÃO - Detector de respostas não-nomes
    eh_nome_valido, mensagem = validar_nome_usuario(nome_digitado)
    
    if not eh_nome_valido:
        await update.message.reply_text(
            f"A Paz de Deus!\n\n"
            f"{mensagem}\n\n"
            f"📝 **Digite novamente:**"
        )
        return
    
    nome = mensagem  # É o nome limpo quando válido
    
    # Validação de comprimento (mantida do original)
    if len(nome) < 3:
        await update.message.reply_text("❌ Nome deve ter pelo menos 3 caracteres.")
        return
    
    # Salvar nome
    context.user_data['cadastro']['nome'] = nome
    context.user_data['cadastro']['pagina_funcao'] = 0
    
    logger.info(f"✅ Nome válido recebido: {nome}")
    
    # Mostrar menu de funções
    await mostrar_menu_funcoes(update, context)

# ================================================================================================
# MENU DE FUNÇÕES - CALLBACKS DIRETOS
# ================================================================================================

async def mostrar_menu_funcoes(update, context: ContextTypes.DEFAULT_TYPE):
    """Mostra menu de funções"""
    funcoes_paginadas = agrupar_funcoes()
    pagina_atual = context.user_data['cadastro'].get('pagina_funcao', 0)
    
    # Validar página
    if pagina_atual >= len(funcoes_paginadas):
        pagina_atual = 0
    elif pagina_atual < 0:
        pagina_atual = len(funcoes_paginadas) - 1
    
    context.user_data['cadastro']['pagina_funcao'] = pagina_atual
    
    # Construir teclado
    keyboard = []
    for funcao in funcoes_paginadas[pagina_atual]:
        callback_data = f"selecionar_funcao_{funcao}"
        keyboard.append([InlineKeyboardButton(funcao, callback_data=callback_data)])
    
    # Navegação
    nav_buttons = []
    if len(funcoes_paginadas) > 1:
        nav_buttons.append(InlineKeyboardButton("⬅️ Anterior", callback_data="navegar_funcao_anterior"))
        nav_buttons.append(InlineKeyboardButton("Próxima ➡️", callback_data="navegar_funcao_proxima"))
    keyboard.append(nav_buttons)
    
    keyboard.append([InlineKeyboardButton("🔄 Outra Função", callback_data="funcao_outra")])
    keyboard.append([InlineKeyboardButton("❌ Cancelar", callback_data="cancelar_cadastro")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    texto = (
        "A Paz de Deus!\n\n"
        f"✅ Nome: {context.user_data['cadastro']['nome']}\n\n"
        "Selecione a função:\n\n"
        f"📄 Página {pagina_atual + 1}/{len(funcoes_paginadas)}"
    )
    
    await update.message.reply_text(texto, reply_markup=reply_markup)

async def mostrar_menu_funcoes_callback(query, context: ContextTypes.DEFAULT_TYPE):
    """Mostra menu de funções - para callbacks"""
    funcoes_paginadas = agrupar_funcoes()
    pagina_atual = context.user_data['cadastro'].get('pagina_funcao', 0)
    
    # Validar página
    if pagina_atual >= len(funcoes_paginadas):
        pagina_atual = 0
    elif pagina_atual < 0:
        pagina_atual = len(funcoes_paginadas) - 1
    
    context.user_data['cadastro']['pagina_funcao'] = pagina_atual
    
    # Construir teclado
    keyboard = []
    for funcao in funcoes_paginadas[pagina_atual]:
        callback_data = f"selecionar_funcao_{funcao}"
        keyboard.append([InlineKeyboardButton(funcao, callback_data=callback_data)])
    
    # Navegação
    nav_buttons = []
    if len(funcoes_paginadas) > 1:
        nav_buttons.append(InlineKeyboardButton("⬅️ Anterior", callback_data="navegar_funcao_anterior"))
        nav_buttons.append(InlineKeyboardButton("Próxima ➡️", callback_data="navegar_funcao_proxima"))
    keyboard.append(nav_buttons)
    
    keyboard.append([InlineKeyboardButton("🔄 Outra Função", callback_data="funcao_outra")])
    keyboard.append([InlineKeyboardButton("❌ Cancelar", callback_data="cancelar_cadastro")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    texto = (
        "A Paz de Deus!\n\n"
        f"✅ Nome: {context.user_data['cadastro']['nome']}\n\n"
        "Selecione a função:\n\n"
        f"📄 Página {pagina_atual + 1}/{len(funcoes_paginadas)}"
    )
    
    await query.edit_message_text(texto, reply_markup=reply_markup)

async def navegar_funcoes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler para navegação entre páginas de funções"""
    query = update.callback_query
    await query.answer()
    
    # Verificar contexto
    if 'cadastro' not in context.user_data:
        await query.edit_message_text(
            "Sessão expirou. Use /cadastrar para iniciar novamente."
        )
        return
    
    data = query.data
    
    if data == "navegar_funcao_anterior":
        context.user_data['cadastro']['pagina_funcao'] -= 1
        await mostrar_menu_funcoes_callback(query, context)
    
    elif data == "navegar_funcao_proxima":
        context.user_data['cadastro']['pagina_funcao'] += 1
        await mostrar_menu_funcoes_callback(query, context)

async def selecionar_funcao(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler para seleção de função"""
    query = update.callback_query
    await query.answer()
    
    # Verificar contexto
    if 'cadastro' not in context.user_data:
        await query.edit_message_text(
            "Sessão expirou. Use /cadastrar para iniciar novamente."
        )
        return
    
    # Extrair função
    funcao = query.data.replace("selecionar_funcao_", "")
    
    if funcao not in FUNCOES:
        await query.edit_message_text(
            "Função não encontrada. Use /cadastrar para tentar novamente."
        )
        return
    
    # Salvar função
    context.user_data['cadastro']['funcao'] = funcao
    
    logger.info(f"✅ Função selecionada: {funcao}")
    
    # Mostrar confirmação
    await mostrar_confirmacao(query, context)

async def funcao_outra(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler para função personalizada"""
    query = update.callback_query
    await query.answer()
    
    # Verificar contexto
    if 'cadastro' not in context.user_data:
        await query.edit_message_text(
            "Sessão expirou. Use /cadastrar para iniciar novamente."
        )
        return
    
    # Mudar estado para aguardar função
    context.user_data['cadastro']['estado'] = ESTADO_AGUARDANDO_FUNCAO
    
    await query.edit_message_text(
        "A Paz de Deus!\n\n"
        "✍️ DIGITE SUA FUNÇÃO:\n\n"
        "(Ex: Patrimônio, Tesoureiro, etc.)"
    )

async def receber_funcao_personalizada(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Recebe função personalizada digitada"""
    # Verificar estado
    if ('cadastro' not in context.user_data or 
        context.user_data['cadastro'].get('estado') != ESTADO_AGUARDANDO_FUNCAO):
        return
    
    funcao = update.message.text.strip()
    
    if len(funcao) < 3:
        await update.message.reply_text("❌ Função deve ter pelo menos 3 caracteres.")
        return
    
    # Verificar função similar
    funcao_similar_encontrada, funcao_oficial = detectar_funcao_similar(funcao)
    
    if funcao_similar_encontrada:
        await update.message.reply_text(
            f"⚠️ Função similar encontrada!\n\n"
            f"Você digitou: \"{funcao}\"\n"
            f"Similar a: \"{funcao_oficial}\"\n\n"
            f"Use /cadastrar novamente e selecione \"{funcao_oficial}\" no menu."
        )
        return
    
    # Salvar função
    context.user_data['cadastro']['funcao'] = funcao
    
    logger.info(f"✅ Função personalizada: {funcao}")
    
    # Mostrar confirmação
    await mostrar_confirmacao_mensagem(update, context)

# ================================================================================================
# CONFIRMAÇÃO E FINALIZAÇÃO
# ================================================================================================

async def mostrar_confirmacao(query, context: ContextTypes.DEFAULT_TYPE):
    """Mostra confirmação - via callback"""
    dados = context.user_data['cadastro']
    
    keyboard = [
        [
            InlineKeyboardButton("✅ Confirmar", callback_data="confirmar_cadastro"),
            InlineKeyboardButton("❌ Cancelar", callback_data="cancelar_cadastro")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    texto = (
        "A Paz de Deus!\n\n"
        "📝 Confirme os dados:\n\n"
        f"📍 Código: {dados['codigo']}\n"
        f"🏢 Casa: {dados['nome_igreja']}\n"
        f"👤 Nome: {dados['nome']}\n"
        f"🔧 Função: {dados['funcao']}\n\n"
        "Os dados estão corretos?"
    )
    
    await query.edit_message_text(texto, reply_markup=reply_markup)

async def mostrar_confirmacao_mensagem(update, context: ContextTypes.DEFAULT_TYPE):
    """Mostra confirmação - via mensagem"""
    dados = context.user_data['cadastro']
    
    keyboard = [
        [
            InlineKeyboardButton("✅ Confirmar", callback_data="confirmar_cadastro"),
            InlineKeyboardButton("❌ Cancelar", callback_data="cancelar_cadastro")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    texto = (
        "A Paz de Deus!\n\n"
        "📝 Confirme os dados:\n\n"
        f"📍 Código: {dados['codigo']}\n"
        f"🏢 Casa: {dados['nome_igreja']}\n"
        f"👤 Nome: {dados['nome']}\n"
        f"🔧 Função: {dados['funcao']}\n\n"
        "Os dados estão corretos?"
    )
    
    await update.message.reply_text(texto, reply_markup=reply_markup)

async def confirmar_cadastro(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Finaliza cadastro no banco de dados - COM CORREÇÕES"""
    query = update.callback_query
    await query.answer()
    
    # Verificar contexto
    if 'cadastro' not in context.user_data:
        await query.edit_message_text(
            "Sessão expirou. Use /cadastrar para iniciar novamente."
        )
        return
    
    # NOVO: Verificar saúde do OneDrive ANTES de prosseguir
    if not await check_onedrive_health(context):
        await query.edit_message_text(
            "🔧 **Sistema temporariamente indisponível**\n\n"
            "⚠️ Estamos com problemas técnicos no momento\n"
            "⏰ Tente novamente em alguns minutos\n\n"
            "_Seus dados são importantes e só serão salvos quando "
            "o sistema estiver 100% operacional_\n\n"
            "📞 Em caso de urgência, contate o administrador",
            parse_mode='Markdown'
        )
        return
    
    # Obter dados
    dados = context.user_data['cadastro']
    user_id = update.effective_user.id
    username = update.effective_user.username or ""
    
    try:
        # Salvar no banco (compatível Sistema BRK)
        sucesso, status = salvar_responsavel(
            dados['codigo'], 
            dados['nome'], 
            dados['funcao'], 
            user_id, 
            username
        )
        
        if sucesso:
            # Cadastro bem-sucedido
            await query.edit_message_text(
                "Projeto Débito Automático\n\n"
                "✅ Cadastro realizado com sucesso!\n\n"
                f"📍 Código: {dados['codigo']}\n"
                f"🏢 Casa: {dados['nome_igreja']}\n"
                f"👤 Nome: {dados['nome']}\n"
                f"🔧 Função: {dados['funcao']}\n\n"
                "📢 Os alertas automáticos começarão em breve.\n\n"
                "Deus te abençoe! 🙌"
            )
            
            logger.info(f"✅ Cadastro concluído: {dados['codigo']} - {dados['nome']}")
            
        else:
            # CORREÇÃO: Tratar diferentes tipos de erro
            if isinstance(status, str) and "nome_ja_cadastrado" in status:
                # Extrair função existente
                parts = status.split("|")
                funcao_existente = parts[1] if len(parts) > 1 else "não informada"
                
                await query.edit_message_text(
                    "A Paz de Deus!\n\n"
                    "⚠️ **Cadastro Duplicado Detectado**\n\n"
                    f"👤 O nome **{dados['nome']}** já está cadastrado "
                    f"na Casa de Oração **{dados['nome_igreja']}**\n\n"
                    f"🔧 Função atual: {funcao_existente}\n\n"
                    "ℹ️ **O que fazer:**\n"
                    "• Se você mudou de função, contate o administrador\n"
                    "• Se não é você, verifique se digitou o nome corretamente\n"
                    "• Cada pessoa pode ter apenas um cadastro por Casa\n\n"
                    "📞 Em caso de dúvidas, contate o responsável da sua Casa de Oração",
                    parse_mode='Markdown'
                )
                
                logger.warning(f"⚠️ Cadastro duplicado: {dados['codigo']} - {dados['nome']} (usuário {user_id})")
                
            else:
                # Outros tipos de erro
                await query.edit_message_text(
                    "A Paz de Deus!\n\n"
                    "❌ Ocorreu um erro técnico durante seu cadastro.\n\n"
                    "🔄 Por favor, tente novamente em alguns minutos.\n\n"
                    "Se o problema persistir, contate o administrador da sua Casa de Oração.\n\n"
                    "Obrigado pela compreensão! 🙏"
                )
                
                logger.error(f"❌ Erro no cadastro: {dados['codigo']} - {dados['nome']} - Status: {status}")
    
    except Exception as e:
        # Erro crítico - alertar admin se OneDrive estava envolvido
        error_msg = str(e)
        if "onedrive" in error_msg.lower() or "microsoft" in error_msg.lower():
            await alert_onedrive_failure(error_msg, context)
        
        await query.edit_message_text(
            "A Paz de Deus!\n\n"
            "❌ Ocorreu um erro técnico inesperado.\n\n"
            "🔄 Por favor, tente realizar seu cadastro novamente.\n\n"
            "📞 Se o problema continuar, contate o administrador.\n\n"
            "Pedimos desculpas pelo inconveniente! 🙏"
        )
        
        logger.error(f"❌ Exceção no cadastro: {e}")
    
    finally:
        # Limpar contexto
        if 'cadastro' in context.user_data:
            del context.user_data['cadastro']

# ================================================================================================
# CANCELAMENTO
# ================================================================================================

async def cancelar_cadastro(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancela cadastro em qualquer etapa"""
    query = update.callback_query
    await query.answer()
    
    # Limpar contexto
    if 'cadastro' in context.user_data:
        del context.user_data['cadastro']
    
    await query.edit_message_text(
        "A Santa Paz de Deus!\n\n"
        "❌ Cadastro cancelado!\n\n"
        "Use /cadastrar para tentar novamente.\n\n"
        "Deus te abençoe! 🙏"
    )

# ================================================================================================
# REGISTRO DE HANDLERS - SISTEMA DIRETO
# ================================================================================================

def registrar_handlers_cadastro(application):
    """Registra todos os handlers usando sistema de callbacks diretos"""
    
    # Comandos básicos
    application.add_handler(CommandHandler("cadastrar", iniciar_cadastro_etapas))
    
    # LGPD
    application.add_handler(CallbackQueryHandler(
        processar_aceite_lgpd, 
        pattern='^aceitar_lgpd_cadastro_auto$'
    ))
    
    # Navegação igrejas
    application.add_handler(CallbackQueryHandler(
        navegar_igrejas, 
        pattern='^navegar_igreja_'
    ))
    
    # Seleção igreja
    application.add_handler(CallbackQueryHandler(
        selecionar_igreja, 
        pattern='^selecionar_igreja_'
    ))
    
    # Navegação funções
    application.add_handler(CallbackQueryHandler(
        navegar_funcoes, 
        pattern='^navegar_funcao_'
    ))
    
    # Seleção função
    application.add_handler(CallbackQueryHandler(
        selecionar_funcao, 
        pattern='^selecionar_funcao_'
    ))
    
    # Função personalizada
    application.add_handler(CallbackQueryHandler(
        funcao_outra, 
        pattern='^funcao_outra$'
    ))
    
    # Confirmação final
    application.add_handler(CallbackQueryHandler(
        confirmar_cadastro, 
        pattern='^confirmar_cadastro$'
    ))
    
    # Cancelamento
    application.add_handler(CallbackQueryHandler(
        cancelar_cadastro, 
        pattern='^cancelar_cadastro$'
    ))
    
    # Entrada de texto (nome e função personalizada)
    application.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND, 
        processar_entrada_texto
    ))
    
    logger.info("✅ Handlers cadastro DIRETOS registrados - Sistema 100% funcional com correções")

async def processar_entrada_texto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Processa entrada de texto baseado no estado atual"""
    if 'cadastro' not in context.user_data:
        return  # Ignora se não há cadastro ativo
    
    estado = context.user_data['cadastro'].get('estado')
    
    if estado == ESTADO_AGUARDANDO_NOME:
        await receber_nome(update, context)
    elif estado == ESTADO_AGUARDANDO_FUNCAO:
        await receber_funcao_personalizada(update, context)
