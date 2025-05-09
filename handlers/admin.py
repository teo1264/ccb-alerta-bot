#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Handlers para funções administrativas do CCB Alerta Bot
"""

from handlers.data import FUNCOES, obter_igreja_por_codigo
import os
import pandas as pd
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, CallbackQueryHandler, ContextTypes

from config import EXCEL_FILE, ADMIN_IDS
try:
    # Primeiro tenta importar diretamente
    from utils import verificar_admin, adicionar_admin, fazer_backup_planilha
except ImportError:
    # Se falhar, tenta encontrar o módulo no diretório raiz
    import sys
    import os
    # Adicionar diretório pai ao path
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
    from utils import verificar_admin, adicionar_admin, fazer_backup_planilha

async def exportar_planilha(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Envia a planilha de cadastros como um arquivo (apenas para administradores)"""
    # Verificar se o usuário é administrador
    if not verificar_admin(update.effective_user.id):
        await update.message.reply_text(
            "A Santa Paz de Deus!\n\n"
            "⚠️ *Acesso Negado*\n\n"
            "Você não tem permissão para acessar esta função.\n\n"
            "_Deus te abençoe!_ 🙏",
            parse_mode='Markdown'
        )
        return
    
    try:
        if not os.path.exists(EXCEL_FILE):
            await update.message.reply_text(
                "A Santa Paz de Deus!\n\n"
                "❌ Nenhum arquivo de cadastro encontrado.\n\n"
                "_Deus te abençoe!_ 🙏",
                parse_mode='Markdown'
            )
            return
        
        # Enviar um relatório de diagnóstico sobre o arquivo
        await update.message.reply_text(
            "🔍 *Analisando arquivo de cadastros...*\n\n"
            f"Arquivo: `{EXCEL_FILE}`\n"
            "Por favor, aguarde enquanto preparamos os relatórios.",
            parse_mode='Markdown'
        )
        
        # Ler dados do arquivo existente
        df = pd.read_excel(EXCEL_FILE)
        
        # Verificar se há dados
        if df.empty:
            await update.message.reply_text(
                "A Santa Paz de Deus!\n\n"
                "❌ Planilha vazia, sem cadastros para exportar.\n\n"
                "_Deus te abençoe!_ 🙏",
                parse_mode='Markdown'
            )
            return
        
        # Enviar informações de diagnóstico
        info_text = (
            "📊 *Informações da Planilha:*\n\n"
            f"Total de registros: `{len(df)}`\n"
            f"Colunas encontradas: `{', '.join(df.columns)}`\n\n"
            "*Contagem de valores não nulos por coluna:*\n"
        )
        
        for col in df.columns:
            count = df[col].count()
            info_text += f"- {col}: `{count}` valores\n"
        
        await update.message.reply_text(info_text, parse_mode='Markdown')
        
        # Criar diversos arquivos para teste
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        
        # 1. Versão Excel normal
        excel_file = f"export_{timestamp}.xlsx"
        df.to_excel(excel_file, index=False)
        
        # 2. Versão CSV (mais confiável)
        csv_file = f"export_{timestamp}.csv"
        df.to_csv(csv_file, index=False)
        
        # 3. Versão Excel com formatação específica
        formatted_excel = f"formatted_{timestamp}.xlsx"
        with pd.ExcelWriter(formatted_excel, engine='openpyxl') as writer:
            df.to_excel(writer, index=False)
            worksheet = writer.sheets['Sheet1']
            for idx, col in enumerate(df.columns, 1):
                # Converter a letra de coluna do Excel (A, B, C...)
                letter = chr(64 + idx)
                worksheet.column_dimensions[letter].width = 20
        
        # 4. Gerar um relatório em texto plano
        txt_file = f"report_{timestamp}.txt"
        with open(txt_file, 'w', encoding='utf-8') as f:
            f.write("RELATÓRIO DE CADASTROS\n")
            f.write("====================\n\n")
            f.write(f"Data de geração: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n")
            f.write(f"Total de registros: {len(df)}\n\n")
            f.write("LISTA DE CADASTROS:\n\n")
            
            for idx, row in df.iterrows():
                f.write(f"Registro #{idx+1}:\n")
                for col in df.columns:
                    f.write(f"  {col}: {row[col]}\n")
                f.write("\n")
        
        # Enviar todos os arquivos
        await update.message.reply_text(
            "A Santa Paz de Deus!\n\n"
            "📋 *Relatórios gerados!*\n\n"
            "Estamos enviando os dados em diferentes formatos para análise. "
            "Por favor, verifique qual formato exibe as informações corretamente.\n\n"
            "_Deus te abençoe!_ 🙏",
            parse_mode='Markdown'
        )
        
        # Enviar Excel normal
        await update.message.reply_document(
            document=open(excel_file, 'rb'),
            filename="cadastros.xlsx",
            caption="📊 Planilha Excel (versão padrão)"
        )
        
        # Enviar CSV
        await update.message.reply_document(
            document=open(csv_file, 'rb'),
            filename="cadastros.csv",
            caption="📄 Arquivo CSV (pode ser aberto no Excel ou editor de texto)"
        )
        
        # Enviar Excel formatado
        await update.message.reply_document(
            document=open(formatted_excel, 'rb'),
            filename="cadastros_formatado.xlsx",
            caption="📊 Planilha Excel (com formatação especial)"
        )
        
        # Enviar relatório em texto
        await update.message.reply_document(
            document=open(txt_file, 'rb'),
            filename="relatorio_cadastros.txt",
            caption="📝 Relatório em texto plano"
        )
        
        # Limpar arquivos temporários
        try:
            os.remove(excel_file)
            os.remove(csv_file)
            os.remove(formatted_excel)
            os.remove(txt_file)
        except:
            pass
        
        print(f"Relatórios enviados para o administrador: {update.effective_user.id} - {update.effective_user.username}")
        
    except Exception as e:
        await update.message.reply_text(
            "A Santa Paz de Deus!\n\n"
            f"❌ Erro ao gerar relatórios: {str(e)}\n\n"
            "_Deus te abençoe!_ 🙏",
            parse_mode='Markdown'
        )
        
async def listar_cadastros(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Lista todos os cadastros (apenas para administradores)"""
    # Verificar se o usuário é administrador
    if not verificar_admin(update.effective_user.id):
        await update.message.reply_text(
            " *A Santa Paz de Deus!*\n\n"
            "⚠️ *Acesso Negado*\n\n"
            "Você não tem permissão para acessar esta função.\n\n"
            "_Deus te abençoe!_ 🙏",
            parse_mode='Markdown'
        )
        return
    
    # Extrair argumentos opcionais
    args = context.args
    filtro_igreja = None
    filtro_funcao = None
    
    # Analisar argumentos para filtros
    if args:
        for arg in args:
            if arg.upper().startswith('BR21-'):
                filtro_igreja = arg.upper()
            elif arg.lower() in [f.lower() for f in FUNCOES]:
                filtro_funcao = next(f for f in FUNCOES if f.lower() == arg.lower())
    
    try:
        if not os.path.exists(EXCEL_FILE):
            await update.message.reply_text(
                " *A Santa Paz de Deus!*\n\n"
                "❌ Nenhum cadastro encontrado.\n\n"
                "_Deus te abençoe!_ 🙏",
                parse_mode='Markdown'
            )
            return
            
        df = pd.read_excel(EXCEL_FILE)
        
        if df.empty:
            await update.message.reply_text(
                " *A Santa Paz de Deus!*\n\n"
                "❌ Nenhum cadastro encontrado.\n\n"
                "_Deus te abençoe!_ 🙏",
                parse_mode='Markdown'
            )
            return
        
        # Aplicar filtros se fornecidos
        if filtro_igreja:
            df = df[df['Codigo_Casa'].str.upper() == filtro_igreja]
        
        if filtro_funcao:
            df = df[df['Funcao'].str.lower() == filtro_funcao.lower()]
        
        if df.empty:
            await update.message.reply_text(
                "🕊️ *A Santa Paz de Deus!*\n\n"
                "❌ Nenhum cadastro encontrado com os filtros especificados.\n\n"
                "_Deus te abençoe!_ 🙏",
                parse_mode='Markdown'
            )
            return
        
        # Contar cadastros por igreja e função
        total_igrejas = df['Codigo_Casa'].nunique()
        total_cadastros = len(df)
        contagem_funcoes = df['Funcao'].value_counts().to_dict()
        
        # Criar resumo estatístico
        resumo = "🕊️ *A Santa Paz de Deus!*\n\n"
        resumo += "📊 *Resumo dos Cadastros:*\n\n"
        resumo += f"📍 Total de Igrejas: *{total_igrejas}*\n"
        resumo += f"👥 Total de Responsáveis: *{total_cadastros}*\n\n"
        resumo += "*Distribuição por Função:*\n"
        
        for funcao, contagem in contagem_funcoes.items():
            resumo += f"• {funcao}: *{contagem}*\n"
        
        resumo += "\n"
        
        # Agrupar por igreja
        igrejas_agrupadas = df.groupby('Codigo_Casa')
        
        # Formatar mensagem detalhada com os cadastros
        mensagem = "📋 *Lista de Cadastros:*\n\n"
        
        for codigo_igreja, grupo in igrejas_agrupadas:
            # Obter nome da igreja a partir do código
            igreja_info = obter_igreja_por_codigo(codigo_igreja)
            nome_igreja = igreja_info['nome'] if igreja_info else "Desconhecida"
            
            mensagem += f"📍 *{codigo_igreja} - {nome_igreja}*\n"
            
            for i, row in grupo.iterrows():
                mensagem += f"  👤 *{row['Nome']}* - {row['Funcao']}\n"
            
            mensagem += "\n"
        
        # Enviar primeiro o resumo estatístico
        await update.message.reply_text(resumo, parse_mode='Markdown')
        
        # Enviar a lista detalhada (possivelmente dividida se for muito grande)
        if len(mensagem) > 4096:
            partes = [mensagem[i:i+4096] for i in range(0, len(mensagem), 4096)]
            for parte in partes:
                await update.message.reply_text(parte, parse_mode='Markdown')
        else:
            await update.message.reply_text(mensagem, parse_mode='Markdown')
            
    except Exception as e:
        await update.message.reply_text(
            " *A Santa Paz de Deus!*\n\n"
            f"❌ Erro ao listar cadastros: {str(e)}\n\n"
            "_Deus te abençoe!_ 🙏",
            parse_mode='Markdown'
        )

async def limpar_cadastros(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Remove todos os cadastros (apenas para administradores)"""
    # Verificar se o usuário é administrador
    if not verificar_admin(update.effective_user.id):
        await update.message.reply_text(
            " *A Santa Paz de Deus!*\n\n"
            "⚠️ *Acesso Negado*\n\n"
            "Você não tem permissão para acessar esta função.\n\n"
            "_Deus te abençoe!_ 🙏",
            parse_mode='Markdown'
        )
        return
    
    # Confirmar ação com botões
    keyboard = [
        [
            InlineKeyboardButton("⚠️ Sim, limpar tudo", callback_data="confirmar_limpar"),
            InlineKeyboardButton("❌ Cancelar", callback_data="cancelar_limpar")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        " *A Santa Paz de Deus!*\n\n"
        "⚠️ *ATENÇÃO!*\n\n"
        "Você está prestes a *APAGAR TODOS OS CADASTROS*.\n"
        "Esta ação NÃO pode ser desfeita!\n\n"
        "Tem certeza que deseja continuar?",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def processar_callback_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Processa callbacks dos botões inline para comandos administrativos"""
    query = update.callback_query
    await query.answer()
    
    # Verificar se o usuário é administrador
    if not verificar_admin(update.effective_user.id):
        await query.edit_message_text(
            "🕊️ *A Santa Paz de Deus!*\n\n"
            "⚠️ *Acesso Negado*\n\n"
            "Você não tem permissão para acessar esta função.\n\n"
            "_Deus te abençoe!_ 🙏",
            parse_mode='Markdown'
        )
        return
    
    if query.data == "confirmar_limpar":
        try:
            if os.path.exists(EXCEL_FILE):
                # Fazer backup antes de limpar
                backup_file = fazer_backup_planilha()
                
                # Criar planilha vazia
                df = pd.DataFrame(columns=[
                    'Codigo_Casa', 'Nome', 'Funcao', 
                    'User_ID', 'Username', 'Data_Cadastro',
                    'Ultima_Atualizacao'
                ])
                df.to_excel(EXCEL_FILE, index=False)
                
                await query.edit_message_text(
                    "🕊️ *A Santa Paz de Deus!*\n\n"
                    "✅ *Todos os cadastros foram removidos!*\n\n"
                    f"Um backup foi criado como: `{backup_file}`\n\n"
                    "_Deus te abençoe!_ 🙏",
                    parse_mode='Markdown'
                )
            else:
                await query.edit_message_text(
                    "🕊️ *A Santa Paz de Deus!*\n\n"
                    "ℹ️ Nenhum cadastro encontrado para remover.\n\n"
                    "_Deus te abençoe!_ 🙏",
                    parse_mode='Markdown'
                )
        except Exception as e:
            await query.edit_message_text(
                "🕊️ *A Santa Paz de Deus!*\n\n"
                f"❌ Erro ao limpar cadastros: {str(e)}\n\n"
                "_Deus te abençoe!_ 🙏",
                parse_mode='Markdown'
            )
    
    elif query.data == "cancelar_limpar":
        await query.edit_message_text(
            " *A Santa Paz de Deus!*\n\n"
            "✅ *Operação cancelada!*\n\n"
            "Nenhum cadastro foi removido.\n\n"
            "_Deus te abençoe!_ 🙏",
            parse_mode='Markdown'
        )

async def adicionar_admin_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Adiciona um novo administrador (apenas para administradores)"""
    # Verificar se o usuário é administrador
    if not verificar_admin(update.effective_user.id):
        await update.message.reply_text(
            " *A Santa Paz de Deus!*\n\n"
            "⚠️ *Acesso Negado*\n\n"
            "Você não tem permissão para acessar esta função.\n\n"
            "_Deus te abençoe!_ 🙏",
            parse_mode='Markdown'
        )
        return
    
    # Verificar se há argumentos
    args = context.args
    if not args or not args[0].isdigit():
        await update.message.reply_text(
            " *A Santa Paz de Deus!*\n\n"
            "❌ *Formato inválido!*\n\n"
            "Use: `/admin_add ID_DO_USUARIO`\n"
            "Exemplo: `/admin_add 123456789`\n\n"
            "_Deus te abençoe!_ 🙏",
            parse_mode='Markdown'
        )
        return
    
    # Obter ID do novo administrador
    novo_admin_id = int(args[0])
    
    # Adicionar como administrador
    sucesso, status = adicionar_admin(novo_admin_id)
    
    if not sucesso and status == "já é admin":
        await update.message.reply_text(
            " *A Santa Paz de Deus!*\n\n"
            "ℹ️ Este usuário já é um administrador.\n\n"
            "_Deus te abençoe!_ 🙏",
            parse_mode='Markdown'
        )
        return
    
    if sucesso:
        await update.message.reply_text(
            " *A Santa Paz de Deus!*\n\n"
            f"✅ Administrador adicionado com sucesso: `{novo_admin_id}`\n\n"
            "_Deus te abençoe!_ 🙏",
            parse_mode='Markdown'
        )
    else:
        await update.message.reply_text(
            " *A Santa Paz de Deus!*\n\n"
            f"❌ Erro ao adicionar administrador: {status}\n\n"
            "_Deus te abençoe!_ 🙏",
            parse_mode='Markdown'
        )

def registrar_handlers_admin(application):
    """Registra handlers para funções administrativas"""
    application.add_handler(CommandHandler("exportar", exportar_planilha))
    application.add_handler(CommandHandler("listar", listar_cadastros))
    application.add_handler(CommandHandler("limpar", limpar_cadastros))
    application.add_handler(CommandHandler("admin_add", adicionar_admin_cmd))
    
    # Handler para os callbacks de confirmação nas funções administrativas
    application.add_handler(CallbackQueryHandler(
        processar_callback_admin, 
        pattern='^(confirmar_limpar|cancelar_limpar)$'
    ))
