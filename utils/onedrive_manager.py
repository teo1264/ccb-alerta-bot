#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
📁 ARQUIVO: utils/onedrive_manager.py
💾 ONDE SALVAR: ccb-alerta-bot/utils/onedrive_manager.py
📦 FUNÇÃO: Gerenciador OneDrive para banco de dados compartilhado
🔧 DESCRIÇÃO: Upload/download SQLite, criação estrutura, fallback local
👨‍💼 ADAPTADO PARA: CCB Alerta Bot
"""

import os
import requests
import sqlite3
import tempfile
import shutil
from datetime import datetime
import pytz
import logging
from typing import Optional, Dict, Tuple

# Logger específico
logger = logging.getLogger("CCB-Alerta-Bot.onedrive")

class OneDriveManager:
    """
    Gerenciador OneDrive para banco de dados compartilhado
    
    Responsabilidades:
    - Upload/download SQLite para OneDrive/Alerta/
    - Criação automática da estrutura de pastas
    - Fallback para storage local em caso de falha
    - Sincronização bidirecional (OneDrive ↔ Local)
    """
    
    def __init__(self, auth_manager):
        """
        Inicializar gerenciador OneDrive
        
        Args:
            auth_manager: Instância MicrosoftAuth configurada
        """
        self.auth = auth_manager
        
        # Configurações OneDrive
        self.alerta_folder_id = os.getenv("ONEDRIVE_ALERTA_ID")
        self.base_url = "https://graph.microsoft.com/v1.0"
        
        # Caminhos locais (fallback)
        self.local_storage_path = "/opt/render/project/storage"
        self.local_db_path = os.path.join(self.local_storage_path, "alertas_bot_local.db")
        
        # Garantir que diretório local existe
        os.makedirs(self.local_storage_path, exist_ok=True)
        
        logger.info("🔧 OneDriveManager inicializado")
        logger.info(f"   Pasta Alerta ID: {'✅ Configurado' if self.alerta_folder_id else '❌ Não configurado'}")
    
    def _obter_headers(self) -> Dict[str, str]:
        """Obter headers autenticados para requisições"""
        try:
            return self.auth.obter_headers_autenticados()
        except Exception as e:
            logger.error(f"❌ Erro obtendo headers: {e}")
            return {}
    
    def descobrir_pasta_alerta_id(self) -> Optional[str]:
        """
        Descobrir automaticamente o ID da pasta 'Alerta' no OneDrive
        
        Returns:
            str: ID da pasta Alerta ou None se não encontrada
        """
        try:
            headers = self._obter_headers()
            if not headers:
                return None
            
            # Buscar pasta 'Alerta' na raiz do OneDrive
            url = f"{self.base_url}/me/drive/root/children"
            params = {"$filter": "name eq 'Alerta' and folder ne null"}
            
            response = requests.get(url, headers=headers, params=params, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('value'):
                    pasta_id = data['value'][0]['id']
                    logger.info(f"✅ Pasta 'Alerta' encontrada: {pasta_id}")
                    return pasta_id
                else:
                    logger.info("📁 Pasta 'Alerta' não encontrada - será criada")
                    return None
            else:
                logger.error(f"❌ Erro buscando pasta Alerta: HTTP {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Erro descobrindo pasta Alerta: {e}")
            return None
    
    def criar_pasta_alerta(self) -> Optional[str]:
        """
        Criar pasta 'Alerta' na raiz do OneDrive
        
        Returns:
            str: ID da pasta criada ou None se falhar
        """
        try:
            headers = self._obter_headers()
            if not headers:
                return None
            
            # Criar pasta na raiz
            url = f"{self.base_url}/me/drive/root/children"
            
            data = {
                "name": "Alerta",
                "folder": {},
                "@microsoft.graph.conflictBehavior": "fail"
            }
            
            response = requests.post(url, headers=headers, json=data, timeout=30)
            
            if response.status_code == 201:
                pasta_data = response.json()
                pasta_id = pasta_data['id']
                logger.info(f"✅ Pasta 'Alerta' criada: {pasta_id}")
                return pasta_id
            elif response.status_code == 409:
                # Pasta já existe
                logger.info("📁 Pasta 'Alerta' já existe")
                return self.descobrir_pasta_alerta_id()
            else:
                logger.error(f"❌ Erro criando pasta Alerta: HTTP {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Erro criando pasta Alerta: {e}")
            return None
    
    def criar_estrutura_completa(self) -> bool:
        """
        Criar estrutura completa no OneDrive
        
        Returns:
            bool: True se estrutura criada com sucesso
        """
        try:
            # Descobrir ou criar pasta principal
            if not self.alerta_folder_id:
                self.alerta_folder_id = self.descobrir_pasta_alerta_id()
            
            if not self.alerta_folder_id:
                self.alerta_folder_id = self.criar_pasta_alerta()
            
            if not self.alerta_folder_id:
                logger.error("❌ Não foi possível criar/encontrar pasta Alerta")
                return False
            
            # Criar subpastas
            subpastas = ["backup", "logs"]
            
            for pasta in subpastas:
                self._criar_subpasta(pasta)
            
            logger.info("✅ Estrutura OneDrive criada com sucesso")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro criando estrutura OneDrive: {e}")
            return False
    
    def _criar_subpasta(self, nome_pasta: str) -> Optional[str]:
        """Criar subpasta dentro da pasta Alerta"""
        try:
            headers = self._obter_headers()
            if not headers or not self.alerta_folder_id:
                return None
            
            url = f"{self.base_url}/me/drive/items/{self.alerta_folder_id}/children"
            
            data = {
                "name": nome_pasta,
                "folder": {},
                "@microsoft.graph.conflictBehavior": "replace"
            }
            
            response = requests.post(url, headers=headers, json=data, timeout=30)
            
            if response.status_code in [201, 200]:
                pasta_data = response.json()
                logger.info(f"✅ Subpasta '{nome_pasta}' criada/atualizada")
                return pasta_data['id']
            else:
                logger.warning(f"⚠️ Problema criando subpasta '{nome_pasta}': HTTP {response.status_code}")
                return None
                
        except Exception as e:
            logger.warning(f"⚠️ Erro criando subpasta '{nome_pasta}': {e}")
            return None
    
    def upload_database(self, local_db_path: str) -> bool:
        """
        Upload do banco SQLite para OneDrive
        
        Args:
            local_db_path (str): Caminho do arquivo local
            
        Returns:
            bool: True se upload bem-sucedido
        """
        try:
            if not os.path.exists(local_db_path):
                logger.error(f"❌ Arquivo local não encontrado: {local_db_path}")
                return False
            
            headers = self._obter_headers()
            if not headers or not self.alerta_folder_id:
                logger.error("❌ Não é possível fazer upload sem autenticação/pasta")
                return False
            
            # Ler arquivo local
            with open(local_db_path, 'rb') as f:
                file_content = f.read()
            
            # URL para upload
            filename = "alertas_bot.db"
            url = f"{self.base_url}/me/drive/items/{self.alerta_folder_id}:/{filename}:/content"
            
            # Headers para upload de arquivo
            upload_headers = {
                'Authorization': headers['Authorization'],
                'Content-Type': 'application/octet-stream'
            }
            
            response = requests.put(url, headers=upload_headers, data=file_content, timeout=60)
            
            if response.status_code in [200, 201]:
                file_data = response.json()
                logger.info(f"✅ Database enviado para OneDrive: {filename}")
                logger.info(f"   Tamanho: {len(file_content)} bytes")
                return True
            else:
                logger.error(f"❌ Erro no upload: HTTP {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Erro fazendo upload do database: {e}")
            return False
    
    def download_database(self, local_db_path: str) -> bool:
        """
        Download do banco SQLite do OneDrive
        
        Args:
            local_db_path (str): Caminho onde salvar o arquivo
            
        Returns:
            bool: True se download bem-sucedido
        """
        try:
            headers = self._obter_headers()
            if not headers or not self.alerta_folder_id:
                logger.error("❌ Não é possível fazer download sem autenticação/pasta")
                return False
            
            # URL para download
            filename = "alertas_bot.db"
            url = f"{self.base_url}/me/drive/items/{self.alerta_folder_id}:/{filename}:/content"
            
            response = requests.get(url, headers=headers, timeout=60)
            
            if response.status_code == 200:
                # Garantir que diretório existe
                os.makedirs(os.path.dirname(local_db_path), exist_ok=True)
                
                # Salvar arquivo
                with open(local_db_path, 'wb') as f:
                    f.write(response.content)
                
                logger.info(f"✅ Database baixado do OneDrive: {filename}")
                logger.info(f"   Tamanho: {len(response.content)} bytes")
                logger.info(f"   Salvo em: {local_db_path}")
                return True
            elif response.status_code == 404:
                logger.info("📁 Arquivo não existe no OneDrive - será criado")
                return False
            else:
                logger.error(f"❌ Erro no download: HTTP {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Erro fazendo download do database: {e}")
            return False
    
    def obter_caminho_database_hibrido(self) -> str:
        """
        Obter caminho do database usando estratégia híbrida
        
        1. Tenta baixar do OneDrive para cache local
        2. Se falhar, usa arquivo local
        3. Sempre retorna caminho local para uso
        
        Returns:
            str: Caminho do arquivo local para uso
        """
        try:
            # Garantir estrutura OneDrive
            if not self.alerta_folder_id:
                self.criar_estrutura_completa()
            
            # Tentar download do OneDrive
            cache_path = os.path.join(self.local_storage_path, "alertas_bot_cache.db")
            
            if self.download_database(cache_path):
                logger.info("✅ Database sincronizado do OneDrive")
                return cache_path
            else:
                logger.info("📁 Usando arquivo local (OneDrive indisponível)")
                return self.local_db_path
                
        except Exception as e:
            logger.error(f"❌ Erro obtendo caminho híbrido: {e}")
            return self.local_db_path
    
    def sincronizar_para_onedrive(self, local_db_path: str) -> bool:
        """
        Sincronizar arquivo local para OneDrive (após modificações)
        
        Args:
            local_db_path (str): Caminho do arquivo local modificado
            
        Returns:
            bool: True se sincronização bem-sucedida
        """
        try:
            # Garantir estrutura OneDrive
            if not self.alerta_folder_id:
                if not self.criar_estrutura_completa():
                    logger.warning("⚠️ Não foi possível sincronizar - OneDrive indisponível")
                    return False
            
            # Fazer upload
            if self.upload_database(local_db_path):
                logger.info("✅ Database sincronizado para OneDrive")
                return True
            else:
                logger.warning("⚠️ Falha na sincronização para OneDrive")
                return False
                
        except Exception as e:
            logger.error(f"❌ Erro sincronizando para OneDrive: {e}")
            return False
    
    def status_onedrive(self) -> Dict:
        """
        Obter status da configuração OneDrive
        
        Returns:
            Dict: Informações sobre status OneDrive
        """
        return {
            "pasta_alerta_configurada": bool(self.alerta_folder_id),
            "pasta_alerta_id": self.alerta_folder_id,
            "auth_disponivel": bool(self.auth.access_token),
            "local_storage_path": self.local_storage_path,
            "local_db_exists": os.path.exists(self.local_db_path)
        }
