#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
📁 ARQUIVO: auth/microsoft_auth.py
💾 ONDE SALVAR: ccb-alerta-bot/auth/microsoft_auth.py  
📦 FUNÇÃO: Autenticação Microsoft Graph API para Bot Telegram
🔧 DESCRIÇÃO: Gerenciamento de tokens, refresh e credenciais Microsoft
👨‍💼 ADAPTADO PARA: CCB Alerta Bot (compartilhamento com sistema BRK)
🐛 VERSÃO DEBUG: Com logs detalhados para troubleshooting
"""

import os
import json
import requests
from pathlib import Path
from typing import Dict, Optional
import hashlib
from datetime import datetime
import base64
from cryptography.fernet import Fernet
import logging

# Logger específico
logger = logging.getLogger("CCB-Alerta-Bot.auth")

class MicrosoftAuth:
    """
    Gerenciador de autenticação Microsoft Graph API para Bot Telegram
    
    REUTILIZA a mesma lógica de segurança do sistema BRK:
    - Tokens criptografados no persistent disk
    - Renovação automática via refresh_token
    - Validação via environment variables
    - Compatibilidade total com sistema BRK
    """
    
    def __init__(self):
        """Inicializar autenticação com validação obrigatória"""
        
        # CONFIGURAÇÕES: CLIENT_ID via ambiente + TENANT_ID fixo (IGUAL BRK)
        self.client_id = os.getenv("MICROSOFT_CLIENT_ID")
        self.tenant_id = "consumers"  # FIXO igual BRK que funciona
        
        # VALIDAÇÃO OBRIGATÓRIA
        if not self.client_id:
            raise ValueError("❌ MICROSOFT_CLIENT_ID não configurado!")
        
        # Caminhos para tokens (persistent disk RENDER OFICIAL)
        self.token_file_persistent = "/opt/render/project/storage/token.json"
        self.token_file_local = "token.json"
        
        # DEBUG: Log dos caminhos
        logger.info(f"🔍 DEBUG: Arquivo persistent: {self.token_file_persistent}")
        logger.info(f"🔍 DEBUG: Arquivo local: {self.token_file_local}")
        logger.info(f"🔍 DEBUG: Persistent existe? {os.path.exists(self.token_file_persistent)}")
        logger.info(f"🔍 DEBUG: Local existe? {os.path.exists(self.token_file_local)}")
        
        # Estado de autenticação
        self.access_token = None
        self.refresh_token = None
        
        # Carregar tokens existentes
        tokens_ok = self.carregar_token()
        
        logger.info(f"🔐 Microsoft Auth BOT inicializado")
        logger.info(f"   Client ID: configurado e protegido")
        logger.info(f"   Tenant: {self.tenant_id}")
        logger.info(f"   Token: {'✅ OK' if tokens_ok else '❌ Faltando'}")

    def _get_encryption_key(self):
        """Obter ou gerar chave de criptografia (PATH RENDER OFICIAL)"""
        key_file = "/opt/render/project/storage/.encryption_key"
        try:
            if os.path.exists(key_file):
                with open(key_file, 'rb') as f:
                    return f.read()
            
            key = Fernet.generate_key()
            with open(key_file, 'wb') as f:
                f.write(key)
            os.chmod(key_file, 0o600)
            return key
        except Exception:
            # Fallback: gerar chave determinística (PADRÃO BRK CORRIGIDO)
            unique_data = f"{self.client_id}{os.getenv('RENDER_SERVICE_ID', 'fallback')}"
            return base64.urlsafe_b64encode(hashlib.sha256(unique_data.encode()).digest())

    def _encrypt_token_data(self, token_data):
        """Criptografar dados do token"""
        try:
            key = self._get_encryption_key()
            cipher = Fernet(key)
            json_data = json.dumps(token_data).encode('utf-8')
            return cipher.encrypt(json_data)
        except Exception:
            return None

    def _decrypt_token_data(self, encrypted_data):
        """Descriptografar dados do token"""
        try:
            key = self._get_encryption_key()
            cipher = Fernet(key)
            decrypted_data = cipher.decrypt(encrypted_data)
            return json.loads(decrypted_data.decode('utf-8'))
        except Exception:
            return None
    
    def carregar_token(self) -> bool:
        """
        Carregar token do persistent disk ou local
        
        Prioridade:
        1. /opt/render/project/storage/token.json (persistent disk)
        2. ./token.json (local para desenvolvimento)
        
        Returns:
            bool: True se tokens carregados com sucesso
        """
        logger.info("🔍 DEBUG: Iniciando carregamento de token...")
        
        if os.path.exists(self.token_file_persistent):
            logger.info(f"🔍 DEBUG: Arquivo persistent encontrado: {self.token_file_persistent}")
            return self._carregar_do_arquivo(self.token_file_persistent)
        elif os.path.exists(self.token_file_local):
            logger.info(f"🔍 DEBUG: Arquivo local encontrado: {self.token_file_local}")
            return self._carregar_do_arquivo(self.token_file_local)
        else:
            logger.info("🔍 DEBUG: Nenhum arquivo de token encontrado")
            logger.info(f"🔍 DEBUG: Tentou persistent: {self.token_file_persistent}")
            logger.info(f"🔍 DEBUG: Tentou local: {self.token_file_local}")
            logger.info("💡 Token não encontrado - use mesmo token do sistema BRK")
            return False
    
    def _carregar_do_arquivo(self, filepath: str) -> bool:
        """
        Carregar token de arquivo específico (com suporte a criptografia)
        """
        try:
            logger.info(f"🔍 DEBUG: Tentando carregar arquivo: {filepath}")
            
            # 🔐 LÓGICA: Tentar carregar arquivo criptografado primeiro
            encrypted_file = filepath.replace('.json', '.enc')
            logger.info(f"🔍 DEBUG: Verificando arquivo criptografado: {encrypted_file}")
            
            if os.path.exists(encrypted_file):
                logger.info(f"🔍 DEBUG: Arquivo criptografado encontrado")
                with open(encrypted_file, 'rb') as f:
                    encrypted_data = f.read()
                token_data = self._decrypt_token_data(encrypted_data)
                if token_data:
                    self.access_token = token_data.get('access_token')
                    self.refresh_token = token_data.get('refresh_token')
                    if self.access_token and self.refresh_token:
                        logger.info(f"🔒 Token CRIPTOGRAFADO carregado: {encrypted_file}")
                        return True
            
            # Fallback: carregar arquivo JSON original
            logger.info(f"🔍 DEBUG: Tentando carregar JSON original: {filepath}")
            with open(filepath, 'r') as f:
                token_data = json.load(f)
            
            logger.info(f"🔍 DEBUG: JSON carregado com sucesso")
            
            self.access_token = token_data.get('access_token')
            self.refresh_token = token_data.get('refresh_token')
            
            logger.info(f"🔍 DEBUG: access_token existe? {bool(self.access_token)}")
            logger.info(f"🔍 DEBUG: refresh_token existe? {bool(self.refresh_token)}")
            
            if self.access_token and self.refresh_token:
                logger.info(f"✅ Tokens carregados de: {filepath}")
                return True
            else:
                logger.info(f"❌ Tokens incompletos em: {filepath}")
                return False
                
        except json.JSONDecodeError as e:
            logger.error(f"❌ JSON inválido em {filepath}: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ Erro carregando {filepath}: {e}")
            return False
    
    def salvar_token_persistent(self) -> bool:
        """
        Salvar token no persistent disk com proteção de segurança E CRIPTOGRAFIA
        """
        try:
            # 🔒 PROTEÇÃO: Proteger diretório
            token_dir = os.path.dirname(self.token_file_persistent)
            os.makedirs(token_dir, exist_ok=True)
            os.chmod(token_dir, 0o700)  # Apenas proprietário
            
            token_data = {
                'access_token': self.access_token,
                'refresh_token': self.refresh_token,
                'expires_in': 3600,
                'token_type': 'Bearer',
                'scope': 'https://graph.microsoft.com/.default offline_access',
                # 🔒 Metadados de segurança:
                'saved_at': datetime.now().isoformat(),
                'client_hash': hashlib.sha256(self.client_id.encode()).hexdigest()[:8],
                'app_type': 'ccb_alerta_bot'  # Identificar origem
            }
            
            # 🔐 LÓGICA: Tentar salvar criptografado primeiro
            encrypted_data = self._encrypt_token_data(token_data)
            if encrypted_data:
                encrypted_file = self.token_file_persistent.replace('.json', '.enc')
                with open(encrypted_file, 'wb') as f:
                    f.write(encrypted_data)
                os.chmod(encrypted_file, 0o600)
                # Remover arquivo antigo não criptografado se existir
                if os.path.exists(self.token_file_persistent):
                    os.remove(self.token_file_persistent)
                logger.info(f"🔒 Token salvo CRIPTOGRAFADO: {encrypted_file}")
            else:
                # Fallback: salvar sem criptografia
                with open(self.token_file_persistent, 'w') as f:
                    json.dump(token_data, f, indent=2)
                os.chmod(self.token_file_persistent, 0o600)
                logger.info(f"💾 Token salvo com proteção: {self.token_file_persistent}")
            
            return True
        except Exception as e:
            logger.error(f"❌ Erro salvando token protegido: {e}")
            return False
    
    def atualizar_token(self) -> bool:
        """
        Renovar access_token usando refresh_token
        
        Returns:
            bool: True se renovação bem-sucedida
        """
        if not self.refresh_token:
            logger.error("❌ Refresh token não disponível")
            return False
        
        try:
            url = f"https://login.microsoftonline.com/{self.tenant_id}/oauth2/v2.0/token"
            
            data = {
                'client_id': self.client_id,
                'grant_type': 'refresh_token',
                'refresh_token': self.refresh_token,
                'scope': 'https://graph.microsoft.com/.default offline_access'
            }
            
            response = requests.post(url, data=data, timeout=30)
            
            if response.status_code == 200:
                token_data = response.json()
                
                # Atualizar access_token
                self.access_token = token_data['access_token']
                
                # Atualizar refresh_token se fornecido
                if 'refresh_token' in token_data:
                    self.refresh_token = token_data['refresh_token']
                
                # Salvar no persistent disk
                self.salvar_token_persistent()
                
                logger.info("✅ Token renovado com sucesso")
                return True
                
            else:
                logger.error(f"❌ Erro renovando token: HTTP {response.status_code}")
                try:
                    error_detail = response.json()
                    logger.error(f"   Detalhes: {error_detail.get('error_description', 'N/A')}")
                except:
                    pass
                return False
                
        except requests.RequestException as e:
            logger.error(f"❌ Erro de rede na renovação: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ Erro inesperado na renovação: {e}")
            return False
    
    def validar_token(self) -> bool:
        """
        Validar se access_token atual está funcional
        
        Returns:
            bool: True se token válido
        """
        if not self.access_token:
            return False
        
        try:
            headers = {'Authorization': f'Bearer {self.access_token}'}
            response = requests.get(
                'https://graph.microsoft.com/v1.0/me',
                headers=headers,
                timeout=10
            )
            
            return response.status_code == 200
            
        except Exception:
            return False
    
    def obter_headers_autenticados(self) -> Dict[str, str]:
        """
        Obter headers HTTP com autenticação (COM RENOVAÇÃO AUTOMÁTICA)
        
        Returns:
            Dict[str, str]: Headers prontos para requisições Graph API
        """
        # Renovar token se necessário
        if not self.validar_token():
            logger.info("🔄 Token inválido, renovando automaticamente...")
            if not self.atualizar_token():
                raise ValueError("❌ Falha na renovação automática do token")
        
        if not self.access_token:
            raise ValueError("❌ Access token não disponível")
        
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }
        
        return headers
    
    def tentar_renovar_se_necessario(self, response_status: int) -> bool:
        """
        Tentar renovar token se requisição retornou 401
        
        Args:
            response_status (int): Status HTTP da requisição que falhou
            
        Returns:
            bool: True se renovação foi bem-sucedida
        """
        if response_status == 401:
            logger.info("🔄 Token expirado detectado, tentando renovar...")
            return self.atualizar_token()
        
        return False
    
    def status_autenticacao(self) -> Dict:
        """
        Obter status atual da autenticação
        
        Returns:
            Dict: Informações sobre estado da autenticação
        """
        return {
            "client_id_configurado": bool(self.client_id),
            "client_id_protegido": f"{self.client_id[:8]}******" if self.client_id else "N/A",
            "tenant_id": self.tenant_id,
            "access_token_presente": bool(self.access_token),
            "refresh_token_presente": bool(self.refresh_token),
            "arquivo_token_persistent": os.path.exists(self.token_file_persistent),
            "arquivo_token_local": os.path.exists(self.token_file_local),
            "app_type": "ccb_alerta_bot"
        }
