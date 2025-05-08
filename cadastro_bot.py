        from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
import os
import pandas as pd
from datetime import datetime
import re
import pytz

TOKEN = "7773179413:AAHqJp-NBPPs6YrSV1kB5-q4vkV3tjDFyy4"
EXCEL_FILE = "responsaveis_casas.xlsx"

# Coloque aqui o seu ID do Telegram e de outros administradores
ADMIN_IDS = [6661599889]  # Substitua pelos IDs reais dos administradores

async def mensagem_boas_vindas(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Responde a qualquer mensagem com uma saudação e instruções"""
    await update.message.reply_text(
        "🕊️ *A Santa Paz de Deus!*\n\n"
        "📢 *Bem-vindo ao sistema de alertas automáticos da CCB ADM Mauá!*\n\n"
        "⚙️ Este serviço está em *fase de desenvolvimento* e funcionará de forma gratuita, auxiliando na gestão das Casas de Oração.\n\n"
        "🔔 *Você receberá alertas sobre:*\n"
        "• 💧 Consumo excessivo de água (BRK)\n"
        "• ⚡ Consumo fora do padrão de energia (ENEL)\n"
        "• ☀️ Relatórios mensais de compensação (para casas com sistema fotovoltaico)\n\n"
        "📝 *Como se cadastrar?*\n"
        "Envie a seguinte mensagem (sem acento):\n"
        "`BR21-0000 / Seu Nome Completo / Sua Função`\n\n"
        "📌 *Exemplo:*\n"
        "`BR21-0270 / João Silva / Cooperador`\n\n"
        "👥 Destinado a:\n"
        "✅ Cooperadores\n"
        "✅ Encarregados de Manutenção\n"
        "✅ Responsáveis pela Escrita\n"
        "✅ E demais irmãos do ministério\n\n"
        "_Deus te abençoe!_ 🙏",
        parse_mode='Markdown'
    )

def inicializar_planilha():
    """Inicializa a planilha de cadastros se não existir"""
    if not os.path.exists(EXCEL_FILE):
        df = pd.DataFrame(columns=[
            'Codigo_Casa', 'Nome', 'Funcao', 
            'User_ID', 'Username', 'Data_Cadastro',
            'Ultima_Atualizacao'
        ])
        df.to_excel(EXCEL_FILE, index=False)
        print(f"Planilha {EXCEL_FILE} criada com sucesso")

def verificar_duplicata(codigo):
    """Verifica se já existe cadastro com o mesmo código"""
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
        
def salvar_cadastro(texto, user_id, username):
    """Salva os dados do cadastro na planilha Excel"""
    try:
        # Inicializar planilha se não existir
        inicializar_planilha()
        
        # Separar os dados pelo delimitador "/"
        partes = [p.strip() for p in texto.split('/')]
        
        # Garantir que temos pelo menos 3 partes (código, nome, função)
        if len(partes) >= 3:
            codigo_casa = partes[0].strip()
            nome = partes[1].strip()
            funcao = partes[2].strip()
        else:
            # Se não tiver 3 partes, use o texto completo e deixe campos em branco
            codigo_casa = texto.strip()
            nome = ""
            funcao = ""
        
        # Verificar duplicata antes de salvar
        if verificar_duplicata(codigo_casa):
            print(f"Tentativa de cadastro duplicado: {codigo_casa}")
            return False, "duplicado"
        
        # Data atual em formato brasileiro
        fuso_horario = pytz.timezone('America/Sao_Paulo')
        agora = datetime.now(fuso_horario)
        data_formatada = agora.strftime("%d/%m/%Y %H:%M:%S")
        
        # Criar DataFrame com os dados
        data = {
            'Codigo_Casa': [codigo_casa],
            'Nome': [nome],
            'Funcao': [funcao],
            'User_ID': [user_id],
            'Username': [username],
            'Data_Cadastro': [data_formatada],
            'Ultima_Atualizacao': [data_formatada]
        }
        df = pd.DataFrame(data)
        
        # Verificar se o arquivo já existe
        if os.path.exists(EXCEL_FILE):
            # Adicionar nova linha ao arquivo existente
            df_existente = pd.read_excel(EXCEL_FILE)
            df_atualizado = pd.concat([df_existente, df], ignore_index=True)
            df_atualizado.to_excel(EXCEL_FILE, index=False)
        else:
            # Criar novo arquivo
            df.to_excel(EXCEL_FILE, index=False)
            
        print(f"Cadastro salvo com sucesso: {texto}")
        return True, "sucesso"
    except Exception as e:
        print(f"Erro ao salvar cadastro: {e}")
        return False, str(e)

async def cadastro(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Processa um cadastro enviado com /cadastro"""
    texto = update.message.text.replace('/cadastro', '').strip()
    
    # Verificar se há dados após o comando
    if not texto:
        await mensagem_boas_vindas(update, context)
        return
    
    # Verificar formato
    if not verificar_formato_cadastro(texto):
        await update.message.reply_text(
            "🕊️ *A Santa Paz de Deus!*\n\n"
            "❌ *Formato inválido!*\n\n"
            "📝 Por favor, use o formato correto:\n"
            "`BR21-0000 / Seu Nome Completo / Sua Função`\n\n"
            "📌 *Exemplo:*\n"
            "`BR21-0270 / João Silva / Cooperador`\n\n"
            "_Deus te abençoe!_ 🙏",
            parse_mode='Markdown'
        )
        return
    
    # Salvar os dados
    sucesso, status = salvar_cadastro(texto, update.effective_user.id, update.effective_user.username)
    
    if not sucesso and status == "duplicado":
        await update.message.reply_text(
            "🕊️ *A Santa Paz de Deus!*\n\n"
            "⚠️ *Atenção!*\n\n"
            f"O código da Casa de Oração já está cadastrado no sistema.\n\n"
            "Se precisar atualizar as informações, entre em contato com o administrador.\n\n"
            "_Deus te abençoe!_ 🙏",
            parse_mode='Markdown'
        )
        return
    
    if sucesso:
        await update.message.reply_text(
            f"🕊️ *A Santa Paz de Deus!*\n\n"
            f"✅ *Cadastro recebido com sucesso:*\n`{texto}`\n\n"
            f"🗂️ Estamos em *fase de cadastro* dos irmãos responsáveis pelo acompanhamento.\n"
            f"📢 Assim que esta fase for concluída, os *alertas automáticos de consumo* começarão a ser enviados.\n\n"
            f"_Deus te abençoe!_ 🙌",
            parse_mode='Markdown'
        )
    else:
        await update.message.reply_text(
            "🕊️ *A Santa Paz de Deus!*\n\n"
            "❌ *Houve um problema ao processar seu cadastro!*\n\n"
            "Por favor, tente novamente mais tarde ou entre em contato com o administrador.\n\n"
            "_Deus te abençoe!_ 🙏",
            parse_mode='Markdown'
        )

def verificar_formato_cadastro(texto):
    """Verifica se o texto está no formato esperado para cadastro"""
    # Padrão esperado: BR21-0000 / Nome / Função
    padrao = r'^(BR\d{2}-\d{4})\s*\/\s*(.+?)\s*\/\s*(.+)$'
    return bool(re.match(padrao, texto, re.IGNORECASE))

async def processar_cadastro_simples(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Processa qualquer mensagem como um possível cadastro"""
    texto = update.message.text.strip()
    
    # Mostrar ID do usuário para ajudar na configuração
    user_id = update.effective_user.id
    print(f"Mensagem recebida do usuário ID: {user_id}, Username: @{update.effective_user.username}")
    
    # Verificar se parece com um formato de cadastro
    if verificar_formato_cadastro(texto):
        # Confirmar cadastro com botões
        keyboard = [
            [
                InlineKeyboardButton("✅ Confirmar Cadastro", callback_data="confirmar"),
                InlineKeyboardButton("❌ Cancelar", callback_data="cancelar")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Separar partes do cadastro para exibição
        partes = [p.strip() for p in texto.split('/')]
        codigo = partes[0].strip()
        nome = partes[1].strip() if len(partes) > 1 else ""
        funcao = partes[2].strip() if len(partes) > 2 else ""
        
        # Armazenar dados no contexto para uso posterior
        context.user_data['cadastro_pendente'] = texto
        
        await update.message.reply_text(
            "🕊️ *A Santa Paz de Deus!*\n\n"
            "📝 *Confirme os dados do cadastro:*\n\n"
            f"📍 *Código:* `{codigo}`\n"
            f"👤 *Nome:* `{nome}`\n"
            f"🔧 *Função:* `{funcao}`\n\n"
            "Os dados estão corretos?",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    else:
        # Se não parece um cadastro, envia a mensagem de boas-vindas
        await mensagem_boas_vindas(update, context)

async def processar_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Processa callbacks dos botões inline"""
    query = update.callback_query
    await query.answer()
    
    if query.data == "confirmar":
        # Recuperar dados de cadastro do contexto
        texto = context.user_data.get('cadastro_pendente', '')
        if not texto:
            await query.edit_message_text(
                "🕊️ *A Santa Paz de Deus!*\n\n"
                "❌ *Erro ao recuperar os dados!*\n\n"
                "Por favor, tente novamente.\n\n"
                "_Deus te abençoe!_ 🙏",
                parse_mode='Markdown'
            )
            return
        
        # Processar cadastro
        sucesso, status = salvar_cadastro(texto, update.effective_user.id, update.effective_user.username)
        
        if not sucesso and status == "duplicado":
            await query.edit_message_text(
                "🕊️ *A Santa Paz de Deus!*\n\n"
                "⚠️ *Atenção!*\n\n"
                f"O código da Casa de Oração já está cadastrado no sistema.\n\n"
                "Se precisar atualizar as informações, entre em contato com o administrador.\n\n"
                "_Deus te abençoe!_ 🙏",
                parse_mode='Markdown'
            )
            return
        
        if sucesso:
            await query.edit_message_text(
                f"🕊️ *A Santa Paz de Deus!*\n\n"
                f"✅ *Cadastro recebido com sucesso:*\n`{texto}`\n\n"
                f"🗂️ Estamos em *fase de cadastro* dos irmãos responsáveis pelo acompanhamento.\n"
                f"📢 Assim que esta fase for concluída, os *alertas automáticos de consumo* começarão a ser enviados.\n\n"
                f"_Deus te abençoe!_ 🙌",
                parse_mode='Markdown'
            )
        else:
            await query.edit_message_text(
                "🕊️ *A Santa Paz de Deus!*\n\n"
                "❌ *Houve um problema ao processar seu cadastro!*\n\n"
                "Por favor, tente novamente mais tarde ou entre em contato com o administrador.\n\n"
                "_Deus te abençoe!_ 🙏",
                parse_mode='Markdown'
            )
        
        # Limpar dados do contexto
        if 'cadastro_pendente' in context.user_data:
            del context.user_data['cadastro_pendente']
            
    elif query.data == "cancelar":
        await query.edit_message_text(
            "🕊️ *A Santa Paz de Deus!*\n\n"
            "❌ *Cadastro cancelado!*\n\n"
            "Você pode tentar novamente quando quiser.\n\n"
            "_Deus te abençoe!_ 🙏",
            parse_mode='Markdown'
        )
        
        # Limpar dados do contexto
        if 'cadastro_pendente' in context.user_data:
            del context.user_data['cadastro_pendente']
async def exportar_planilha(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Envia a planilha de cadastros como um arquivo (apenas para administradores)"""
    # Verificar se o usuário é administrador
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text(
            "🕊️ *A Santa Paz de Deus!*\n\n"
            "⚠️ *Acesso Negado*\n\n"
            "Você não tem permissão para acessar esta função.\n\n"
            "_Deus te abençoe!_ 🙏",
            parse_mode='Markdown'
        )
        return
    
    try:
        if not os.path.exists(EXCEL_FILE):
            await update.message.reply_text(
                "🕊️ *A Santa Paz de Deus!*\n\n"
                "❌ Nenhum arquivo de cadastro encontrado.\n\n"
                "_Deus te abençoe!_ 🙏",
                parse_mode='Markdown'
            )
            return
            
        # Enviar o arquivo
        await update.message.reply_document(
            document=open(EXCEL_FILE, 'rb'),
            filename=EXCEL_FILE,
            caption="🕊️ *A Santa Paz de Deus!*\n\nAqui está o arquivo com todos os cadastros de responsáveis.\n\n_Deus te abençoe!_ 🙏",
            parse_mode='Markdown'
        )
        
        print(f"Planilha enviada para o administrador: {update.effective_user.id} - {update.effective_user.username}")
        
    except Exception as e:
        await update.message.reply_text(
            "🕊️ *A Santa Paz de Deus!*\n\n"
            f"❌ Erro ao enviar planilha: {str(e)}\n\n"
            "_Deus te abençoe!_ 🙏",
            parse_mode='Markdown'
        )

# Comando para listar todos os cadastros (apenas para administradores)
async def listar_cadastros(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Lista todos os cadastros (apenas para administradores)"""
    # Verificar se o usuário é administrador
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text(
            "🕊️ *A Santa Paz de Deus!*\n\n"
            "⚠️ *Acesso Negado*\n\n"
            "Você não tem permissão para acessar esta função.\n\n"
            "_Deus te abençoe!_ 🙏",
            parse_mode='Markdown'
        )
        return
    
    try:
        if not os.path.exists(EXCEL_FILE):
            await update.message.reply_text(
                "🕊️ *A Santa Paz de Deus!*\n\n"
                "❌ Nenhum cadastro encontrado.\n\n"
                "_Deus te abençoe!_ 🙏",
                parse_mode='Markdown'
            )
            return
            
        df = pd.read_excel(EXCEL_FILE)
        
        if df.empty:
            await update.message.reply_text(
                "🕊️ *A Santa Paz de Deus!*\n\n"
                "❌ Nenhum cadastro encontrado.\n\n"
                "_Deus te abençoe!_ 🙏",
                parse_mode='Markdown'
            )
            return
        
        # Formatar mensagem com os cadastros
        mensagem = "🕊️ *A Santa Paz de Deus!*\n\n"
        mensagem += "📋 *Lista de Cadastros:*\n\n"
        
        for i, row in df.iterrows():
            mensagem += f"📍 *{row['Codigo_Casa']}*\n"
            mensagem += f"👤 Nome: {row['Nome']}\n"
            mensagem += f"🔧 Função: {row['Funcao']}\n"
            mensagem += f"📅 Data: {row['Data_Cadastro']}\n\n"
        
        # Enviar mensagem (possivelmente dividida se for muito grande)
        if len(mensagem) > 4096:
            partes = [mensagem[i:i+4096] for i in range(0, len(mensagem), 4096)]
            for parte in partes:
                await update.message.reply_text(parte, parse_mode='Markdown')
        else:
            await update.message.reply_text(mensagem, parse_mode='Markdown')
            
    except Exception as e:
        await update.message.reply_text(
            "🕊️ *A Santa Paz de Deus!*\n\n"
            f"❌ Erro ao listar cadastros: {str(e)}\n\n"
            "_Deus te abençoe!_ 🙏",
            parse_mode='Markdown'
        )

# Comando para limpar todos os cadastros (apenas para administradores)
async def limpar_cadastros(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Remove todos os cadastros (apenas para administradores)"""
    # Verificar se o usuário é administrador
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text(
            "🕊️ *A Santa Paz de Deus!*\n\n"
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
        "🕊️ *A Santa Paz de Deus!*\n\n"
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
    
    if query.data == "confirmar_limpar":
        try:
            if os.path.exists(EXCEL_FILE):
                # Fazer backup antes de limpar
                timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
                backup_file = f"backup_{timestamp}_{EXCEL_FILE}"
                
                # Copiar arquivo para backup
                df = pd.read_excel(EXCEL_FILE)
                df.to_excel(backup_file, index=False)
                
                # Criar planilha vazia
                inicializar_planilha()
                
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
            "🕊️ *A Santa Paz de Deus!*\n\n"
            "✅ *Operação cancelada!*\n\n"
            "Nenhum cadastro foi removido.\n\n"
            "_Deus te abençoe!_ 🙏",
            parse_mode='Markdown'
        )

# Comando para adicionar um administrador (apenas para administradores)
async def adicionar_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Adiciona um novo administrador (apenas para administradores)"""
    global ADMIN_IDS  # Declaração global deve vir primeiro
    
    # Verificar se o usuário é administrador
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text(
            "🕊️ *A Santa Paz de Deus!*\n\n"
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
            "🕊️ *A Santa Paz de Deus!*\n\n"
            "❌ *Formato inválido!*\n\n"
            "Use: `/admin_add ID_DO_USUARIO`\n"
            "Exemplo: `/admin_add 123456789`\n\n"
            "_Deus te abençoe!_ 🙏",
            parse_mode='Markdown'
        )
        return
    
    # Obter ID do novo administrador
    novo_admin_id = int(args[0])
    
    # Verificar se já é administrador
    if novo_admin_id in ADMIN_IDS:
        await update.message.reply_text(
            "🕊️ *A Santa Paz de Deus!*\n\n"
            "ℹ️ Este usuário já é um administrador.\n\n"
            "_Deus te abençoe!_ 🙏",
            parse_mode='Markdown'
        )
        return
    
    # Adicionar ao arquivo de configuração
    try:
        # Cria uma cópia da lista global para modificação
        admin_ids_atualizados = ADMIN_IDS.copy()
        admin_ids_atualizados.append(novo_admin_id)
        
        # Atualiza a lista global
        ADMIN_IDS = admin_ids_atualizados
        
        # Salvar em um arquivo para persistência (opcional)
        with open('admin_ids.txt', 'w') as f:
            for admin_id in ADMIN_IDS:
                f.write(f"{admin_id}\n")
        
        await update.message.reply_text(
            "🕊️ *A Santa Paz de Deus!*\n\n"
            f"✅ Administrador adicionado com sucesso: `{novo_admin_id}`\n\n"
            "_Deus te abençoe!_ 🙏",
            parse_mode='Markdown'
        )
    except Exception as e:
        await update.message.reply_text(
            "🕊️ *A Santa Paz de Deus!*\n\n"
            f"❌ Erro ao adicionar administrador: {str(e)}\n\n"
            "_Deus te abençoe!_ 🙏",
            parse_mode='Markdown'
        )

# Comando para mostrar seu próprio ID
async def mostrar_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Mostra o ID do usuário que enviou a mensagem"""
    user_id = update.effective_user.id
    username = update.effective_user.username or "Sem username"
    first_name = update.effective_user.first_name or "Sem nome"
    
    await update.message.reply_text(
        f"🕊️ *A Santa Paz de Deus!*\n\n"
        f"📋 *Suas informações:*\n\n"
        f"🆔 *Seu ID:* `{user_id}`\n"
        f"👤 *Username:* @{username}\n"
        f"📝 *Nome:* {first_name}\n\n"
        f"_Guarde seu ID para configurar como administrador!_",
        parse_mode='Markdown'
    )

# Função para carregar IDs de administradores de um arquivo
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
    except Exception as e:
        print(f"Erro ao carregar IDs de administradores: {e}")

def main():
    # Carregar IDs de administradores
    carregar_admin_ids()
    
    # Inicializar planilha
    inicializar_planilha()
    
    # Criar aplicação
    application = Application.builder().token(TOKEN).build()
    
    # Handlers para comandos básicos
    application.add_handler(CommandHandler("start", mensagem_boas_vindas))
    application.add_handler(CommandHandler("cadastro", cadastro))
    application.add_handler(CommandHandler("meu_id", mostrar_id))
    
    # Handlers para comandos administrativos
    application.add_handler(CommandHandler("exportar", exportar_planilha))
    application.add_handler(CommandHandler("listar", listar_cadastros))
    application.add_handler(CommandHandler("limpar", limpar_cadastros))
    application.add_handler(CommandHandler("admin_add", adicionar_admin))
    
    # Handler para mensagens de texto
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, processar_cadastro_simples))
    
    # Handlers para callbacks
    application.add_handler(CallbackQueryHandler(processar_callback, pattern='^(confirmar|cancelar)))
    application.add_handler(CallbackQueryHandler(processar_callback_admin, pattern='^(confirmar_limpar|cancelar_limpar)))
    
    # Iniciar o bot com polling
    print("Bot iniciado!")
    application.run_polling()

if __name__ == '__main__':
    main()            
