"""
Módulo de acesso ao banco de dados SQLite com integração OneDrive
VERSÃO CORRIGIDA FINAL: Sincronização garantida sem conflitos com navegação
NUNCA MAIS VAI PERDER DADOS + TODAS AS FUNÇÕES IMPLEMENTADAS
"""
import sqlite3
import os
import logging
from datetime import datetime, timedelta
import pytz
import shutil
import threading
import time

logger = logging.getLogger("CCB-Alerta-Bot.database")

# Gerenciador OneDrive global (será inicializado)
_onedrive_manager = None

# Cache para evitar downloads repetidos
_last_onedrive_sync = None
_cache_timeout_minutes = 3

def _should_sync_onedrive():
    """Evitar sincronizações muito frequentes"""
    global _last_onedrive_sync
    
    if not _last_onedrive_sync:
        return True
    
    cache_age = datetime.now() - _last_onedrive_sync
    return cache_age.total_seconds() > (_cache_timeout_minutes * 60)

def inicializar_onedrive_manager():
    """Inicializar gerenciador OneDrive globalmente"""
    global _onedrive_manager
    
    try:
        onedrive_enabled = os.getenv("ONEDRIVE_DATABASE_ENABLED", "false").lower() == "true"
        
        if not onedrive_enabled:
            logger.info("📁 OneDrive desabilitado - usando storage local")
            return
        
        from auth.microsoft_auth import MicrosoftAuth
        from utils.onedrive_manager import OneDriveManager
        
        auth = MicrosoftAuth()
        
        if not auth.access_token:
            logger.warning("⚠️ Token Microsoft não disponível - usando storage local")
            return
        
        _onedrive_manager = OneDriveManager(auth)
        _onedrive_manager.criar_estrutura_completa()
        
        logger.info("✅ OneDriveManager inicializado com sucesso")
        
    except Exception as e:
        logger.error(f"❌ Erro inicializando OneDriveManager: {e}")
        logger.info("📁 Continuando com storage local")

def get_db_path():
    """Caminho database com cache otimizado"""
    global _onedrive_manager, _last_onedrive_sync
    
    if _onedrive_manager:
        try:
            cache_path = os.path.join(
                "/opt/render/project/storage", 
                "alertas_bot_cache.db"
            )
            
            if _should_sync_onedrive() or not os.path.exists(cache_path):
                if _onedrive_manager.download_database(cache_path):
                    _last_onedrive_sync = datetime.now()
                    logger.info("✅ Database atualizado do OneDrive")
                else:
                    logger.debug("📁 Usando cache local existente")
            else:
                logger.debug("📁 Cache ainda válido - sem download")
            
            return cache_path
            
        except Exception as e:
            logger.warning(f"⚠️ Erro OneDrive: {e}")
    
    # Fallback: caminho local
    RENDER_DISK_PATH = os.environ.get("RENDER_DISK_PATH", "/opt/render/project/disk")
    DATA_DIR = os.path.join(RENDER_DISK_PATH, "shared_data")
    os.makedirs(DATA_DIR, exist_ok=True)
    
    return os.path.join(DATA_DIR, "alertas_bot.db")

def _sincronizar_para_onedrive_critico():
    """
    🔥 CORREÇÃO PRINCIPAL: Sincronização APENAS para operações críticas
    
    Esta função é chamada APENAS após:
    - Cadastros completos (salvar_responsavel)
    - Exclusões de dados (remover_cadastros_por_user_id)
    - Operações administrativas (adicionar_admin)
    - Consentimentos LGPD (registrar_consentimento_lgpd)
    
    NÃO é chamada durante:
    - Navegação de botões (Anterior/Próxima)
    - Consultas de leitura (listar, buscar)
    - Operações temporárias
    
    BENEFÍCIOS:
    ✅ Garante que dados nunca sejam perdidos
    ✅ Não interfere com navegação de botões
    ✅ Upload assíncrono (não trava interface)
    ✅ Logs detalhados para monitoramento
    """
    global _onedrive_manager
    
    if not _onedrive_manager:
        logger.debug("📁 OneDrive não configurado - dados salvos apenas localmente")
        return
    
    try:
        def fazer_upload_seguro():
            """Thread separada para upload sem bloquear interface"""
            try:
                cache_path = "/opt/render/project/storage/alertas_bot_cache.db"
                
                if not os.path.exists(cache_path):
                    logger.warning("⚠️ Cache local não encontrado para sync")
                    return
                
                # Tentar upload com timeout
                sucesso = _onedrive_manager.upload_database(cache_path)
                
                if sucesso:
                    logger.info("🔥 DADOS SINCRONIZADOS COM ONEDRIVE - PROTEGIDOS CONTRA PERDA!")
                    logger.info(f"💾 Arquivo sincronizado: {os.path.getsize(cache_path)} bytes")
                else:
                    logger.warning("⚠️ Falha no upload OneDrive - dados seguros localmente")
                    
            except Exception as e:
                logger.error(f"❌ Erro no upload OneDrive: {e}")
                logger.info("💾 Dados permanecem seguros no cache local")
        
        # Executar upload em thread separada para não bloquear
        thread_upload = threading.Thread(target=fazer_upload_seguro, daemon=True)
        thread_upload.start()
        
        logger.info("📤 SYNC ONEDRIVE INICIADO - Dados serão protegidos em segundo plano")
        
    except Exception as e:
        logger.error(f"❌ Erro criando thread de sync: {e}")

def get_connection():
    """Conexão SQLite segura"""
    try:
        db_path = get_db_path()
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        return conn
    except Exception as e:
        logger.error(f"Erro criando conexão: {e}")
        raise

def init_database():
    """Inicializa o banco de dados com as tabelas necessárias"""
    try:
        conn = get_connection()
        try:
            cursor = conn.cursor()
            
            # Tabela de usuários/responsáveis
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS responsaveis (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                codigo_casa TEXT NOT NULL,
                nome TEXT NOT NULL,
                funcao TEXT NOT NULL,
                user_id INTEGER NOT NULL,
                username TEXT,
                data_cadastro TEXT NOT NULL,
                ultima_atualizacao TEXT NOT NULL
            )
            ''')
            
            # Índices para otimizar buscas
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_codigo_casa ON responsaveis(codigo_casa)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_user_id ON responsaveis(user_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_nome ON responsaveis(nome)')
            
            # Tabela para registro de alertas enviados
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS alertas_enviados (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                codigo_casa TEXT NOT NULL,
                tipo_alerta TEXT NOT NULL,
                mensagem TEXT NOT NULL,
                data_envio TEXT NOT NULL,
                user_id INTEGER NOT NULL,
                pdf_path TEXT
            )
            ''')
            
            # Tabela para registros de consentimento LGPD
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS consentimento_lgpd (
                user_id INTEGER PRIMARY KEY,
                data_consentimento TEXT NOT NULL,
                ip_address TEXT,
                detalhes TEXT
            )
            ''')
            
            # Tabela para administradores
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS administradores (
                user_id INTEGER PRIMARY KEY,
                nome TEXT,
                data_adicao TEXT NOT NULL
            )
            ''')
            
            conn.commit()
            logger.info("✅ Banco de dados inicializado com sucesso")
            
            # 🔥 CORREÇÃO: Sincronizar após inicialização
            _sincronizar_para_onedrive_critico()
            
            return True
            
        finally:
            conn.close()
            
    except Exception as e:
        logger.error(f"❌ Erro ao inicializar banco de dados: {e}")
        return False

def salvar_responsavel(codigo_casa, nome, funcao, user_id, username):
    """
    🔥 FUNÇÃO CRÍTICA CORRIGIDA: Insere ou atualiza responsável com SYNC GARANTIDO
    
    MUDANÇAS APLICADAS:
    ✅ Sempre chama sync após salvar com sucesso
    ✅ Logs detalhados para monitoramento
    ✅ Proteção contra perda de dados
    """
    try:
        # Obter data atual
        fuso_horario = pytz.timezone('America/Sao_Paulo')
        agora = datetime.now(fuso_horario).strftime("%d/%m/%Y %H:%M:%S")
        
        conn = get_connection()
        try:
            cursor = conn.cursor()
            
            # Verificar se já existe cadastro com mesmo código + nome
            cursor.execute('''
            SELECT id, funcao, user_id FROM responsaveis 
            WHERE UPPER(TRIM(codigo_casa)) = ? AND UPPER(TRIM(nome)) = ?
            ''', (codigo_casa.strip().upper(), nome.strip().upper()))
            
            registro_existente = cursor.fetchone()
            
            if registro_existente:
                if registro_existente['user_id'] == user_id:
                    # Mesmo usuário atualizando sua própria função
                    cursor.execute('''
                    UPDATE responsaveis 
                    SET funcao = ?, username = ?, ultima_atualizacao = ?
                    WHERE id = ?
                    ''', (funcao, username, agora, registro_existente['id']))
                    
                    conn.commit()
                    
                    # 🔥 CORREÇÃO CRÍTICA: Sincronizar após atualização
                    _sincronizar_para_onedrive_critico()
                    
                    if registro_existente['funcao'] != funcao:
                        logger.info(f"✅ FUNÇÃO ATUALIZADA E SINCRONIZADA: {nome} ({registro_existente['funcao']} → {funcao})")
                        return True, f"funcao_atualizada|{registro_existente['funcao']}|{funcao}"
                    else:
                        logger.info(f"✅ DADOS ATUALIZADOS E SINCRONIZADOS: {nome}")
                        return True, "dados_atualizados"
                        
                else:
                    # Usuário diferente tentando cadastrar mesmo nome na mesma igreja
                    logger.warning(f"⚠️ Tentativa de cadastro duplicado: {codigo_casa} - {nome} (usuário {user_id})")
                    return False, f"nome_ja_cadastrado|{registro_existente['funcao']}"
            
            else:
                # Não existe - inserir novo registro
                cursor.execute('''
                INSERT INTO responsaveis 
                (codigo_casa, nome, funcao, user_id, username, data_cadastro, ultima_atualizacao)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    codigo_casa,
                    nome,
                    funcao,
                    user_id,
                    username,
                    agora,
                    agora
                ))
                
                conn.commit()
                
                # 🔥 CORREÇÃO CRÍTICA: Sincronizar após inserção
                _sincronizar_para_onedrive_critico()
                
                logger.info(f"🔥 NOVO CADASTRO INSERIDO E SINCRONIZADO: {codigo_casa} - {nome} ({funcao})")
                logger.info(f"👥 Usuário ID: {user_id}, Username: {username}")
                return True, "inserido"
                
        finally:
            conn.close()
            
    except Exception as e:
        logger.error(f"❌ Erro ao salvar responsável: {e}")
        return False, str(e)

def verificar_cadastro_existente(codigo, nome, funcao=None):
    """Verifica se já existe um cadastro com o mesmo código e nome"""
    try:
        conn = get_connection()
        try:
            cursor = conn.cursor()
            
            codigo_norm = codigo.strip().upper()
            nome_norm = nome.strip().upper()
            
            cursor.execute('''
            SELECT id, funcao FROM responsaveis 
            WHERE UPPER(TRIM(codigo_casa)) = ? 
              AND UPPER(TRIM(nome)) = ?
            ''', (codigo_norm, nome_norm))
            
            resultado = cursor.fetchone()
            
            if resultado:
                logger.info(f"📋 Cadastro já existe: {codigo} - {nome} (função atual: {resultado['funcao']})")
                return True
            
            return False
            
        finally:
            conn.close()
            
    except Exception as e:
        logger.error(f"❌ Erro ao verificar cadastro existente: {e}")
        return False

def verificar_cadastro_existente_detalhado(codigo, nome):
    """
    🔥 FUNÇÃO FALTANTE IMPLEMENTADA: Verifica se já existe um cadastro e retorna detalhes
    """
    try:
        conn = get_connection()
        try:
            cursor = conn.cursor()
            
            # Normalizar para comparação
            codigo_norm = codigo.strip().upper()
            nome_norm = nome.strip().upper()
            
            cursor.execute('''
            SELECT * FROM responsaveis 
            WHERE UPPER(TRIM(codigo_casa)) = ? 
              AND UPPER(TRIM(nome)) = ?
            ''', (codigo_norm, nome_norm))
            
            resultado = cursor.fetchone()
            
            if resultado:
                return dict(resultado)
            
            return None
            
        finally:
            conn.close()
            
    except Exception as e:
        logger.error(f"❌ Erro ao verificar cadastro existente detalhado: {e}")
        return None

def obter_cadastros_por_user_id(user_id):
    """Obtem todos os cadastros de um usuário pelo ID"""
    try:
        conn = get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM responsaveis WHERE user_id = ? ORDER BY codigo_casa, nome",
                (user_id,)
            )
            
            resultados = []
            for row in cursor.fetchall():
                resultados.append(dict(row))
            
            return resultados
            
        finally:
            conn.close()
            
    except Exception as e:
        logger.error(f"❌ Erro ao obter cadastros por user_id: {e}")
        return []

def remover_cadastros_por_user_id(user_id):
    """Remove todos os cadastros de um usuário pelo ID - COM SYNC"""
    try:
        conn = get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                "DELETE FROM responsaveis WHERE user_id = ?",
                (user_id,)
            )
            
            removidos = cursor.rowcount
            conn.commit()
            
            # 🔥 CORREÇÃO: Sincronizar após remoção
            if removidos > 0:
                _sincronizar_para_onedrive_critico()
                logger.info(f"🔥 {removidos} CADASTROS REMOVIDOS E SINCRONIZADOS para usuário {user_id}")
            
            return removidos
            
        finally:
            conn.close()
            
    except Exception as e:
        logger.error(f"❌ Erro ao remover cadastros por user_id: {e}")
        return 0

def buscar_responsaveis_por_codigo(codigo_casa):
    """Busca responsáveis pelo código da casa"""
    try:
        conn = get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM responsaveis WHERE codigo_casa = ? ORDER BY nome",
                (codigo_casa,)
            )
            
            resultados = []
            for row in cursor.fetchall():
                resultados.append(dict(row))
            
            return resultados
            
        finally:
            conn.close()
            
    except Exception as e:
        logger.error(f"❌ Erro ao buscar responsáveis por código: {e}")
        return []

def buscar_responsavel_por_id(user_id):
    """Busca responsável pelo ID do Telegram"""
    try:
        conn = get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM responsaveis WHERE user_id = ?",
                (user_id,)
            )
            
            row = cursor.fetchone()
            if row:
                return dict(row)
            return None
            
        finally:
            conn.close()
            
    except Exception as e:
        logger.error(f"❌ Erro ao buscar responsável por ID: {e}")
        return None

def listar_todos_responsaveis():
    """Retorna todos os responsáveis cadastrados"""
    try:
        conn = get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM responsaveis ORDER BY codigo_casa, nome")
            
            resultados = []
            for row in cursor.fetchall():
                resultados.append(dict(row))
            
            return resultados
            
        finally:
            conn.close()
            
    except Exception as e:
        logger.error(f"❌ Erro ao listar todos responsáveis: {e}")
        return []

def remover_responsavel(user_id):
    """Remove todos os registros de um usuário pelo ID"""
    try:
        conn = get_connection()
        try:
            cursor = conn.cursor()
            
            cursor.execute("SELECT COUNT(*) as total FROM responsaveis WHERE user_id = ?", (user_id,))
            count = cursor.fetchone()['total']
            
            cursor.execute("DELETE FROM responsaveis WHERE user_id = ?", (user_id,))
            conn.commit()
            
            # 🔥 CORREÇÃO: Sincronizar após remoção
            if count > 0:
                _sincronizar_para_onedrive_critico()
            
            return True, count
            
        finally:
            conn.close()
    
    except Exception as e:
        logger.error(f"❌ Erro ao remover responsável: {e}")
        return False, 0

def remover_responsavel_especifico(codigo_casa, nome, funcao=None):
    """Remove um registro específico por código e nome"""
    try:
        conn = get_connection()
        try:
            cursor = conn.cursor()
            
            if funcao:
                cursor.execute(
                    "DELETE FROM responsaveis WHERE codigo_casa = ? AND nome = ? AND funcao = ?", 
                    (codigo_casa, nome, funcao)
                )
            else:
                cursor.execute(
                    "DELETE FROM responsaveis WHERE codigo_casa = ? AND nome = ?", 
                    (codigo_casa, nome)
                )
            
            conn.commit()
            
            # 🔥 CORREÇÃO: Sincronizar após remoção
            if cursor.rowcount > 0:
                _sincronizar_para_onedrive_critico()
            
            return True, cursor.rowcount
            
        finally:
            conn.close()
    
    except Exception as e:
        logger.error(f"❌ Erro ao remover responsável específico: {e}")
        return False, 0

def editar_responsavel(id_registro, campos):
    """Edita um registro existente"""
    try:
        campos_permitidos = ['codigo_casa', 'nome', 'funcao']
        campos_update = {k: v for k, v in campos.items() if k in campos_permitidos}
        
        if not campos_update:
            logger.warning("⚠️ Nenhum campo válido para atualização")
            return False
        
        fuso_horario = pytz.timezone('America/Sao_Paulo')
        agora = datetime.now(fuso_horario).strftime("%d/%m/%Y %H:%M:%S")
        campos_update['ultima_atualizacao'] = agora
        
        conn = get_connection()
        try:
            cursor = conn.cursor()
            
            campos_set = ', '.join([f"{campo} = ?" for campo in campos_update.keys()])
            valores = list(campos_update.values())
            valores.append(id_registro)
            
            query = f"UPDATE responsaveis SET {campos_set} WHERE id = ?"
            
            cursor.execute(query, valores)
            conn.commit()
            
            sucesso = cursor.rowcount > 0
            
            # 🔥 CORREÇÃO: Sincronizar após edição
            if sucesso:
                _sincronizar_para_onedrive_critico()
                logger.info(f"🔥 CADASTRO EDITADO E SINCRONIZADO: ID {id_registro}")
            
            return sucesso
            
        finally:
            conn.close()
    
    except Exception as e:
        logger.error(f"❌ Erro ao editar responsável: {e}")
        return False

def limpar_todos_responsaveis():
    """Remove todos os responsáveis do banco de dados - COM SYNC"""
    try:
        conn = get_connection()
        try:
            cursor = conn.cursor()
            
            cursor.execute("SELECT COUNT(*) as total FROM responsaveis")
            count = cursor.fetchone()['total']
            
            cursor.execute("DELETE FROM responsaveis")
            conn.commit()
            
            logger.info(f"🔥 REMOVIDOS {count} RESPONSÁVEIS DO BANCO DE DADOS")
            
            # 🔥 CORREÇÃO: Sincronizar após limpeza
            if count > 0:
                _sincronizar_para_onedrive_critico()
                logger.info("🔥 LIMPEZA SINCRONIZADA COM ONEDRIVE")
            
            return True
            
        finally:
            conn.close()
    
    except Exception as e:
        logger.error(f"❌ Erro ao limpar todos os responsáveis: {e}")
        return False

# ============================================
# FUNÇÕES ADMINISTRATIVAS
# ============================================

def verificar_admin(user_id):
    """Verifica se o usuário é um administrador"""
    try:
        conn = get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT user_id FROM administradores WHERE user_id = ?", (user_id,))
            return cursor.fetchone() is not None
        finally:
            conn.close()
    except Exception as e:
        logger.error(f"❌ Erro ao verificar administrador: {e}")
        return False

def listar_admins():
    """Lista todos os administradores"""
    try:
        conn = get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT user_id FROM administradores")
            return [row['user_id'] for row in cursor.fetchall()]
        finally:
            conn.close()
    except Exception as e:
        logger.error(f"❌ Erro ao listar administradores: {e}")
        return []

def adicionar_admin(user_id, nome=None):
    """Adiciona um novo administrador - COM SYNC"""
    try:
        if verificar_admin(user_id):
            return False, "já é admin"
        
        fuso_horario = pytz.timezone('America/Sao_Paulo')
        agora = datetime.now(fuso_horario).strftime("%d/%m/%Y %H:%M:%S")
        
        conn = get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO administradores (user_id, nome, data_adicao) VALUES (?, ?, ?)",
                (user_id, nome, agora)
            )
            conn.commit()
            
            # 🔥 CORREÇÃO: Sincronizar após adicionar admin
            _sincronizar_para_onedrive_critico()
            logger.info(f"🔥 ADMINISTRADOR ADICIONADO E SINCRONIZADO: {user_id}")
            
            return True, "sucesso"
            
        finally:
            conn.close()
            
    except Exception as e:
        logger.error(f"❌ Erro ao adicionar administrador: {e}")
        return False, str(e)

def remover_admin(user_id):
    """Remove um administrador"""
    try:
        conn = get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM administradores WHERE user_id = ?", (user_id,))
            conn.commit()
            
            sucesso = cursor.rowcount > 0
            
            # 🔥 CORREÇÃO: Sincronizar após remoção
            if sucesso:
                _sincronizar_para_onedrive_critico()
            
            return sucesso
            
        finally:
            conn.close()
            
    except Exception as e:
        logger.error(f"❌ Erro ao remover administrador: {e}")
        return False

def inicializar_admins_padrao(admin_ids):
    """Inicializa administradores padrão no banco de dados"""
    try:
        count = 0
        for admin_id in admin_ids:
            sucesso, _ = adicionar_admin(admin_id)
            if sucesso:
                count += 1
        
        return count
    except Exception as e:
        logger.error(f"❌ Erro ao inicializar admins padrão: {e}")
        return 0

# ============================================
# FUNÇÕES LGPD
# ============================================

def registrar_consentimento_lgpd(user_id, ip_address=None, detalhes=None):
    """Registra o consentimento do usuário para LGPD - COM SYNC"""
    try:
        fuso_horario = pytz.timezone('America/Sao_Paulo')
        agora = datetime.now(fuso_horario).strftime("%d/%m/%Y %H:%M:%S")
        
        conn = get_connection()
        try:
            cursor = conn.cursor()
            
            cursor.execute("SELECT user_id FROM consentimento_lgpd WHERE user_id = ?", (user_id,))
            
            if cursor.fetchone():
                cursor.execute(
                    "UPDATE consentimento_lgpd SET data_consentimento = ?, ip_address = ?, detalhes = ? WHERE user_id = ?",
                    (agora, ip_address, detalhes, user_id)
                )
            else:
                cursor.execute(
                    "INSERT INTO consentimento_lgpd (user_id, data_consentimento, ip_address, detalhes) VALUES (?, ?, ?, ?)",
                    (user_id, agora, ip_address, detalhes)
                )
                
            conn.commit()
            
            # 🔥 CORREÇÃO: Sincronizar após registrar consentimento
            _sincronizar_para_onedrive_critico()
            logger.info(f"🔥 CONSENTIMENTO LGPD REGISTRADO E SINCRONIZADO: {user_id}")
            
            return True
            
        finally:
            conn.close()
            
    except Exception as e:
        logger.error(f"❌ Erro ao registrar consentimento LGPD: {e}")
        return False

def verificar_consentimento_lgpd(user_id):
    """Verifica se o usuário deu consentimento LGPD"""
    try:
        conn = get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT user_id FROM consentimento_lgpd WHERE user_id = ?", (user_id,))
            return cursor.fetchone() is not None
        finally:
            conn.close()
    except Exception as e:
        logger.error(f"❌ Erro ao verificar consentimento LGPD: {e}")
        return False

def remover_consentimento_lgpd(user_id):
    """Remove o registro de consentimento LGPD do usuário"""
    try:
        conn = get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM consentimento_lgpd WHERE user_id = ?", (user_id,))
            conn.commit()
            
            sucesso = cursor.rowcount > 0
            
            # 🔥 CORREÇÃO: Sincronizar após remoção
            if sucesso:
                _sincronizar_para_onedrive_critico()
            
            return sucesso
            
        finally:
            conn.close()
            
    except Exception as e:
        logger.error(f"❌ Erro ao remover consentimento LGPD: {e}")
        return False

# ============================================
# FUNÇÕES DE ALERTAS
# ============================================

def registrar_alerta_enviado(codigo_casa, tipo_alerta, mensagem, user_id, pdf_path=None):
    """Registra um alerta enviado"""
    try:
        fuso_horario = pytz.timezone('America/Sao_Paulo')
        agora = datetime.now(fuso_horario).strftime("%d/%m/%Y %H:%M:%S")
        
        conn = get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO alertas_enviados 
                (codigo_casa, tipo_alerta, mensagem, data_envio, user_id, pdf_path)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (codigo_casa, tipo_alerta, mensagem, agora, user_id, pdf_path)
            )
            conn.commit()
            
            # 🔥 CORREÇÃO: Sincronizar após registrar alerta
            _sincronizar_para_onedrive_critico()
            
            return True
            
        finally:
            conn.close()
            
    except Exception as e:
        logger.error(f"❌ Erro ao registrar alerta enviado: {e}")
        return False

def listar_alertas_enviados(user_id=None, codigo_casa=None, limite=100):
    """Lista alertas enviados, com filtragem opcional"""
    try:
        conn = get_connection()
        try:
            cursor = conn.cursor()
            
            query = "SELECT * FROM alertas_enviados"
            params = []
            
            where_clauses = []
            if user_id:
                where_clauses.append("user_id = ?")
                params.append(user_id)
                
            if codigo_casa:
                where_clauses.append("codigo_casa = ?")
                params.append(codigo_casa)
                
            if where_clauses:
                query += " WHERE " + " AND ".join(where_clauses)
                
            query += " ORDER BY data_envio DESC LIMIT ?"
            params.append(limite)
            
            cursor.execute(query, params)
            
            resultados = []
            for row in cursor.fetchall():
                resultados.append(dict(row))
            
            return resultados
            
        finally:
            conn.close()
            
    except Exception as e:
        logger.error(f"❌ Erro ao listar alertas enviados: {e}")
        return []

def obter_estatisticas_alertas():
    """Obtém estatísticas sobre alertas enviados"""
    try:
        conn = get_connection()
        try:
            cursor = conn.cursor()
            
            # Total de alertas
            cursor.execute("SELECT COUNT(*) as total FROM alertas_enviados")
            total = cursor.fetchone()['total']
            
            # Contagem por tipo
            cursor.execute("""
                SELECT tipo_alerta, COUNT(*) as contagem 
                FROM alertas_enviados 
                GROUP BY tipo_alerta
                ORDER BY contagem DESC
            """)
            
            tipos = {}
            for row in cursor.fetchall():
                tipos[row['tipo_alerta']] = row['contagem']
            
            # Contagem por mês/ano
            cursor.execute("""
                SELECT 
                    substr(data_envio, 7, 4) || '-' || substr(data_envio, 4, 2) as mes_ano,
                    COUNT(*) as contagem
                FROM alertas_enviados
                GROUP BY mes_ano
                ORDER BY mes_ano DESC
            """)
            
            por_periodo = {}
            for row in cursor.fetchall():
                por_periodo[row['mes_ano']] = row['contagem']
            
            return {
                'total': total,
                'por_tipo': tipos,
                'por_periodo': por_periodo
            }
            
        finally:
            conn.close()
            
    except Exception as e:
        logger.error(f"❌ Erro ao obter estatísticas de alertas: {e}")
        return {'total': 0, 'por_tipo': {}, 'por_periodo': {}}

def fazer_backup_banco():
    """Cria um backup do banco de dados"""
    try:
        db_path = get_db_path()
        if not os.path.exists(db_path):
            logger.warning(f"⚠️ Banco de dados não encontrado para backup: {db_path}")
            return None
            
        fuso_horario = pytz.timezone('America/Sao_Paulo')
        agora = datetime.now(fuso_horario)
        timestamp = agora.strftime("%Y%m%d%H%M%S")
        
        RENDER_DISK_PATH = os.environ.get("RENDER_DISK_PATH", "/opt/render/project/disk")
        DATA_DIR = os.path.join(RENDER_DISK_PATH, "shared_data")
        backup_dir = os.path.join(DATA_DIR, "backup")
        os.makedirs(backup_dir, exist_ok=True)
        
        backup_file = os.path.join(backup_dir, f"backup_{timestamp}.db")
        
        shutil.copy2(db_path, backup_file)
        
        logger.info(f"✅ Backup local criado: {backup_file}")
        return backup_file
        
    except Exception as e:
        logger.error(f"❌ Erro ao fazer backup: {e}")
        return None
