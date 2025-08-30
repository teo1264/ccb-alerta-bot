#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
📊 Comando /health para Administradores - Sistema CCB
🔍 Diagnóstico completo do sistema para admins
🚨 Integração com sistema de verificação OneDrive
"""

import os
import sqlite3
from datetime import datetime
from telegram.ext import CommandHandler

def get_admin_ids():
    """Obter IDs dos administradores"""
    admin_ids_str = os.getenv("ADMIN_IDS", "")
    return [admin_id.strip() for admin_id in admin_ids_str.split(',') if admin_id.strip()]

def check_database_health():
    """Verificar saúde do banco de dados"""
    try:
        # Tentar acessar database local
        db_path = "/opt/render/project/disk/shared_data/alertas_bot.db"  # Path no Render
        if not os.path.exists(db_path):
            db_path = "alertas_bot.db"  # Fallback local
            
        if not os.path.exists(db_path):
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
            "details": f"Database: {db_path}"
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
        bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
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
/restart - Reiniciar sistema
/sync - Forçar sincronização
/test - Testar componentes

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
    print(f"📊 Comando /health executado por admin {user_id} - Status: {overall_status}")

async def restart_command(update, context):
    """Comando /restart - Reiniciar componentes (placeholder)"""
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
    """Comando /sync - Forçar sincronização (placeholder)"""
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

def get_admin_command_handlers():
    """Retorna lista de handlers para comandos de admin"""
    return [
        CommandHandler("health", health_command),
        CommandHandler("restart", restart_command),
        CommandHandler("sync", sync_command)
    ]
