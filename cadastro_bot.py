from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import os
import pandas as pd
from datetime import datetime

TOKEN = "7773179413:AAHqJp-NBPPs6YrSV1kB5-q4vkV3tjDFyy4"
EXCEL_FILE = "responsaveis_casas.xlsx"

async def mensagem_boas_vindas(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Responde a qualquer mensagem com uma saudação e instruções"""
    await update.message.reply_text(
        "A Santa Paz de Deus!\n\n"
        "Este é o sistema gratuito de alertas automáticos para as Casas de Oração da CCB ADM Mauá.\n\n"
        "Você receberá alertas sobre:\n"
        "• Aumentos no consumo de água (BRK) e energia (ENEL)\n"
        "• Futuramente Relatórios de compensação para casas com sistema fotovoltaico\n\n"
        "Para se cadastrar, envie uma mensagem no formato:\n"
        "BR21-0000 / Seu Nome Completo / Sua Função\n\n"
        "Exemplo: BR21-0270 / João Silva / Cooperador\n\n"
        "Este serviço é destinado a Cooperadores, Encarregados de Manutenção, Responsáveis pela Escrita e demais irmãos do ministério.\n\n"
        "Deus o abençoe!"
    )

async def cadastro(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Processa um cadastro enviado com /cadastro"""
    texto = update.message.text.replace('/cadastro', '').strip()
    
    # Verificar se há dados após o comando
    if not texto:
        await mensagem_boas_vindas(update, context)
        return
    
    # Salvar os dados
    salvar_cadastro(texto, update.effective_user.id, update.effective_user.username)
    
    await update.message.reply_text(
        f"A Santa Paz de Deus!\n\n"
        f"Cadastro recebido com sucesso:\n{texto}\n\n"
        f"Você está registrado para receber alertas de consumo da sua Casa de Oração.\n\n"
        f"Fase em Desenvolvimento!"
        f"Deus o abençoe!"
    )

async def processar_cadastro_simples(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Processa qualquer mensagem como um possível cadastro"""
    texto = update.message.text.strip()
    
    # Verificar se parece com um formato de cadastro
    if "/" in texto and ("BR" in texto.upper() or "21-" in texto):
        # Salvar os dados
        salvar_cadastro(texto, update.effective_user.id, update.effective_user.username)
        
        await update.message.reply_text(
            f"A Santa Paz de Deus!\n\n"
            f"Cadastro recebido com sucesso:\n{texto}\n\n"
            f"Você está registrado para receber alertas de consumo da casa de oração.\n\n"
            f"Fase em Desenvolvimento!"
            f"Deus o abençoe!"
        )
    else:
        # Se não parece um cadastro, envia a mensagem de boas-vindas
        await mensagem_boas_vindas(update, context)

def salvar_cadastro(texto, user_id, username):
    """Salva os dados do cadastro na planilha Excel"""
    try:
        # Separar os dados pelo delimitador "/"
        partes = [p.strip() for p in texto.split('/')]
        
        # Garantir que temos pelo menos 3 partes (código, nome, função)
        if len(partes) >= 3:
            codigo_casa = partes[0]
            nome = partes[1]
            funcao = partes[2]
        else:
            # Se não tiver 3 partes, use o texto completo e deixe campos em branco
            codigo_casa = texto
            nome = ""
            funcao = ""
        
        # Criar DataFrame com os dados
        data = {
            'Codigo_Casa': [codigo_casa],
            'Nome': [nome],
            'Funcao': [funcao],
            'User_ID': [user_id],
            'Username': [username],
            'Data_Cadastro': [datetime.now().strftime("%d/%m/%Y %H:%M:%S")]
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
        return True
    except Exception as e:
        print(f"Erro ao salvar cadastro: {e}")
        return False

def main():
    application = Application.builder().token(TOKEN).build()
    
    # Mantém o handler para /start para compatibilidade
    application.add_handler(CommandHandler("start", mensagem_boas_vindas))
    
    # Mantém o handler para /cadastro para compatibilidade
    application.add_handler(CommandHandler("cadastro", cadastro))
    
    # Adiciona um handler para qualquer mensagem de texto
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, processar_cadastro_simples))
    
    # Usar polling
    application.run_polling()

if __name__ == '__main__':
    main()
