from telegram import Update
from telegram.ext import ContextTypes
import csv
from io import StringIO
from db import get_transactions, get_user_id

async def exportar_planilha(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user_id = get_user_id(chat_id)

    if not user_id:
        await update.message.reply_text("Use o bot primeiro para registrar suas transações antes de exportar.")
        return

    transacoes = get_transactions(user_id)

    if not transacoes:
        await update.message.reply_text("Você não tem transações para exportar.")
        return

    # Criar CSV na memória
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(["Data", "Categoria", "Tipo", "Valor"])
    for t in transacoes:
        writer.writerow([t["data"], t["categoria"], t["tipo"], t["valor"]])

    output.seek(0)
    await update.message.reply_document(document=output, filename="transacoes.csv")