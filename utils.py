#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Funções utilitárias para o CCB Alerta Bot
"""

import os
import re
import pandas as pd
import logging
from datetime import datetime
import pytz
from config import EXCEL_FILE, ADMIN_IDS

# Configurar logger
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def verificar_duplicata(codigo):
    """
    Verifica se já existe cadastro com o mesmo código
    
    Args:
        codigo (str): Código da casa a verificar
        
    Returns:
        bool: True se já existe cadastro com este código, False caso contrário
    """
    try:
        if not os.path.exists(EXCEL_FILE):
            return False
            
        df = pd.read_excel(EXCEL_FILE)
        
        # Normaliza código para comparação (remove espaços e converte para maiúsculas)
        codigo_normalizado = codigo.strip().upper()
        
        # Aplica a mesma normalização aos códigos existentes
        df_codigos = df['Codigo_Casa'].astype(str).apply(lambda x: x.strip().upper())
        
        return codigo_normalizado in df_codigos.values
    except Exception as e:
        logger.error(f"Erro ao verificar duplicata: {e}")
        return False

def verificar_formato_cadastro(texto):
    """
    Verifica se o texto está no formato esperado para cadastro
    
    Args:
        texto (str): Texto a ser verificado
        
    Returns:
        bool: True se o formato estiver correto, False caso contrário
    """
    # Padrão esperado: BR21-0000 / Nome / Função
    padrao = r'^(BR\d{2}-\d{4})\s*\/\s*(.+?)\s*\/\s*(.+)$'
    return bool(re.match(padrao, texto, re.IGNORECASE))

def inicializar_planilha():
    """
    Inicializa a planilha de cadastros se não existir
    """
    try:
        if not os.path.exists(EXCEL_FILE):
            # Criar DataFrame vazio com as colunas corretas
            colunas = ['Codigo_Casa', 'Nome', 'Funcao', 'User_ID', 'Username', 'Data_Cadastro', 'Ultima_Atualizacao']
            df = pd.DataFrame(columns=colunas)
            
            # Salvar planilha
            df.to_excel(EXCEL_FILE, index=False)
            logger.info(f"Planilha inicializada: {EXCEL_FILE}")
    except Exception as e:
        logger.error(f"Erro ao inicializar planilha: {e}")

def salvar_cadastro(codigo, nome, funcao, user_id, username):
    """
    Salva os dados do cadastro na planilha Excel
    
    Args:
        codigo (str): Código da casa de oração
        nome (str): Nome do responsável
        funcao (str): Função do responsável
        user_id (int): ID do usuário no Telegram
        username (str): Nome de usuário no Telegram
        
    Returns:
        tuple: (sucesso, status) onde sucesso é um boolean e status é uma mensagem
    """
    try:
        # Inicializar planilha se não existir
        inicializar_planilha()
        
        # Data atual em formato brasileiro
        fuso_horario = pytz.timezone('America/Sao_Paulo')
        agora = datetime.now(fuso_horario)
        data_formatada = agora.strftime("%d/%m/%Y %H:%M:%S")
        
        # Criar DataFrame com os dados
        data = {
            'Codigo_Casa': [codigo],
            'Nome': [nome],
            'Funcao': [funcao],
            'User_ID': [user_id],
            'Username': [username],
            'Data_Cadastro': [data_formatada],
            'Ultima_Atualizacao': [data_formatada]
        }
        df_novo = pd.DataFrame(data)
        
        # Lógica de salvamento melhorada
        df_atualizado = None
        
        if os.path.exists(EXCEL_FILE):
            try:
                df_existente = pd.read_excel(EXCEL_FILE)
                if not df_existente.empty:
                    # Verificar se temos as colunas esperadas no DataFrame existente
                    colunas_esperadas = ['Codigo_Casa', 'Nome', 'Funcao', 'User_ID', 'Username', 'Data_Cadastro', 'Ultima_Atualizacao']
                    colunas_faltantes = [col for col in colunas_esperadas if col not in df_existente.columns]
                    
                    if colunas_faltantes:
                        logger.warning(f"Colunas faltantes na planilha existente: {colunas_faltantes}")
                        # Adicionar colunas faltantes
                        for col in colunas_faltantes:
                            df_existente[col] = ""
                    
                    # Concatenar com o novo cadastro
                    df_atualizado = pd.concat([df_existente, df_novo], ignore_index=True)
                    logger.info(f"Concatenados {len(df_existente)} registros existentes + 1 novo")
                else:
                    df_atualizado = df_novo
                    logger.info("Planilha existente estava vazia, usando apenas o novo cadastro")
            except Exception as e:
                logger.error(f"Erro ao ler planilha existente: {e}")
                # Fazer backup da planilha corrompida
                backup_file = f"corrupted_{EXCEL_FILE}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
                try:
                    import shutil
                    shutil.copy2(EXCEL_FILE, backup_file)
                    logger.info(f"Backup da planilha corrompida criado: {backup_file}")
                except Exception as backup_err:
                    logger.error(f"Erro ao criar backup da planilha corrompida: {backup_err}")
                
                # Usar apenas o novo cadastro
                df_atualizado = df_novo
                logger.info("Usando apenas o novo cadastro devido a erro na leitura da planilha existente")
        else:
            # Se o arquivo não existir, usar apenas o novo DataFrame
            df_atualizado = df_novo
            logger.info("Arquivo não existia, criando novo com o cadastro atual")
        
        # Salvar o DataFrame atualizado
        try:
            # Primeiro tentar salvar com formatação
            from openpyxl import Workbook
            from openpyxl.utils.dataframe import dataframe_to_rows
            
            # Salvar primeiro sem formatação para garantir
            df_atualizado.to_excel(EXCEL_FILE, index=False)
            logger.info(f"Planilha salva sem formatação: {len(df_atualizado)} registros")
            
            # Depois tentar aplicar formatação
            try:
                # Carregar o arquivo recém-salvo
                wb = Workbook()
                ws = wb.active
                
                # Definir cabeçalhos
                headers = list(df_atualizado.columns)
                ws.append(headers)
                
                # Adicionar dados
                for r_idx, row in df_atualizado.iterrows():
                    ws.append([row[col] for col in df_atualizado.columns])
                
                # Ajustar largura das colunas
                ws.column_dimensions['A'].width = 15  # Codigo_Casa
                ws.column_dimensions['B'].width = 30  # Nome
                ws.column_dimensions['C'].width = 20  # Funcao
                ws.column_dimensions['D'].width = 15  # User_ID
                ws.column_dimensions['E'].width = 20  # Username
                ws.column_dimensions['F'].width = 20  # Data_Cadastro
                ws.column_dimensions['G'].width = 20  # Ultima_Atualizacao
                
                # Salvar arquivo formatado
                wb.save(EXCEL_FILE)
                logger.info("Formatação aplicada com sucesso")
            except Exception as format_err:
                logger.warning(f"Erro ao aplicar formatação, mas dados foram salvos: {format_err}")
            
        except Exception as e:
            logger.error(f"Erro ao salvar planilha: {e}")
            return False, f"erro_salvamento: {str(e)}"
        
        # Verificar se o salvamento foi bem-sucedido
        try:
            # Tenta ler o arquivo recém-salvo para confirmar
            verificacao = pd.read_excel(EXCEL_FILE)
            registros_salvos = len(verificacao)
            
            if registros_salvos > 0:
                logger.info(f"Verificação confirmou {registros_salvos} registros salvos")
                return True, "sucesso"
            else:
                logger.error("Verificação encontrou planilha vazia")
                return False, "erro_planilha_vazia"
                
        except Exception as e:
            logger.error(f"Erro ao verificar salvamento: {e}")
            return False, f"erro_verificacao: {str(e)}"
            
    except Exception as e:
        logger.error(f"Erro ao salvar cadastro: {e}")
        return False, str(e)

def extrair_dados_cadastro(texto):
    """
    Extrai código, nome e função de um texto no formato 'BR21-0000 / Nome / Função'
    
    Args:
        texto (str): Texto no formato do cadastro
        
    Returns:
        tuple: (codigo, nome, funcao) ou (None, None, None) em caso de erro
    """
    try:
        if verificar_formato_cadastro(texto):
            # Padrão esperado: BR21-0000 / Nome / Função
            padrao = r'^(BR\d{2}-\d{4})\s*\/\s*(.+?)\s*\/\s*(.+)$'
            match = re.match(padrao, texto, re.IGNORECASE)
            
            if match:
                codigo = match.group(1).strip()
                nome = match.group(2).strip()
                funcao = match.group(3).strip()
                return codigo, nome, funcao
                
        # Se não estiver no formato correto, tenta separar pelo delimitador
        partes = [p.strip() for p in texto.split('/')]
        
        if len(partes) >= 3:
            codigo = partes[0].strip()
            nome = partes[1].strip()
            funcao = partes[2].strip()
            return codigo, nome, funcao
            
        return None, None, None
    except Exception as e:
        logger.error(f"Erro ao extrair dados de cadastro: {e}")
        return None, None, None

def verificar_admin(user_id):
    """
    Verifica se um usuário é administrador
    
    Args:
        user_id (int): ID do usuário a verificar
        
    Returns:
        bool: True se for administrador, False caso contrário
    """
    return user_id in ADMIN_IDS

def adicionar_admin(novo_admin_id):
    """
    Adiciona um novo administrador
    
    Args:
        novo_admin_id (int): ID do novo administrador
        
    Returns:
        bool: True se adicionado com sucesso, False caso contrário
    """
    global ADMIN_IDS
    
    try:
        # Verificar se já é administrador
        if novo_admin_id in ADMIN_IDS:
            return False, "já é admin"
            
        # Cria uma cópia da lista global para modificação
        admin_ids_atualizados = ADMIN_IDS.copy()
        admin_ids_atualizados.append(novo_admin_id)
        
        # Atualiza a lista global
        ADMIN_IDS = admin_ids_atualizados
        
        # Salvar em um arquivo para persistência
        with open('admin_ids.txt', 'w') as f:
            for admin_id in ADMIN_IDS:
                f.write(f"{admin_id}\n")
                
        return True, "sucesso"
    except Exception as e:
        logger.error(f"Erro ao adicionar administrador: {e}")
        return False, str(e)

def obter_data_formatada():
    """
    Retorna a data atual formatada no padrão brasileiro
    
    Returns:
        str: Data formatada (DD/MM/AAAA HH:MM:SS)
    """
    fuso_horario = pytz.timezone('America/Sao_Paulo')
    agora = datetime.now(fuso_horario)
    return agora.strftime("%d/%m/%Y %H:%M:%S")

def fazer_backup_planilha():
    """
    Cria um backup da planilha atual
    
    Returns:
        str: Nome do arquivo de backup ou None em caso de erro
    """
    try:
        if not os.path.exists(EXCEL_FILE):
            return None
            
        # Gerar nome único para o backup
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        backup_file = f"backup_{timestamp}_{EXCEL_FILE}"
        
        # Copiar arquivo para backup
        df = pd.read_excel(EXCEL_FILE)
        df.to_excel(backup_file, index=False)
        
        logger.info(f"Backup criado: {backup_file}")
        return backup_file
    except Exception as e:
        logger.error(f"Erro ao fazer backup: {e}")
        return None

def verificar_cadastro_existente(codigo, nome, funcao=None):
    """
    Verifica se já existe cadastro exatamente igual (mesmo código, nome e função)
    
    Args:
        codigo (str): Código da casa a verificar
        nome (str): Nome do responsável
        funcao (str, optional): Função do responsável
        
    Returns:
        bool: True se já existe cadastro exatamente igual, False caso contrário
    """
    try:
        if not os.path.exists(EXCEL_FILE):
            return False
            
        df = pd.read_excel(EXCEL_FILE)
        
        # Se dataframe estiver vazio, não há duplicatas
        if df.empty:
            return False
            
        # Normaliza dados para comparação
        codigo_normalizado = codigo.strip().upper()
        nome_normalizado = nome.strip().upper()
        
        # Filtra por código
        df_codigos = df['Codigo_Casa'].astype(str).apply(lambda x: x.strip().upper())
        registros_mesmo_codigo = df[df_codigos == codigo_normalizado]
        
        if registros_mesmo_codigo.empty:
            return False
            
        # Normaliza nomes dos cadastros existentes
        nomes_existentes = registros_mesmo_codigo['Nome'].astype(str).apply(lambda x: x.strip().upper())
        
        # Filtra por nome
        registros_mesmo_codigo_nome = registros_mesmo_codigo[nomes_existentes == nome_normalizado]
        
        if registros_mesmo_codigo_nome.empty:
            return False
            
        # Se funcao for None, verificamos apenas código e nome
        if funcao is None:
            return True
            
        # Normaliza função
        funcao_normalizada = funcao.strip().upper()
        funcoes_existentes = registros_mesmo_codigo_nome['Funcao'].astype(str).apply(lambda x: x.strip().upper())
        
        # Verifica se existe o mesmo código, nome e função
        return (funcao_normalizada == funcoes_existentes).any()
        
    except Exception as e:
        logger.error(f"Erro ao verificar cadastro existente: {e}")
        return False
