#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Funções utilitárias para o CCB Alerta Bot
"""

import os
import re
import pandas as pd
from datetime import datetime
import pytz
from config import EXCEL_FILE, ADMIN_IDS

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
        print(f"Erro ao verificar duplicata: {e}")
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
        bool: True se o cadastro foi salvo com sucesso, False caso contrário
    """
    try:
        # Verificar duplicata antes de salvar
        if verificar_duplicata(codigo):
            print(f"Tentativa de cadastro duplicado: {codigo}")
            return False, "duplicado"
        
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
        
        # Ler a planilha existente (se não existir, inicializar_planilha() já terá criado)
        df_existente = pd.read_excel(EXCEL_FILE)
        
        # Adicionar nova linha
        df_atualizado = pd.concat([df_existente, df_novo], ignore_index=True)
        
        # Criar um writer com engine openpyxl
        writer = pd.ExcelWriter(EXCEL_FILE, engine='openpyxl')
        
        # Escrever o DataFrame atualizado
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
        
        # Salvar o arquivo
        writer.close()
            
        print(f"Cadastro salvo com sucesso: {codigo} / {nome} / {funcao}")
        return True, "sucesso"
    except Exception as e:
        print(f"Erro ao salvar cadastro: {e}")
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
        print(f"Erro ao extrair dados de cadastro: {e}")
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
        print(f"Erro ao adicionar administrador: {e}")
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
        
        print(f"Backup criado: {backup_file}")
        return backup_file
    except Exception as e:
        print(f"Erro ao fazer backup: {e}")
        return None