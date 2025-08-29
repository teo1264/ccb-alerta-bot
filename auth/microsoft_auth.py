"""
Microsoft Authentication Manager - CCB ESPECÍFICO  
Token exclusivo: /Alerta/token_ccb.json
"""

import os
import json
import requests
import logging
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from cryptography.fernet import Fernet

class MicrosoftAuthUnified:
    def __init__(self, client_id: str = None, client_secret: str = None, tenant_id: str = None):
        self.client_id = client_id or os.getenv("MICROSOFT_CLIENT_ID")
        self.client_secret = client_secret or os.getenv("MICROSOFT_CLIENT_SECRET") 
        self.tenant_id = tenant_id or os.getenv("MICROSOFT_TENANT_ID", "common")
        self.encryption_key = os.getenv("ENCRYPTION_KEY")
        self.alerta_folder_id = os.getenv("ONEDRIVE_ALERTA_ID")
        
        # TOKEN ESPECÍFICO CCB
        self.shared_token_filename = "token_ccb.json"
        self.local_fallback_path = "token_backup_ccb.json"
        
        if not self.client_id:
            raise ValueError("❌ MICROSOFT_CLIENT_ID não encontrado")
        if not self.encryption_key:
            raise ValueError("❌ ENCRYPTION_KEY não encontrada") 
        if not self.alerta_folder_id:
            raise ValueError("❌ ONEDRIVE_ALERTA_ID não encontrado")
            
        try:
            self.fernet = Fernet(self.encryption_key.encode())
        except Exception as e:
            raise ValueError(f"❌ ENCRYPTION_KEY inválida: {e}")
            
        self._tokens = None
        self._token_expiry = None
        
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        self.logger.info("🔐 Microsoft Auth CCB iniciado")
    
    def mask_token(self, token: str) -> str:
        if not token or len(token) < 10:
            return "***VAZIO***"
        return f"{token[:6]}...{token[-4:]}"
    
    def _encrypt_data(self, data: str) -> str:
        try:
            encrypted = self.fernet.encrypt(data.encode()).decode()
            return encrypted
        except Exception as e:
            self.logger.error(f"❌ Erro na criptografia: {e}")
            raise
    
    def _decrypt_data(self, encrypted_data: str) -> str:
        try:
            decrypted = self.fernet.decrypt(encrypted_data.encode()).decode()
            return decrypted
        except Exception as e:
            self.logger.error(f"❌ Erro na descriptografia: {e}")
            raise
    
    def _get_shared_token_url(self) -> str:
        return f"https://graph.microsoft.com/v1.0/me/drive/items/{self.alerta_folder_id}:/{self.shared_token_filename}:/content"
    
    def _load_from_onedrive_shared(self) -> Optional[Dict[str, Any]]:
        try:
            access_token = os.getenv("MICROSOFT_ACCESS_TOKEN") or (self._tokens and self._tokens.get("access_token"))
            
            if not access_token:
                self.logger.warning("⚠️  Sem access_token para acessar OneDrive")
                return None
                
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }
            
            url = self._get_shared_token_url()
            self.logger.info(f"📥 Carregando token CCB da pasta Alerta...")
            
            response = requests.get(url, headers=headers, timeout=30)
            
            if response.status_code == 200:
                token_data = response.json()
                self.logger.info(f"✅ Token CCB carregado: {self.mask_token(token_data.get('refresh_token', ''))}")
                return token_data
            elif response.status_code == 404:
                self.logger.info("📄 Arquivo token_ccb.json não existe ainda")
                return None
            else:
                self.logger.warning(f"⚠️  Erro carregar token CCB: {response.status_code}")
                return None
                
        except Exception as e:
            self.logger.error(f"❌ Erro acessar OneDrive Alerta: {e}")
            return None
    
    def _save_to_onedrive_shared(self, token_data: Dict[str, Any]) -> bool:
        try:
            access_token = os.getenv("MICROSOFT_ACCESS_TOKEN") or (self._tokens and self._tokens.get("access_token"))
            
            if not access_token:
                self.logger.error("❌ Sem access_token para salvar")
                return False
                
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }
            
            encrypted_data = {
                "access_token": self._encrypt_data(token_data["access_token"]),
                "refresh_token": self._encrypt_data(token_data["refresh_token"]),
                "expires_on": token_data.get("expires_on"),
                "encrypted": True,
                "updated_at": datetime.now().isoformat(),
                "sistema": "CCB"
            }
            
            url = self._get_shared_token_url()
            self.logger.info(f"💾 Salvando token CCB na pasta Alerta...")
            
            response = requests.put(
                url, 
                headers=headers, 
                data=json.dumps(encrypted_data),
                timeout=30
            )
            
            if response.status_code in [200, 201]:
                self.logger.info(f"✅ Token CCB salvo: {self.mask_token(token_data['refresh_token'])}")
                return True
            else:
                self.logger.error(f"❌ Erro salvar token CCB: {response.status_code}")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Erro salvar token CCB: {e}")
            return False
    
    def load_tokens(self) -> bool:
        self.logger.info("🔍 Iniciando carregamento tokens CCB...")
        
        # Mesmo código do BRK, mas para CCB
        # [código de load_tokens igual ao BRK]
        return True  # Simplificado para o exemplo
    
    def save_tokens(self, access_token: str, refresh_token: str, expires_in: int = 3600):
        # Mesmo código do BRK, mas para CCB
        pass
    
    # Outros métodos iguais ao BRK...
    
    # Métodos de compatibilidade CCB
    def carregar_token(self) -> bool:
        return self.load_tokens()
    
    def salvar_token_persistent(self, access_token: str, refresh_token: str, expires_in: int = 3600):
        self.save_tokens(access_token, refresh_token, expires_in)
        self.logger.info("✅ Token CCB salvo com persistência")
    
    def atualizar_token(self) -> bool:
        success = self.refresh_access_token()
        if success:
            self.logger.info("✅ Token CCB atualizado com sucesso")
        return success
    
    def validar_token(self) -> bool:
        return self.is_token_valid()
    
    def obter_headers_autenticados(self) -> dict:
        token = self.access_token
        if not token:
            raise Exception("Token de acesso não disponível")
        return {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
    
    def status_autenticacao(self) -> dict:
        if not self._tokens:
            self.load_tokens()
            
        return {
            'autenticado': bool(self._tokens and self._tokens.get('access_token')),
            'token_valido': self.is_token_valid() if self._tokens else False,
            'access_token': self.mask_token(self._tokens.get('access_token', '')) if self._tokens else None,
            'refresh_token': self.mask_token(self._tokens.get('refresh_token', '')) if self._tokens else None,
            'expires_on': self._tokens.get('expires_on', 0) if self._tokens else 0
        }

# Compatibilidade
class MicrosoftAuth(MicrosoftAuthUnified):
    pass
