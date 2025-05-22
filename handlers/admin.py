#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Handlers para funções administrativas do CCB Alerta Bot
"""

from handlers.data import FUNCOES, obter_igreja_por_codigo
import os
import pandas as pd
from datetime import datetime
import pytz
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, CallbackQueryHandler, ContextTypes

from config import ADMIN_IDS, DATA_DIR
try:
    # Primeiro tenta importar diretamente
    from utils import verificar_admin, adicionar_admin, fazer_backup_planilha
    from utils.database import (
        listar_todos_responsaveis, buscar_responsaveis_por_codigo,
        buscar_responsavel_por_id, remover_responsavel_especifico,
        editar_responsavel, limpar_todos_responsaveis, get_db_path,
        fazer_backup_banco
    )
except ImportError:
    # Se falhar, tenta encontrar o módulo no diretório raiz
    import sys
    # Adicionar diretório pai ao path
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
    from utils import verificar_admin, adicionar_admin, fazer_backup_planilha
    from utils.database import (
        listar_todos_responsaveis, buscar_responsaveis_por_codigo,
        buscar_responsavel_por_id, remover_responsavel_especifico,
        editar_responsavel, limpar_todos_responsaveis, get_db_path,
        fazer_backup_banco
    )

# Logger
import logging
logger = logging.getLogger("CCB-Alerta-Bot.admin")

# Estados para o gerenciamento de cadastros
SELECIONAR_ACAO, CONFIRMAR_EXCLUSAO = range(2)

async def exportar_planilha(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Exporta os dados do banco para planilhas e envia como arquivos"""
    # Verificar se o usuário é administrador
    if not verificar_admin(update.effective_user.id):
        await update.message.reply_text(
            "A Paz de Deus!\n\n"
            "⚠️ *Acesso Negado*\n\n"
            "Você não tem permissão para acessar esta função.\n\n"
            "_Deus te abençoe!_ 🙏",
            parse_mode='Markdown'
        )
        return
    
    try:
        # Obter todos os responsáveis do banco de dados
        responsaveis = listar_todos_responsaveis()
        
        if not responsaveis:
            await update.message.reply_text(
                "A Paz de Deus!\n\n"
                "❌ Nenhum cadastro encontrado no banco de dados.\n\n"
                "_Deus te abençoe!_ 🙏",
                parse_mode='Markdown'
            )
            return
        
        # Enviar informações sobre o banco de dados
        db_path = get_db_path()
        
        await update.message.reply_text(
            "🔍 *Analisando banco de dados...*\n\n"
            f"Banco de dados: `{db_path}`\n"
            "Por favor, aguarde enquanto preparamos os relatórios.",
            parse_mode='Markdown'
        )
        
        # Converter para DataFrame para facilitar exportação
        df = pd.DataFrame(responsaveis)
        
        # Verificar se há dados
        if df.empty:
            await update.message.reply_text(
                "A Paz de Deus!\n\n"
                "❌ Banco de dados vazio, sem cadastros para exportar.\n\n"
                "_Deus te abençoe!_ 🙏",
                parse_mode='Markdown'
            )
            return
        
        # Enviar informações de diagnóstico
        info_text = (
            "📊 *Informações do Banco de Dados:*\n\n"
            f"Total de registros: `{len(df)}`\n"
            f"Colunas disponíveis: `{', '.join(df.columns)}`\n\n"
            "*Contagem de valores não nulos por coluna:*\n"
        )
        
        for col in df.columns:
            count = df[col].count()
            info_text += f"- {col}: `{count}` valores\n"
        
        await update.message.reply_text(info_text, parse_mode='Markdown')
        
        # Criar diretório temporário para os arquivos
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        temp_dir = os.path.join(DATA_DIR, "temp", f"export_{timestamp}")
        os.makedirs(temp_dir, exist_ok=True)
        
        # 1. Versão Excel normal
        excel_file = os.path.join(temp_dir, "cadastros.xlsx")
        df.to_excel(excel_file, index=False)
        
        # 2. Versão CSV (mais confiável)
        csv_file = os.path.join(temp_dir, "cadastros.csv")
        df.to_csv(csv_file, index=False)
        
        # 3. Versão Excel com formatação específica
        formatted_excel = os.path.join(temp_dir, "cadastros_formatado.xlsx")
        with pd.ExcelWriter(formatted_excel, engine='openpyxl') as writer:
            df.to_excel(writer, index=False)
            worksheet = writer.sheets['Sheet1']
            for idx, col in enumerate(df.columns, 1):
                # Converter a letra de coluna do Excel (A, B, C...)
                letter = chr(64 + idx)
                worksheet.column_dimensions[letter].width = 20
        
        # 4. Gerar um relatório em texto plano
        txt_file = os.path.join(temp_dir, "relatorio_cadastros.txt")
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
            "A Paz de Deus!\n\n"
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
            import shutil
            shutil.rmtree(temp_dir)
        except:
            pass
        
        logger.info(f"Relatórios enviados para o administrador: {update.effective_user.id} - {update.effective_user.username}")
        
    except Exception as e:
        logger.error(f"Erro ao gerar relatórios: {e}")
        await update.message.reply_text(
            "A Paz de Deus!\n\n"
            f"❌ Erro ao gerar relatórios: {str(e)}\n\n"
            "_Deus te abençoe!_ 🙏",
            parse_mode='Markdown'
        )

async def listar_cadastros(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Lista todos os cadastros (apenas para administradores)"""
    # Verificar se o usuário é administrador
    if not verificar_admin(update.effective_user.id):
        await update.message.reply_text(
            " *A Paz de Deus!*\n\n"
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
        # Obter todos os cadastros do banco de dados
        if filtro_igreja:
            # Se houver filtro de igreja, buscar apenas por código
            responsaveis = buscar_responsaveis_por_codigo(filtro_igreja)
        else:
            # Caso contrário, buscar todos
            responsaveis = listar_todos_responsaveis()
        
        if not responsaveis:
            await update.message.reply_text(
                " *A Santa Paz de Deus!*\n\n"
                "❌ Nenhum cadastro encontrado.\n\n"
                "_Deus te abençoe!_ 🙏",
                parse_mode='Markdown'
            )
            return
        
        # Converter para DataFrame para facilitar filtragem e agrupamento
        df = pd.DataFrame(responsaveis)
        
        # Aplicar filtro de função, se fornecido
        if filtro_funcao and 'funcao' in df.columns:
            df = df[df['funcao'].str.lower() == filtro_funcao.lower()]
        
        if df.empty:
            await update.message.reply_text(
                " *A Paz de Deus!*\n\n"
                "❌ Nenhum cadastro encontrado com os filtros especificados.\n\n"
                "_Deus te abençoe!_ 🙏",
                parse_mode='Markdown'
            )
            return
        
        # Contar cadastros por igreja e função
        total_igrejas = df['codigo_casa'].nunique()
        total_cadastros = len(df)
        contagem_funcoes = df['funcao'].value_counts().to_dict()
        
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
        df['codigo_casa_upper'] = df['codigo_casa'].str.upper()  # Para garantir agrupamento correto
        igrejas_agrupadas = df.groupby('codigo_casa_upper')
        
        # Formatar mensagem detalhada com os cadastros
        mensagem = "📋 *Lista de Cadastros:*\n\n"
        
        # NOVA FUNCIONALIDADE: Criar índice global para exclusão simplificada
        indice_global = 1
        indices_cadastros = {}  # Dicionário para mapear índices a registros
        
        for codigo_igreja, grupo in igrejas_agrupadas:
            # Obter nome da igreja a partir do código
            igreja_info = obter_igreja_por_codigo(codigo_igreja)
            nome_igreja = igreja_info['nome'] if igreja_info else "Desconhecida"
            
            mensagem += f"📍 *{codigo_igreja} - {nome_igreja}*\n"
            
            for i, row in grupo.iterrows():
                # Adicionar número de índice global
                mensagem += f"  #{indice_global} 👤 *{row['nome']}* - {row['funcao']}\n"
                
                # Armazenar mapeamento de índice para cadastro
                indices_cadastros[indice_global] = {
                    'codigo': row['codigo_casa'],
                    'nome': row['nome'],
                    'funcao': row['funcao'],
                    'id': row['id']  # ID no banco
                }
                indice_global += 1
            
            mensagem += "\n"
        
        # Armazenar índices no contexto do usuário para uso posterior
        context.user_data['indices_cadastros'] = indices_cadastros
        
        # Adicionar instrução para exclusão simplificada
        mensagem += "*Para excluir um cadastro, use:*\n"
        mensagem += "`/excluir_id NÚMERO`\n\n"
        mensagem += "Exemplo: `/excluir_id 3` para excluir o cadastro #3\n\n"
        
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
        logger.error(f"Erro ao listar cadastros: {e}")
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
            "*A Paz de Deus!*\n\n"
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
        "*A Paz de Deus!*\n\n"
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
            "*A Paz de Deus!*\n\n"
            "⚠️ *Acesso Negado*\n\n"
            "Você não tem permissão para acessar esta função.\n\n"
            "_Deus te abençoe!_ 🙏",
            parse_mode='Markdown'
        )
        return
    
    if query.data == "confirmar_limpar":
        try:
            # Fazer backup antes de limpar
            backup_file = fazer_backup_banco()
            
            # Limpar todos os registros
            sucesso = limpar_todos_responsaveis()
            
            if sucesso:
                await query.edit_message_text(
                    "*A Paz de Deus!*\n\n"
                    "✅ *Todos os cadastros foram removidos!*\n\n"
                    f"Um backup foi criado como: `{backup_file}`\n\n"
                    "_Deus te abençoe!_ 🙏",
                    parse_mode='Markdown'
                )
            else:
                await query.edit_message_text(
                    "*A Paz de Deus!*\n\n"
                    "❌ *Erro ao remover cadastros.*\n\n"
                    "_Deus te abençoe!_ 🙏",
                    parse_mode='Markdown'
                )
        except Exception as e:
            logger.error(f"Erro ao limpar cadastros: {e}")
            await query.edit_message_text(
                "*A Paz de Deus!*\n\n"
                f"❌ *Erro ao limpar cadastros: {str(e)}*\n\n"
                "_Deus te abençoe!_ 🙏",
                parse_mode='Markdown'
            )
    
    elif query.data == "cancelar_limpar":
        await query.edit_message_text(
            "*A Paz de Deus!*\n\n"
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
            "*A Paz de Deus!*\n\n"
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
            "*A Paz de Deus!*\n\n"
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
            "*A Paz de Deus!*\n\n"
            "ℹ️ *Este usuário já é um administrador.*\n\n"
            "_Deus te abençoe!_ 🙏",
            parse_mode='Markdown'
        )
        return
    
    if sucesso:
        await update.message.reply_text(
            "*A Paz de Deus!*\n\n"
            f"✅ *Administrador adicionado com sucesso: `{novo_admin_id}`*\n\n"
            "_Deus te abençoe!_ 🙏",
            parse_mode='Markdown'
        )
    else:
        await update.message.reply_text(
            "*A Paz de Deus!*\n\n"
            f"❌ *Erro ao adicionar administrador: {status}*\n\n"
            "_Deus te abençoe!_ 🙏",
            parse_mode='Markdown'
        )

async def editar_buscar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Busca cadastros para edição (apenas para administradores)
    Uso: /editar_buscar TERMO_BUSCA
    Exemplo: /editar_buscar João
    """
    # Verificar se o usuário é administrador
    if not verificar_admin(update.effective_user.id):
        await update.message.reply_text(
            "A Paz de Deus!\n\n"
            "⚠️ *Acesso Negado*\n\n"
            "Você não tem permissão para acessar esta função.\n\n"
            "_Deus te abençoe!_ 🙏",
            parse_mode='Markdown'
        )
        return
    
    # Verificar argumentos
    args = context.args
    if not args:
        await update.message.reply_text(
            "A Paz de Deus!\n\n"
            "❌ *Formato inválido!*\n\n"
            "Use: `/editar_buscar TERMO_BUSCA`\n"
            "Exemplo: `/editar_buscar João` ou `/editar_buscar BR21-0001`\n\n"
            "Você pode buscar por partes do nome, código ou função.\n\n"
            "_Deus te abençoe!_ 🙏",
            parse_mode='Markdown'
        )
        return
    
    termo_busca = ' '.join(args).lower()
    
    try:
        # Buscar todos os responsáveis
        todos_responsaveis = listar_todos_responsaveis()
        
        if not todos_responsaveis:
            await update.message.reply_text(
                "A Paz de Deus!\n\n"
                "❌ *Nenhum cadastro encontrado no banco de dados.*\n\n"
                "_Deus te abençoe!_ 🙏",
                parse_mode='Markdown'
            )
            return
        
        # Buscar em todas as colunas relevantes
        colunas_busca = ['codigo_casa', 'nome', 'funcao']
        resultados = []
        
        for responsavel in todos_responsaveis:
            encontrado = False
            for coluna in colunas_busca:
                if coluna in responsavel and termo_busca in str(responsavel[coluna]).lower():
                    encontrado = True
                    break
            
            if encontrado:
                resultados.append(responsavel)
        
        if len(resultados) == 0:
            await update.message.reply_text(
                "A Paz de Deus!\n\n"
                f"ℹ️ *Encontrados {len(responsaveis)} cadastros com o código {codigo}*\n\n"
                "Por favor, especifique qual registro deseja editar usando o comando:\n"
                "`/editar CODIGO CAMPO VALOR \"NOME\"`\n\n"
                "Por exemplo: `/editar BR21-0001 Funcao \"Auxiliar da Escrita\" \"João da Silva\"`\n\n"
                "Cadastros encontrados:\n"
            )
            
            for i, resp in enumerate(responsaveis, 1):
                mensagem += f"{i}. *{resp['nome']}* ({resp['funcao']})\n"
            
            await update.message.reply_text(mensagem, parse_mode='Markdown')
            return
        
        # Se chegou aqui, há apenas um responsável com este código
        responsavel = responsaveis[0]
        
        # Fazer backup antes de modificar
        fazer_backup_banco()
        
        # Obter valor antigo para mostrar na confirmação
        valor_antigo = responsavel[campo_db]
        
        # Preparar dicionário com campos a serem atualizados
        campos_atualizacao = {campo_db: valor}
        
        # Atualizar a data de modificação
        fuso_horario = pytz.timezone('America/Sao_Paulo')
        agora = datetime.now(fuso_horario)
        data_formatada = agora.strftime("%d/%m/%Y %H:%M:%S")
        campos_atualizacao['ultima_atualizacao'] = data_formatada
        
        # Atualizar cadastro
        sucesso = editar_responsavel(responsavel['id'], campos_atualizacao)
        
        if not sucesso:
            await update.message.reply_text(
                "A Paz de Deus!\n\n"
                "❌ *Erro ao atualizar cadastro.*\n\n"
                "Por favor, tente novamente mais tarde.\n\n"
                "_Deus te abençoe!_ 🙏",
                parse_mode='Markdown'
            )
            return
        
        # Obter nome da igreja para a mensagem de confirmação
        nome_igreja = "Desconhecida"
        try:
            igreja_info = obter_igreja_por_codigo(codigo)
            if igreja_info:
                nome_igreja = igreja_info['nome']
        except:
            pass
        
        await update.message.reply_text(
            "A Paz de Deus!\n\n"
            "✅ *Cadastro atualizado com sucesso!*\n\n"
            f"📄 *Código:* `{codigo}`\n"
            f"🏢 *Casa:* `{nome_igreja}`\n"
            f"👤 *Nome:* `{responsavel['nome']}`\n"
            f"📝 *Campo atualizado:* `{campo}`\n"
            f"📄 *Valor antigo:* `{valor_antigo}`\n"
            f"📄 *Novo valor:* `{valor}`\n\n"
            "_Deus te abençoe!_ 🙏",
            parse_mode='Markdown'
        )
        
    except Exception as e:
        logger.error(f"Erro ao atualizar cadastro: {e}")
        await update.message.reply_text(
            "A Santa Paz de Deus!\n\n"
            f"❌ *Erro ao atualizar cadastro: {str(e)}*\n\n"
            "_Deus te abençoe!_ 🙏",
            parse_mode='Markdown'
        )❌ *Nenhum cadastro encontrado com o termo '{termo_busca}'.*\n\n"
                "_Deus te abençoe!_ 🙏",
                parse_mode='Markdown'
            )
            return
        
        # Montar mensagem com os resultados
        mensagem = (
            "A Santa Paz de Deus!\n\n"
            f"✅ *{len(resultados)} cadastros encontrados:*\n\n"
        )
        
        for i, row in enumerate(resultados, 1):
            mensagem += (
                f"*{i}. {row['codigo_casa']} - {row['nome']}*\n"
                f"   Função: {row['funcao']}\n"
                f"   Última atualização: {row['ultima_atualizacao']}\n\n"
            )
        
        mensagem += (
            "*Para editar um cadastro, use o comando:*\n"
            "`/editar CODIGO_CASA CAMPO NOVO_VALOR`\n\n"
            "Exemplo: `/editar BR21-0001 Nome \"Novo Nome\"`\n\n"
            "Campos disponíveis: `codigo_casa`, `nome`, `funcao`\n\n"
            "_Deus te abençoe!_ 🙏"
        )
        
        # Enviar resultados
        await update.message.reply_text(mensagem, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Erro ao buscar cadastros: {e}")
        await update.message.reply_text(
            "A Santa Paz de Deus!\n\n"
            f"❌ *Erro ao buscar cadastros: {str(e)}*\n\n"
            "_Deus te abençoe!_ 🙏",
            parse_mode='Markdown'
        )

async def editar_cadastro(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Edita um cadastro existente (apenas para administradores)
    Uso: /editar CODIGO_CASA CAMPO NOVO_VALOR
    Exemplo: /editar BR21-0001 Nome "João da Silva"
    """
    # Verificar se o usuário é administrador
    if not verificar_admin(update.effective_user.id):
        await update.message.reply_text(
            "A Paz de Deus!\n\n"
            "⚠️ *Acesso Negado*\n\n"
            "Você não tem permissão para acessar esta função.\n\n"
            "_Deus te abençoe!_ 🙏",
            parse_mode='Markdown'
        )
        return
    
    # Verificar argumentos
    args = context.args
    if len(args) < 3:
        await update.message.reply_text(
            "A Paz de Deus!\n\n"
            "❌ *Formato inválido!*\n\n"
            "Use: `/editar CODIGO_CASA CAMPO NOVO_VALOR`\n"
            "Exemplo: `/editar BR21-0001 Nome \"João da Silva\"`\n\n"
            "Campos disponíveis: `codigo_casa`, `nome`, `funcao`\n\n"
            "Para encontrar um cadastro, use o comando `/editar_buscar`.\n\n"
            "_Deus te abençoe!_ 🙏",
            parse_mode='Markdown'
        )
        return
    
    codigo = args[0]
    campo = args[1].lower()  # Normalizar para lowercase
    valor = ' '.join(args[2:])
    
    # Remover aspas que possam estar em volta do valor
    valor = valor.strip('"\'')
    
    try:
        # Mapear campos de comando para nomes de colunas no banco
        mapeamento_campos = {
            'nome': 'nome',
            'funcao': 'funcao',
            'codigo': 'codigo_casa',
            'codigo_casa': 'codigo_casa'
        }
        
        # Verificar se o campo é válido
        campos_permitidos = list(mapeamento_campos.keys())
        if campo.lower() not in campos_permitidos:
            await update.message.reply_text(
                "A Paz de Deus!\n\n"
                f"❌ *Campo `{campo}` não permitido para edição.*\n"
                f"Campos permitidos: `{', '.join(campos_permitidos)}`\n\n"
                "_Deus te abençoe!_ 🙏",
                parse_mode='Markdown'
            )
            return
        
        # Obter nome real do campo no banco
        campo_db = mapeamento_campos[campo.lower()]
        
        # Buscar responsáveis com o código informado
        responsaveis = buscar_responsaveis_por_codigo(codigo)
        
        if not responsaveis:
            await update.message.reply_text(
                "A Paz de Deus!\n\n"
                f"❌ *Código `{codigo}` não encontrado no banco de dados.*\n\n"
                "Use o comando `/editar_buscar` para encontrar o código correto.\n\n"
                "_Deus te abençoe!_ 🙏",
                parse_mode='Markdown'
            )
            return
        
        # Se houver mais de um responsável com o mesmo código, perguntar qual editar
        if len(responsaveis) > 1:
            mensagem = (
                "A Paz de Deus!\n\n"
                f"ℹ️ *Encontrados {len(responsaveis)} cadastros com o código {codigo}*\n\n"
                "Por favor, especifique qual registro deseja editar usando o comando:\n"
                "`/editar CODIGO CAMPO VALOR \"NOME\"`\n\n"
                "Por exemplo: `/editar BR21-0001 Funcao \"Auxiliar da Escrita\" \"João da Silva\"`\n\n"
                "Cadastros encontrados:\n"
            )
            
            for i, resp in enumerate(responsaveis, 1):
                mensagem += f"{i}. *{resp['nome']}* ({resp['funcao']})\n"
            
            await update.message.reply_text(mensagem, parse_mode='Markdown')
            return
        
        # Se chegou aqui, há apenas um responsável com este código
        responsavel = responsaveis[0]
        
        # Fazer backup antes de modificar
        fazer_backup_banco()
        
        # Obter valor antigo para mostrar na confirmação
        valor_antigo = responsavel[campo_db]
        
        # Preparar dicionário com campos a serem atualizados
        campos_atualizacao = {campo_db: valor}
        
        # Atualizar a data de modificação
        fuso_horario = pytz.timezone('America/Sao_Paulo')
        agora = datetime.now(fuso_horario)
        data_formatada = agora.strftime("%d/%m/%Y %H:%M:%S")
        campos_atualizacao['ultima_atualizacao'] = data_formatada
        
        # Atualizar cadastro
        sucesso = editar_responsavel(responsavel['id'], campos_atualizacao)
        
        if not sucesso:
            await update.message.reply_text(
                "A Paz de Deus!\n\n"
                "❌ *Erro ao atualizar cadastro.*\n\n"
                "Por favor, tente novamente mais tarde.\n\n"
                "_Deus te abençoe!_ 🙏",
                parse_mode='Markdown'
            )
            return
        
        # Obter nome da igreja para a mensagem de confirmação
        nome_igreja = "Desconhecida"
        try:
            igreja_info = obter_igreja_por_codigo(codigo)
            if igreja_info:
                nome_igreja = igreja_info['nome']
        except:
            pass
        
        await update.message.reply_text(
            "A Paz de Deus!\n\n"
            "✅ *Cadastro atualizado com sucesso!*\n\n"
            f"📄 *Código:* `{codigo}`\n"
            f"🏢 *Casa:* `{nome_igreja}`\n"
            f"👤 *Nome:* `{responsavel['nome']}`\n"
            f"📝 *Campo atualizado:* `{campo}`\n"
            f"📄 *Valor antigo:* `{valor_antigo}`\n"
            f"📄 *Novo valor:* `{valor}`\n\n"
            "_Deus te abençoe!_ 🙏",
            parse_mode='Markdown'
        )
        
    except Exception as e:
        logger.error(f"Erro ao atualizar cadastro: {e}")
        await update.message.reply_text(
            "A Santa Paz de Deus!\n\n"
            f"❌ *Erro ao atualizar cadastro: {str(e)}*\n\n"
            "_Deus te abençoe!_ 🙏",
            parse_mode='Markdown'
        )

async def excluir_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Exclui um cadastro pelo número de ID (simplificado)
    Uso: /excluir_id NUMERO
    Exemplo: /excluir_id 3
    """
    # Verificar se o usuário é administrador
    if not verificar_admin(update.effective_user.id):
        await update.message.reply_text(
            "A Paz de Deus!\n\n"
            "⚠️ *Acesso Negado*\n\n"
            "Você não tem permissão para acessar esta função.\n\n"
            "_Deus te abençoe!_ 🙏",
            parse_mode='Markdown'
        )
        return
    
    # Verificar argumentos
    args = context.args
    if not args or not args[0].isdigit():
        await update.message.reply_text(
            "A Paz de Deus!\n\n"
            "❌ *Formato inválido!*\n\n"
            "Use: `/excluir_id NUMERO`\n"
            "Exemplo: `/excluir_id 3`\n\n"
            "O número deve corresponder ao índice mostrado nos resultados de busca.\n\n"
            "_Deus te abençoe!_ 🙏",
            parse_mode='Markdown'
        )
        return
    
    # Obter o ID do cadastro a ser excluído
    indice = int(args[0])
    
    # Verificar se há cadastros no contexto
    if 'indices_cadastros' not in context.user_data or not context.user_data['indices_cadastros']:
        await update.message.reply_text(
            "A Paz de Deus!\n\n"
            "❓ *Por favor, primeiro use `/listar` ou `/buscar` para ver os cadastros disponíveis.*\n\n"
            "_Deus te abençoe!_ 🙏",
            parse_mode='Markdown'
        )
        return
    
    # Verificar se o índice existe
    indices_cadastros = context.user_data['indices_cadastros']
    if indice not in indices_cadastros:
        await update.message.reply_text(
            "A Paz de Deus!\n\n"
            f"❌ *Não foi encontrado cadastro com o índice #{indice}.*\n\n"
            "Use `/listar` ou `/buscar` para ver os números de índice corretos.\n\n"
            "_Deus te abençoe!_ 🙏",
            parse_mode='Markdown'
        )
        return
    
    # Obter dados do cadastro
    cadastro = indices_cadastros[indice]
    
    # Obter nome da igreja para a mensagem de confirmação
    nome_igreja = "Desconhecida"
    try:
        igreja_info = obter_igreja_por_codigo(cadastro['codigo'])
        if igreja_info:
            nome_igreja = igreja_info['nome']
    except:
        pass
    
    # Armazenar temporariamente o cadastro a ser excluído
    context.user_data['cadastro_exclusao'] = cadastro
    
    # Botões de confirmação
    keyboard = [
        [
            InlineKeyboardButton("✅ Sim, excluir", callback_data="confirmar_exclusao_id"),
            InlineKeyboardButton("❌ Não, cancelar", callback_data="cancelar_exclusao_id")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "A Paz de Deus!\n\n"
        "⚠️ *Confirmação de Exclusão*\n\n"
        "Você está prestes a excluir o seguinte cadastro:\n\n"
        f"📍 *Código:* `{cadastro['codigo']}`\n"
        f"🏢 *Casa:* `{nome_igreja}`\n"
        f"👤 *Nome:* `{cadastro['nome']}`\n"
        f"🧑‍💼 *Função:* `{cadastro['funcao']}`\n\n"
        "Tem certeza que deseja excluir este cadastro?\n\n"
        "Esta ação não pode ser desfeita!",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def processar_callback_exclusao(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Processa os callbacks de confirmação ou cancelamento de exclusão"""
    query = update.callback_query
    await query.answer()
    
    # Verificar se o usuário é administrador
    if not verificar_admin(update.effective_user.id):
        await query.edit_message_text(
            "A Paz de Deus!\n\n"
            "⚠️ *Acesso Negado*\n\n"
            "Você não tem permissão para acessar esta função.\n\n"
            "_Deus te abençoe!_ 🙏",
            parse_mode='Markdown'
        )
        return
    
    if query.data == "cancelar_exclusao_id":
        # Limpar dados de exclusão
        if 'cadastro_exclusao' in context.user_data:
            del context.user_data['cadastro_exclusao']
        
        await query.edit_message_text(
            "A Paz de Deus!\n\n"
            "✅ *Exclusão cancelada!*\n\n"
            "Nenhum cadastro foi excluído.\n\n"
            "_Deus te abençoe!_ 🙏",
            parse_mode='Markdown'
        )
        return
    
    elif query.data == "confirmar_exclusao_id":
        # Verificar se há dados de exclusão
        if 'cadastro_exclusao' not in context.user_data:
            await query.edit_message_text(
                "A Paz de Deus!\n\n"
                "❌ *Não foi possível excluir o cadastro. Dados não encontrados.*\n\n"
                "Por favor, tente novamente.\n\n"
                "_Deus te abençoe!_ 🙏",
                parse_mode='Markdown'
            )
            return
        
        cadastro = context.user_data['cadastro_exclusao']
        
        try:
            # Fazer backup antes de modificar
            fazer_backup_banco()
            
            # Excluir o cadastro utilizando seu ID
            sucesso, total = remover_responsavel_especifico(
                cadastro['codigo'], 
                cadastro['nome'],
                cadastro['funcao']
            )
            
            if not sucesso or total == 0:
                await query.edit_message_text(
                    "A Paz de Deus!\n\n"
                    "❌ *Não foi possível excluir o cadastro. Registro não encontrado.*\n\n"
                    "O cadastro pode já ter sido excluído anteriormente.\n\n"
                    "_Deus te abençoe!_ 🙏",
                    parse_mode='Markdown'
                )
                return
            
            # Obter nome da igreja para a mensagem de confirmação
            nome_igreja = "Desconhecida"
            try:
                igreja_info = obter_igreja_por_codigo(cadastro['codigo'])
                if igreja_info:
                    nome_igreja = igreja_info['nome']
            except:
                pass
            
            await query.edit_message_text(
                "A Paz de Deus!\n\n"
                "✅ *Cadastro excluído com sucesso!*\n\n"
                f"📍 *Código:* `{cadastro['codigo']}`\n"
                f"🏢 *Casa:* `{nome_igreja}`\n"
                f"👤 *Nome:* `{cadastro['nome']}`\n"
                f"🧑‍💼 *Função:* `{cadastro['funcao']}`\n\n"
                "_Deus te abençoe!_ 🙏",
                parse_mode='Markdown'
            )
            
            # Limpar dados de exclusão
            del context.user_data['cadastro_exclusao']
            
            # Atualizar a lista de índices para refletir a exclusão
            if 'indices_cadastros' in context.user_data:
                # Não podemos simplesmente remover o índice, pois os outros índices 
                # não seriam atualizados. Em vez disso, marcamos como excluído
                for idx in context.user_data['indices_cadastros']:
                    if context.user_data['indices_cadastros'][idx].get('id') == cadastro['id']:
                        context.user_data['indices_cadastros'][idx]['excluido'] = True
            
        except Exception as e:
            logger.error(f"Erro ao excluir cadastro: {e}")
            await query.edit_message_text(
                "A Paz de Deus!\n\n"
                f"❌ Erro ao excluir cadastro: {str(e)}\n\n"
                "_Deus te abençoe!_ 🙏",
                parse_mode='Markdown'
            )
            return

async def excluir_cadastro(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Exclui um cadastro específico (apenas para administradores)
    Uso: /excluir CODIGO_CASA NOME
    Exemplo: /excluir BR21-0001 "João da Silva"
    """
    # Verificar se o usuário é administrador
    if not verificar_admin(update.effective_user.id):
        await update.message.reply_text(
            "A Paz de Deus!\n\n"
            "⚠️ *Acesso Negado*\n\n"
            "Você não tem permissão para acessar esta função.\n\n"
            "_Deus te abençoe!_ 🙏",
            parse_mode='Markdown'
        )
        return
    
    # Verificar argumentos
    args = context.args
    if len(args) < 2:
        await update.message.reply_text(
            "A Santa Paz de Deus!\n\n"
            "❌ *Formato inválido!*\n\n"
            "Use: `/excluir CODIGO_CASA NOME`\n"
            "Exemplo: `/excluir BR21-0001 \"João da Silva\"`\n\n"
            "Para encontrar um cadastro, use o comando `/editar_buscar`.\n\n"
            "_Deus te abençoe!_ 🙏",
            parse_mode='Markdown'
        )
        return
    
    codigo = args[0]
    nome = ' '.join(args[1:])
    
    # Remover aspas que possam estar em volta do nome
    nome = nome.strip('"\'')
    
    try:
        # Buscar responsáveis com o código informado
        responsaveis = buscar_responsaveis_por_codigo(codigo)
        
        if not responsaveis:
            await update.message.reply_text(
                "A Paz de Deus!\n\n"
                f"❌ Cadastro não encontrado para código `{codigo}`.\n\n"
                "Use o comando `/editar_buscar` para encontrar o cadastro correto.\n\n"
                "_Deus te abençoe!_ 🙏",
                parse_mode='Markdown'
            )
            return
        
        # Filtrar pelo nome
        responsaveis_filtrados = [r for r in responsaveis if r['nome'].lower() == nome.lower()]
        
        if not responsaveis_filtrados:
            await update.message.reply_text(
                "A Paz de Deus!\n\n"
                f"❌ Cadastro não encontrado para código `{codigo}` e nome `{nome}`.\n\n"
                "Use o comando `/editar_buscar` para encontrar o cadastro correto.\n\n"
                "_Deus te abençoe!_ 🙏",
                parse_mode='Markdown'
            )
            return
        
        # Fazer backup antes de modificar
        fazer_backup_banco()
        
        # Obter nome da igreja para a mensagem de confirmação
        nome_igreja = "Desconhecida"
        try:
            igreja_info = obter_igreja_por_codigo(codigo)
            if igreja_info:
                nome_igreja = igreja_info['nome']
        except:
            pass
        
        # Excluir cadastro
        sucesso, total = remover_responsavel_especifico(codigo, nome)
        
        if not sucesso or total == 0:
            await update.message.reply_text(
                "A Paz de Deus!\n\n"
                "❌ *Não foi possível excluir o cadastro.*\n\n"
                "_Deus te abençoe!_ 🙏",
                parse_mode='Markdown'
            )
            return
        
        await update.message.reply_text(
            "A Paz de Deus!\n\n"
            "✅ *Cadastro excluído com sucesso!*\n\n"
            f"📄 *Código:* `{codigo}`\n"
            f"🏢 *Casa:* `{nome_igreja}`\n"
            f"👤 *Nome:* `{nome}`\n\n"
            "_Deus te abençoe!_ 🙏",
            parse_mode='Markdown'
        )
        
    except Exception as e:
        logger.error(f"Erro ao excluir cadastro: {e}")
        await update.message.reply_text(
            "A Santa Paz de Deus!\n\n"
            f"❌ Erro ao excluir cadastro: {str(e)}\n\n"
            "_Deus te abençoe!_ 🙏",
            parse_mode='Markdown'
        )

# Função para registrar todos os handlers administrativos
def registrar_handlers_admin(application):
    """Registra todos os handlers administrativos"""
    # Comandos administrativos básicos
    application.add_handler(CommandHandler("exportar", exportar_planilha))
    application.add_handler(CommandHandler("listar", listar_cadastros))
    application.add_handler(CommandHandler("limpar", limpar_cadastros))
    application.add_handler(CommandHandler("admin_add", adicionar_admin_cmd))
    
    # Comandos para edição e busca
    application.add_handler(CommandHandler("editar_buscar", editar_buscar))
    application.add_handler(CommandHandler("editar", editar_cadastro))
    
    # Comandos para exclusão
    application.add_handler(CommandHandler("excluir", excluir_cadastro))
    application.add_handler(CommandHandler("excluir_id", excluir_id))
    
    # Callbacks para botões inline
    application.add_handler(CallbackQueryHandler(
        processar_callback_admin, 
        pattern='^(confirmar_limpar|cancelar_limpar)$'
    ))
    
    application.add_handler(CallbackQueryHandler(
        processar_callback_exclusao, 
        pattern='^(confirmar_exclusao_id|cancelar_exclusao_id)$'
    ))
