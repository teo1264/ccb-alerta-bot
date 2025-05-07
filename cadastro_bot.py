from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import os

TOKEN = os.getenv("BOT_TOKEN")

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

    application.run_webhook(
        listen="0.0.0.0",
        port=10000,
        webhook_url="https://ccb-alerta-bot.onrender.com/telegram"
    )

if __name__ == '__main__':
    main()
