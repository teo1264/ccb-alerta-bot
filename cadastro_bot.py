from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import os

TOKEN = "7773179413:AAFdu3eFlWC7pF4Q7KhFcKvPv8aMJ1N0DV4"

async def mensagem_boas_vindas(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Responde a qualquer mensagem com uma saudação e instruções"""
    await update.message.reply_text(
        "A Santa Paz de Deus!\n\n"
        "Este é o sistema gratuito de alertas automáticos para casas de oração da CCB.\n\n"
        "Você receberá alertas sobre:\n"
        "• Aumentos no consumo de água (BRK) e energia (ENEL)\n"
        "• Relatórios de compensação para casas com sistema fotovoltaico\n\n"
        "Para se cadastrar, envie uma mensagem no formato:\n"
        "BR21-0000 / Seu Nome Completo / Sua Função\n\n"
        "Exemplo: BR21-0275 / João Silva / Cooperador\n\n"
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
    
    await update.message.reply_text(
        f"A Santa Paz de Deus!\n\n"
        f"Cadastro recebido com sucesso:\n{texto}\n\n"
        f"Você está registrado para receber alertas de consumo da casa de oração.\n\n"
        f"Deus o abençoe!"
    )
    # Aqui você adicionaria o código para salvar os dados

async def processar_cadastro_simples(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Processa qualquer mensagem como um possível cadastro"""
    texto = update.message.text.strip()
    
    # Verificar se parece com um formato de cadastro
    if "/" in texto and ("BR" in texto.upper() or "21-" in texto):
        await update.message.reply_text(
            f"A Santa Paz de Deus!\n\n"
            f"Cadastro recebido com sucesso:\n{texto}\n\n"
            f"Você está registrado para receber alertas de consumo da casa de oração.\n\n"
            f"Deus o abençoe!"
        )
        # Aqui você adicionaria o código para salvar os dados
    else:
        # Se não parece um cadastro, envia a mensagem de boas-vindas
        await mensagem_boas_vindas(update, context)

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
