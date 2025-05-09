#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Configurações globais para o CCB Alerta Bot
"""
import os
import pandas as pd

# Token do Bot (coloque aqui seu token)
TOKEN = "7773179413:AAHqJp-NBPPs6YrSV1kB5-q4vkV3tjDFyy4"

# Arquivo Excel para armazenar os cadastros
EXCEL_FILE = "data/responsaveis_casas.xlsx"

def verificar_diretorios():
    """Garante que os diretórios necessários existam"""
    import os
    # Garantir que o diretório de dados existe
    os.makedirs(os.path.dirname(EXCEL_FILE), exist_ok=True)

# IDs de administradores (lista inicial)
ADMIN_IDS = [5876346562]  # Adicione aqui os IDs dos administradores

# Estados para a conversa de cadastro em etapas
CODIGO, NOME, FUNCAO, CONFIRMAR = range(4)

def inicializar_planilha():
    """
    Inicializa a planilha de cadastros se não existir
    ou cria uma nova se a existente estiver corrompida
    """
    try:
        if not os.path.exists(EXCEL_FILE):
            # Criar DataFrame com colunas padronizadas
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
        else:
            # Verificar se a planilha pode ser lida
            try:
                pd.read_excel(EXCEL_FILE)
                print(f"Planilha {EXCEL_FILE} verificada com sucesso")
            except Exception as e:
                print(f"Erro ao ler planilha existente: {e}")
                print("Criando nova planilha...")
                
                # Renomear arquivo com problema
                backup_name = f"{EXCEL_FILE}.bak"
                os.rename(EXCEL_FILE, backup_name)
                print(f"Arquivo existente renomeado para {backup_name}")
                
                # Criar nova planilha
                inicializar_planilha()
    except Exception as e:
        print(f"Erro ao inicializar planilha: {e}")

def carregar_admin_ids():
    """Carrega IDs de administradores de um arquivo"""
    global ADMIN_IDS
    try:
        if os.path.exists('admin_ids.txt'):
            with open('admin_ids.txt', 'r') as f:
                ids = [int(line.strip()) for line in f if line.strip().isdigit()]
                if ids:
                    ADMIN_IDS = ids
                    print(f"IDs de administradores carregados: {ADMIN_IDS}")
        else:
            # Criar arquivo se não existir
            with open('admin_ids.txt', 'w') as f:
                for admin_id in ADMIN_IDS:
                    f.write(f"{admin_id}\n")
            print(f"Arquivo admin_ids.txt criado com os IDs padrão: {ADMIN_IDS}")
    except Exception as e:
        print(f"Erro ao carregar IDs de administradores: {e}")

def inicializar_sistema():
    """Inicializa todos os componentes do sistema"""
    verificar_diretorios()  # Garantir que os diretórios existam antes de inicializar
    carregar_admin_ids()
    inicializar_planilha()
