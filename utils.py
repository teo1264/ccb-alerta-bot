#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Funções utilitárias para o CCB Alerta Bot
"""

import os
import pandas as pd
import re
from datetime import datetime
import pytz
import shutil
from config import EXCEL_FILE, ADMIN_IDS

def verificar_admin(user_id):
    """
    Verifica se o usuário é um administrador
    
    Args:
        user_id (int): ID do usuário
        
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
        tuple: (sucesso, status)
    """
    try:
        global ADMIN_IDS
        
        # Verificar se já é administrador
        if novo_admin_id in ADMIN_IDS:
            return False, "já é admin"
        
        # Adicionar à lista global
        ADMIN_IDS.append(novo_admin_id)
        
        # Salvar no arquivo para persistência
        with open('admin_ids.txt', 'w') as f:
            for admin_id in ADMIN_IDS:
                f.write(f"{admin_id}\n")
        
        return True, "sucesso"
    except Exception as e:
        return False, str(e)

def verificar_formato_cadastro(texto):
    """
    Verifica se o texto está no formato esperado para cadastro
    
    Args:
        texto (str): Texto a ser verificado
        
    Returns:
        bool: True se estiver no formato correto, False caso contrário
    """
    # Padrão esperado: BR21-0000 / Nome / Função
    padrao = r'^(BR\d{2}-\d{4})\s*\/\s*(.+?)\s*\/\s*(.+)$'
    return bool(re.match(padrao, texto, re.IGNORECASE))

def extrair_dados_cadastro(texto):
    """
    Extrai os dados de cadastro do texto
    
    Args:
        texto (str): Texto no formato de cadastro
        
    Returns:
        tuple: (codigo, nome, funcao) ou (None, None, None) se inválido
    """
    if not verificar_formato_cadastro(texto):
        return None, None, None
    
    # Extrair dados pelo delimitador "/"
    partes = [p.strip() for p in texto.split('/')]
    
    # Garantir que temos pelo menos 3 partes (código, nome, função)
    if len(partes) >= 3:
        codigo_casa = partes[0].strip()
        nome = partes[1].strip()
        funcao = partes[2].strip()
        return codigo_casa, nome, funcao
    
    return None, None, None

def fazer_backup_planilha():
    """
    Cria um backup da planilha atual
    
    Returns:
        str: Nome do arquivo de backup
    """
    try:
        if not os.path.exists(EXCEL_FILE):
            return None
            
        # Criar nome para backup
        fuso_horario = pytz.timezone('America/Sao_Paulo')
        agora = datetime.now(fuso_horario)
        timestamp = agora.strftime("%Y%m%d%H%M%S")
        backup_file = f"backup_{timestamp}_{EXCEL_FILE}"
        
        # Criar cópia física do arquivo
        shutil.copy2(EXCEL_FILE, backup_file)
        
        return backup_file
    except Exception as e:
        print(f"Erro ao fazer backup: {e}")
        return None

def verificar_cadastro_existente(codigo, nome, funcao):
    """
    Verifica se já existe um cadastro com os mesmos dados
    
    Args:
        codigo (str): Código da casa
        nome (str): Nome do responsável
        funcao (str): Função do responsável
        
    Returns:
        bool: True se existir, False caso contrário
    """
    try:
        if not os.path.exists(EXCEL_FILE):
            return False
            
        df = pd.read_excel(EXCEL_FILE)
        
        if df.empty:
            return False
        
        # Normalizar para comparação (remover espaços extras e converter para maiúsculas)
        codigo_norm = codigo.strip().upper()
        nome_norm = nome.strip().upper()
        funcao_norm = funcao.strip().upper()
        
        # Verificar se existe cadastro idêntico
        for _, row in df.iterrows():
            if (str(row['Codigo_Casa']).strip().upper() == codigo_norm and
                str(row['Nome']).strip().upper() == nome_norm and
                str(row['Funcao']).strip().upper() == funcao_norm):
                return True
                
        return False
    except Exception as e:
        print(f"Erro ao verificar cadastro existente: {e}")
        return False

def salvar_cadastro(codigo, nome, funcao, user_id, username):
    """
    Salva os dados do cadastro na planilha Excel
    
    Args:
        codigo (str): Código da casa
        nome (str): Nome do responsável
        funcao (str): Função do responsável
        user_id (int): ID do usuário no Telegram
        username (str): Username do usuário no Telegram
        
    Returns:
        tuple: (sucesso, status)
    """
    try:
        # Verificar se a planilha existe, se não, criar
        if not os.path.exists(EXCEL_FILE):
            df = pd.DataFrame(columns=[
                'Codigo_Casa', 'Nome', 'Funcao', 
                'User_ID', 'Username', 'Data_Cadastro',
                'Ultima_Atualizacao'
            ])
            
            # Criar um writer com engine openpyxl
            writer = pd.ExcelWriter(EXCEL_FILE, engine='openpyxl')
            
            # Escrever o DataFrame para o Excel
            df.to_excel(writer, index=False)
            
            # Obter a planilha ativa
            worksheet = writer.sheets['Sheet1']
            
            # Ajustar largura das colunas
            worksheet.column_dimensions['A'].width = 15  # Codigo_Casa
            worksheet.column_dimensions['B'].width = 30  # Nome
            worksheet.column_dimensions['C'].width = 20  # Funcao
            worksheet.column_dimensions['D'].width = 15  # User_ID
            worksheet.column_dimensions['E'].width = 20  # Username
            worksheet.column_dimensions['F'].width = 20  # Data_Cadastro
            worksheet.column_dimensions['G'].width = 20  # Ultima_Atualizacao
            
            # Salvar o arquivo
            writer.close()
            print(f"Planilha {EXCEL_FILE} criada com sucesso")
        
        # Verificar duplicata antes de salvar
        if verificar_cadastro_existente(codigo, nome, funcao):
            print(f"Tentativa de cadastro duplicado: {codigo}, {nome}, {funcao}")
            return False, "duplicado"
        
        # Data atual em formato brasileiro
        fuso_horario = pytz.timezone('America/Sao_Paulo')
        agora = datetime.now(fuso_horario)
        data_formatada = agora.strftime("%d/%m/%Y %H:%M:%S")
        
        # Criar DataFrame com os dados
        novo_registro = pd.DataFrame({
            'Codigo_Casa': [codigo],
            'Nome': [nome],
            'Funcao': [funcao],
            'User_ID': [user_id],
            'Username': [username],
            'Data_Cadastro': [data_formatada],
            'Ultima_Atualizacao': [data_formatada]
        })
        
        # Ler a planilha existente
        df_existente = pd.read_excel(EXCEL_FILE)
        
        # Concatenar com novo registro
        df_atualizado = pd.concat([df_existente, novo_registro], ignore_index=True)
        
        # Salvar com formatação de colunas
        with pd.ExcelWriter(EXCEL_FILE, engine='openpyxl') as writer:
            df_atualizado.to_excel(writer, index=False)
            
            # Obter a planilha ativa
            worksheet = writer.sheets['Sheet1']
            
            # Ajustar largura das colunas
            worksheet.column_dimensions['A'].width = 15  # Codigo_Casa
            worksheet.column_dimensions['B'].width = 30  # Nome
            worksheet.column_dimensions['C'].width = 20  # Funcao
            worksheet.column_dimensions['D'].width = 15  # User_ID
            worksheet.column_dimensions['E'].width = 20  # Username
            worksheet.column_dimensions['F'].width = 20  # Data_Cadastro
            worksheet.column_dimensions['G'].width = 20  # Ultima_Atualizacao
        
        print(f"Cadastro salvo com sucesso: {codigo}, {nome}, {funcao}")
        return True, "sucesso"
    except Exception as e:
        print(f"Erro ao salvar cadastro: {e}")
        return False, str(e)
