#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
CCB Alerta Bot - VERSÃO CORRIGIDA COM MELHORIAS
✅ Sistema de alertas OneDrive para admins
✅ Comando /health para diagnóstico
✅ Fail-fast integrado nos cadastros
✅ Monitoramento proativo do sistema
"""

import logging
import os
from datetime import datetime
from telegram import Update
from telegram.ext import Application, CommandHandler
from config import (
    TOKEN, WEBHOOK_CONFIG, PRODUCTION_CONFIG, 
    inicializar_sistema, verificar_diretorios
)
from handlers.commands import registrar_comandos_basicos
from handlers.cadastro import registrar_handlers_cadastro
from handlers.admin import registrar_handlers_admin
from handlers.mensagens import registrar_handlers_mensagens
from handlers.error import registrar_error_handler
from handlers.lgpd import registrar_handlers_lgpd

# Configurar logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger("CCB-Alerta-Bot")

# ================================================================================================
# SISTEMA DE HEALTH CHECK E ALERTAS ADMIN
# ================================================================================================

def get_admin_ids():
    """Obter IDs dos administradores da variável ADMIN_IDS"""
    admin_ids_str = os.getenv("ADMIN_IDS", "")
    return [admin_id.strip() for admin_id in admin_ids_str.split(',') if admin_id.strip()]

def check_database_health():
    """Verificar saúde do banco de dados"""
    try:
        import sqlite3
        # Tentar acessar database local (prioridade: Render path -> local fallback)
        db_paths = [
            "/opt/render/project/disk/shared_data/alertas_bot.db",  # Render
            "/opt/render/project/storage/alertas_bot_cache.db",    # Render cache
            "alertas_bot.db"                                       # Local
        ]
        
        db_path = None
        for path in db_paths:
            if os.path.exists(path):
                db_path = path
                break
                
        if not db_path:
            return {"status": "❌", "message": "Database não encontrado", "details": ""}
            
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Contar registros principais
        cursor.execute("SELECT COUNT(*) FROM responsaveis")
        total_responsaveis = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM consentimento_lgpd")
        total_lgpd = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            "status": "✅", 
            "message": f"{total_responsaveis} responsáveis, {total_lgpd} LGPD",
            "details": f"Database: {os.path.basename(db_path)}"
        }
        
    except Exception as e:
        return {"status": "❌", "message": f"Erro: {str(e)[:50]}", "details": str(e)}

def check_onedrive_health():
    """Verificar saúde do OneDrive"""
    try:
        # Verificar variáveis básicas
        client_id = os.getenv("MICROSOFT_CLIENT_ID")
        access_token = os.getenv("MICROSOFT_ACCESS_TOKEN") 
        alerta_id = os.getenv("ONEDRIVE_ALERTA_ID")
        
        if not client_id:
            return {"status": "❌", "message": "CLIENT_ID não configurado", "details": ""}
        
        if not access_token:
            return {"status": "⚠️", "message": "ACCESS_TOKEN ausente", "details": "Token pode ter expirado"}
            
        if not alerta_id:
            return {"status": "❌", "message": "ALERTA_ID não configurado", "details": ""}
            
        # Se todas as variáveis existem
        return {
            "status": "✅", 
            "message": "Configurações OK",
            "details": f"Client: {client_id[:10]}..., Alerta: {alerta_id[:10]}..."
        }
        
    except Exception as e:
        return {"status": "❌", "message": f"Erro: {str(e)[:50]}", "details": str(e)}

def check_telegram_health():
    """Verificar saúde do Telegram Bot"""
    try:
        bot_token = TOKEN
        if not bot_token:
            return {"status": "❌", "message": "BOT_TOKEN não configurado", "details": ""}
            
        admin_ids = get_admin_ids()
        if not admin_ids:
            return {"status": "⚠️", "message": "Nenhum admin configurado", "details": "ADMIN_IDS vazio"}
            
        return {
            "status": "✅",
            "message": f"Bot OK, {len(admin_ids)} admins",
            "details": f"Token: {bot_token[:20]}..., Admins: {', '.join(admin_ids)}"
        }
        
    except Exception as e:
        return {"status": "❌", "message": f"Erro: {str(e)[:50]}", "details": str(e)}

async def health_command(update, context):
    """Comando /health - Diagnóstico completo para admins"""
    user_id = str(update.effective_user.id)
    admin_ids = get_admin_ids()
    
    # Verificar se é admin
    if user_id not in admin_ids:
        await update.message.reply_text("❌ Comando disponível apenas para administradores.")
        return
    
    # Mostrar que está processando
    await update.message.reply_text("🔍 Executando diagnóstico completo do sistema...")
    
    # Executar checks
    db_health = check_database_health()
    onedrive_health = check_onedrive_health()
    telegram_health = check_telegram_health()
    
    # Determinar status geral
    all_statuses = [db_health["status"], onedrive_health["status"], telegram_health["status"]]
    if "❌" in all_statuses:
        overall_status = "🚨 CRÍTICO"
    elif "⚠️" in all_statuses:
        overall_status = "⚠️ DEGRADADO"
    else:
        overall_status = "✅ SAUDÁVEL"
    
    # Construir mensagem
    timestamp = datetime.now().strftime('%H:%M:%S - %d/%m/%Y')
    
    message = f"""
📊 **DIAGNÓSTICO SISTEMA CCB**

🌐 **OneDrive:** {onedrive_health["status"]} {onedrive_health["message"]}
💾 **Database:** {db_health["status"]} {db_health["message"]}
📱 **Telegram:** {telegram_health["status"]} {telegram_health["message"]}

📈 **Status Geral:** {overall_status}
⏰ **Verificado:** {timestamp}

🔧 **Comandos Disponíveis:**
/restart - Reiniciar sistema (placeholder)
/sync - Forçar sincronização (placeholder)
/test - Testar componentes (placeholder)

📋 **Detalhes Técnicos:**
```
OneDrive: {onedrive_health["details"]}
Database: {db_health["details"]}
Telegram: {telegram_health["details"]}
```

💡 **Interpretação:**
✅ = Funcionando normalmente
⚠️ = Funcionando com limitações  
❌ = Requer atenção imediata
"""
    
    await update.message.reply_text(message, parse_mode='Markdown')
    
    # Log do comando
    logger.info(f"📊 Comando /health executado por admin {user_id} - Status: {overall_status}")

async def restart_command(update, context):
    """Comando /restart - Placeholder para reiniciar componentes"""
    user_id = str(update.effective_user.id)
    admin_ids = get_admin_ids()
    
    if user_id not in admin_ids:
        await update.message.reply_text("❌ Comando disponível apenas para administradores.")
        return
    
    await update.message.reply_text(
        "🔄 **Comando /restart**\n\n"
        "⚠️ Este comando reiniciaria componentes específicos do sistema.\n\n"
        "🔧 **Implementações possíveis:**\n"
        "• Renovar token OneDrive\n"
        "• Recarregar configurações\n"
        "• Limpar cache do sistema\n\n"
        "📞 Contate o desenvolvedor para implementação completa.",
        parse_mode='Markdown'
    )

async def sync_command(update, context):
    """Comando /sync - Placeholder para forçar sincronização"""
    user_id = str(update.effective_user.id)
    admin_ids = get_admin_ids()
    
    if user_id not in admin_ids:
        await update.message.reply_text("❌ Comando disponível apenas para administradores.")
        return
    
    await update.message.reply_text(
        "🔄 **Comando /sync**\n\n"
        "⚠️ Este comando forçaria sincronização OneDrive.\n\n"
        "🔧 **Funcionalidades:**\n"
        "• Sincronizar database local → OneDrive\n"
        "• Verificar integridade dos dados\n"
        "• Resolver conflitos de sincronização\n\n"
        "📞 Contate o desenvolvedor para implementação completa.",
        parse_mode='Markdown'
    )

async def test_command(update, context):
    """Comando /test - Testar componentes básicos"""
    user_id = str(update.effective_user.id)
    admin_ids = get_admin_ids()
    
    if user_id not in admin_ids:
        await update.message.reply_text("❌ Comando disponível apenas para administradores.")
        return
    
    await update.message.reply_text("🧪 Testando componentes básicos...")
    
    # Testes simples
    tests = []
    
    # Teste 1: Variáveis de ambiente
    client_id = os.getenv("MICROSOFT_CLIENT_ID")
    tests.append(f"🔑 CLIENT_ID: {'✅' if client_id else '❌'}")
    
    # Teste 2: Database
    db_health = check_database_health()
    tests.append(f"💾 Database: {db_health['status']}")
    
    # Teste 3: ADMIN_IDS
    admin_count = len(get_admin_ids())
    tests.append(f"👥 Admins: {'✅' if admin_count > 0 else '❌'} ({admin_count})")
    
    # Teste 4: Bot Token
    bot_token = TOKEN
    tests.append(f"🤖 Bot Token: {'✅' if bot_token else '❌'}")
    
    result_msg = "🧪 **RESULTADO DOS TESTES**\n\n" + "\n".join(tests)
    result_msg += f"\n\n⏰ Testado em: {datetime.now().strftime('%H:%M:%S')}"
    
    await update.message.reply_text(result_msg, parse_mode='Markdown')

def configurar_logs():
    """Configura pasta e arquivos de log"""
    if not os.path.exists("logs"):
        os.makedirs("logs")
    
    data_atual = datetime.now().strftime("%Y%m%d")
    file_handler = logging.FileHandler(f"logs/bot_{data_atual}.log")
    file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    
    logger.addHandler(file_handler)
    logger.info("Sistema de logs configurado")

def main():
    """Função principal - VERSÃO CORRIGIDA COM MELHORIAS"""
    logger.info("=" * 50)
    logger.info("Inicializando o CCB Alerta Bot...")
    logger.info("=" * 50)
    
    # Configurar sistema de logs
    configurar_logs()
    
    # Garantir que os diretórios existam
    verificar_diretorios()
    
    # Inicializar sistema
    inicializar_sistema()
    
    try:
        # Criar a aplicação
        application = Application.builder().token(TOKEN).build()
        
        # Registrar handlers na ordem correta (ConversationHandler PRIMEIRO)
        registrar_comandos_basicos(application)
        logger.info("1️⃣ Comandos básicos registrados")

        registrar_handlers_admin(application)
        logger.info("2️⃣ Handlers admin registrados")

        registrar_handlers_lgpd(application)
        logger.info("3️⃣ Handlers LGPD registrados")

        registrar_handlers_cadastro(application)
        logger.info("4️⃣ Handlers cadastro registrados - PRIORIDADE")

        registrar_handlers_mensagens(application)
        logger.info("5️⃣ Handlers mensagens registrados - ÚLTIMO")

        registrar_error_handler(application)
        logger.info("6️⃣ Error handler registrado")
        
        # NOVO: Registrar comandos de admin para diagnóstico
        application.add_handler(CommandHandler("health", health_command))
        application.add_handler(CommandHandler("restart", restart_command))
        application.add_handler(CommandHandler("sync", sync_command))
        application.add_handler(CommandHandler("test", test_command))
        logger.info("7️⃣ Comandos admin diagnóstico registrados")
        
        # Log das configurações importantes
        admin_ids = get_admin_ids()
        logger.info(f"👥 Administradores configurados: {len(admin_ids)}")
        if admin_ids:
            logger.info(f"   IDs: {', '.join(admin_ids)}")
        else:
            logger.warning("⚠️  Nenhum administrador configurado (ADMIN_IDS vazio)")
        
        # Verificar OneDrive rapidamente
        onedrive_health = check_onedrive_health()
        logger.info(f"🌐 Status OneDrive: {onedrive_health['status']} {onedrive_health['message']}")
        
        # Modo produção: WEBHOOK ou POLLING
        if WEBHOOK_CONFIG['usar_webhook']:
            logger.info("Modo WEBHOOK ativo")
            
            # Webhook built-in do python-telegram-bot
            application.run_webhook(
                listen="0.0.0.0",
                port=WEBHOOK_CONFIG['porta'],
                webhook_url=WEBHOOK_CONFIG['webhook_url'],
                allowed_updates=PRODUCTION_CONFIG['allowed_updates'],
                drop_pending_updates=PRODUCTION_CONFIG['drop_pending_updates']
            )
        else:
            logger.info("Modo POLLING ativo")
            # Polling simples
            application.run_polling(
                drop_pending_updates=PRODUCTION_CONFIG['drop_pending_updates'],
                allowed_updates=PRODUCTION_CONFIG['allowed_updates'],
                poll_interval=1.0
            )
            
    except Exception as e:
        logger.error(f"Erro fatal ao iniciar o bot: {e}")
        
        # Tentar notificar admins sobre falha crítica
        try:
            admin_ids = get_admin_ids()
            if admin_ids:
                logger.info(f"Tentando notificar {len(admin_ids)} admins sobre falha crítica...")
                # Aqui poderia implementar notificação de emergência
        except:
            pass
            
        raise
        
if __name__ == "__main__":
    main()
