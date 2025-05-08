from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import os

TOKEN = "7773179413:AAFdu3eFlWC7pF4Q7KhFcKvPv8aMJ1N0DV4"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "A Paz de Deus!\n\nPor favor envie sua mensagem com o seguinte formato:\n\n/cadastro BR21-0000 / João da Silva / Cooperador"
    )

async def cadastro(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texto = update.message.text.replace('/cadastro', '').strip()
    await update.message.reply_text(f"Cadastro recebido: {texto}\n\nDeus abençoe!")

def main():
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("cadastro", cadastro))
    # Usar polling em vez de webhook
    application.run_polling()

if __name__ == '__main__':
    main()
