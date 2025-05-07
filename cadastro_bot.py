from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes
from telegram.ext import filters
import pandas as pd
import os

TOKEN = '7773179413:AAFkpZxyhs4s91mIbWeYdFQ7UWCXfQGVOn0'
PLANILHA = 'responsaveis_casas.xlsx'

async def registrar(update, context: ContextTypes.DEFAULT_TYPE):
    texto = update.message.text.strip()
    chat_id = update.effective_chat.id

    try:
        casa, nome, cargo = [parte.strip() for parte in texto.split("/")]
    except ValueError:
        await context.bot.send_message(chat_id=chat_id, text=(
            "Formato inválido. Envie assim:\n"
            "`BR 21-0275 | João Silva | Cooperador`"
        ), parse_mode='Markdown')
        return

    # Verifica se a planilha já existe
    if os.path.exists(PLANILHA):
        df = pd.read_excel(PLANILHA)
    else:
        df = pd.DataFrame(columns=["Casa Código", "Nome Responsável", "Cargo", "Chat ID"])

    # Verifica se já está registrado
    ja_registrado = (df["Chat ID"] == chat_id).any()
    if ja_registrado:
        await context.bot.send_message(chat_id=chat_id, text="Seu cadastro já está registrado.")
        return

    # Adiciona nova linha
    nova_linha = {
        "Casa Código": casa,
        "Nome Responsável": nome,
        "Cargo": cargo,
        "Chat ID": chat_id
    }
    df = pd.concat([df, pd.DataFrame([nova_linha])], ignore_index=True)
    df.to_excel(PLANILHA, index=False)

    await context.bot.send_message(chat_id=chat_id, text="Cadastro realizado com sucesso. Deus abençoe!")

app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), registrar))

print("Bot ativo e aguardando registros...")
app.run_polling()
