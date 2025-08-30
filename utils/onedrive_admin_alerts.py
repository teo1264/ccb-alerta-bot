#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🚨 OneDrive Admin Alerts - Sistema de Alertas para Falhas Críticas
📱 Integra com sistema existente do CCB Alerta Bot
🔧 Notifica admins via Telegram quando OneDrive falha
"""

import os
import requests
from datetime import datetime

def get_admin_ids():
    """Obter IDs dos administradores da variável ADMIN_IDS"""
    admin_ids_str = os.getenv("ADMIN_IDS", "")
    return [admin_id.strip() for admin_id in admin_ids_str.split(',') if admin_id.strip()]

def send_telegram_to_admin(admin_id, message):
    """Enviar mensagem Telegram para admin específico"""
    try:
        bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        if not bot_token:
            return False
            
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        data = {
            'chat_id': admin_id,
            'text': message,
            'parse_mode': 'Markdown'
        }
        
        response = requests.post(url, data=data, timeout=10)
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Erro enviando Telegram para admin {admin_id}: {e}")
        return False

def alert_onedrive_failure(error_details):
    """Alertar todos os admins sobre falha do OneDrive"""
    admin_ids = get_admin_ids()
    if not admin_ids:
        print("❌ Nenhum admin configurado para alertas OneDrive")
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
        if send_telegram_to_admin(admin_id, message):
            success_count += 1
            print(f"✅ Alerta OneDrive enviado para admin {admin_id}")
    
    print(f"🚨 Alerta enviado para {success_count}/{len(admin_ids)} admins")
    return success_count > 0

def alert_onedrive_recovery():
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
        if send_telegram_to_admin(admin_id, message):
            success_count += 1
    
    print(f"✅ Recuperação notificada para {success_count}/{len(admin_ids)} admins")
    return success_count > 0
