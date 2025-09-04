from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters
from db import (
    add_user,
    get_user_id,
    add_transaction,
    get_balance,
    get_transactions,
    get_transactions_week,
    supabase
)
import matplotlib.pyplot as plt
from io import BytesIO
from config import BOT_TOKEN
from services.extra import exportar_planilha
from services.extra import normalizar_valor
from services.security import validar_valor, validar_tipo, validar_categoria, sanitizar_texto


# -------------------- COMANDOS DO BOT -------------------- #
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    nome = update.effective_user.first_name
    user_id = add_user(chat_id, nome)

    mensagem = f"""
Olá {nome}! 👋
Seu usuário foi cadastrado com sucesso. ID: {user_id}

Aqui estão algumas coisas que você pode fazer:
💰 Ver saldo: digite 'saldo'
➕ Adicionar transação: digite 'adicionar <valor> <categoria> <tipo>'
Ex: adicionar 50 alimentacao despesa
📊 Ver gráfico de gastos: digite 'grafico'

Vamos começar? 😄
"""
    await update.message.reply_text(mensagem)


async def saldo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user_id = get_user_id(chat_id)
    if user_id:
        saldo_atual = get_balance(user_id)
        await update.message.reply_text(f"💰 Seu saldo atual é: R$ {saldo_atual:.3f}")
    else:
        await update.message.reply_text("Usuário não encontrado. Use /start primeiro.")


async def adicionar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user_id = get_user_id(chat_id)
    if not user_id:
        await update.message.reply_text("Usuário não encontrado. Use /start primeiro.")
        return

    try:
        valor = float(context.args[0])
        categoria = context.args[1]
        tipo = context.args[2].lower()

        # Validações
        if not validar_valor(valor):
            await update.message.reply_text("Valor inválido!")
            return
        if not validar_tipo(tipo):
            await update.message.reply_text("Tipo inválido! Use 'receita' ou 'despesa'.")
            return
        if not validar_categoria(categoria):
            await update.message.reply_text("Categoria inválida! Use apenas letras e números.")
            return

        add_transaction(user_id, valor, categoria, tipo)
        await update.message.reply_text(f"✅ {tipo.capitalize()} de R$ {valor:.2f} adicionada na categoria '{categoria}'!")

    except (IndexError, ValueError):
        await update.message.reply_text("Uso correto: /adicionar <valor> <categoria> <tipo>")


# -------------------- RESPOSTAS NATURAIS -------------------- #
async def responder(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texto = update.message.text.lower()
    chat_id = update.effective_chat.id
    user_id = get_user_id(chat_id)

    # usuário novo
    if not user_id:
        nome = update.effective_user.first_name
        user_id = add_user(chat_id, nome)
        mensagem = f"""
Olá {nome}! 👋
Seu usuário foi cadastrado com sucesso. ID: {user_id}

Aqui estão algumas coisas que você pode fazer:
💰 Ver saldo: digite 'saldo'
➕ Adicionar transação: digite 'adicionar <valor> <categoria> <tipo>'
Ex: adicionar 50 alimentacao despesa
📊 Ver gráfico de gastos: digite 'grafico'

Vamos começar? 😄
"""
        await update.message.reply_text(mensagem)
        return

    # ---------------- Comandos do usuário ---------------- #
    if "oi" in texto or "olá" in texto:
     await update.message.reply_text(
        f"Olá {update.effective_user.first_name}! 👋 Que bom te ver por aqui! 😄\n\n"
        "Você pode começar registrando suas despesas ou receitas, "
        "ou verificando seu saldo atual. Alguns comandos para te ajudar 😀:\n\n"
        "- adicionar 50(O valor que quiser) salário receita\n\n"
        "- adicionar 50 alimentação despesa\n\n"
        "- saldo\n\n"
        "- gráfico\n\n"
        "- zerar saldo\n\n"
        "Vamos lá?"
    )

    elif "zerar saldo" in texto:
        saldo_atual = get_balance(user_id)
        if saldo_atual == 0:
            await update.message.reply_text("✅ Seu saldo já está zerado!")
            return

       
        add_transaction(user_id, saldo_atual, "Ajuste saldo", "despesa")
        await update.message.reply_text(
            f"✅ Saldo zerado! Uma despesa de R$ {saldo_atual:.2f} foi registrada como ajuste."
        )


    elif "saldo" in texto:
        saldo_atual = get_balance(user_id)
        await update.message.reply_text(f"💰 Seu saldo atual é: R$ {saldo_atual:.2f}")

    elif "adicionar" in texto:
        partes = texto.split()
        if len(partes) >= 4:
            entrada_valor = partes[1]  
            valor = normalizar_valor(entrada_valor)
            if valor is None:
                await update.message.reply_text(
                    "Não consegui entender o valor. Use apenas números, ex: 50, 50.0 ou 50,50"
                )
                return

            tipo = partes[-1].lower()
            if tipo not in ["receita", "despesa"]:
                await update.message.reply_text("Tipo inválido! Use 'receita' ou 'despesa'.")
                return

            categoria = " ".join(partes[2:-1])

            add_transaction(user_id, valor, categoria, tipo)

            await update.message.reply_text(
                f"✅ {tipo.capitalize()} de R$ {entrada_valor} adicionada na categoria '{categoria}'!"
            )
        else:
            await update.message.reply_text("Formato correto: adicionar <valor> <categoria> <tipo>")

    elif "zerar despesas" in texto:
        transacoes = get_transactions(user_id)
        despesas = [t for t in transacoes if t['tipo'] == 'despesa' and t['categoria'].lower() != "ajuste saldo"]

        if not despesas:
            await update.message.reply_text("✅ Você não tem despesas cadastradas para zerar.")
            return

        # Deleta todas as despesas (exceto ajustes)
        for d in despesas:
            supabase.table("transactions").delete().eq("id", d['id']).execute()

        await update.message.reply_text(f"✅ Todas as suas despesas ({len(despesas)}) foram zeradas!")


    elif "grafico" in texto or "gráfico" in texto:
        await gerar_grafico(update, context)

    elif "resumo" in texto:
        await resumo_semanal(update, context)

    elif "exportar excel" in texto or "exportar planilha" in texto:
        await exportar_planilha(update, context)

    else:
        await update.message.reply_text(
            "Desculpe, não entendi 😅. Você pode me mandar 'saldo', 'adicionar <valor> <categoria> <tipo>', 'grafico', 'resumo' ou 'zerar despesas' para ver seus gastos."
        )


# -------------------- GRÁFICOS -------------------- #
async def gerar_grafico(update, context):
    chat_id = update.effective_chat.id
    user_id = get_user_id(chat_id)

    if not user_id:
        await update.message.reply_text("Usuário não encontrado. Use o bot primeiro.")
        return

    transacoes = get_transactions(user_id)
    # Filtra apenas despesas "reais", ignorando ajustes ou transações de teste
    despesas = [
        t for t in transacoes 
        if t['tipo'] == 'despesa' and t['categoria'].lower() != "ajuste saldo" and float(t['valor']) > 0
    ]

    if not despesas:
        await update.message.reply_text("Você ainda não tem despesas válidas cadastradas.")
        return

    categorias = {}
    for d in despesas:
        cat = d['categoria'].strip()
        categorias[cat] = categorias.get(cat, 0) + float(d['valor'])

    labels = list(categorias.keys())
    valores = list(categorias.values())

    plt.figure(figsize=(7, 7))
    plt.pie(valores, labels=None, autopct="%1.1f%%", startangle=90)
    plt.axis('equal')  # Mantém o gráfico redondo
    plt.title("Gastos por Categoria")

    # Legenda à direita, quebrando nomes longos
    plt.legend(
        [f"{label}: R$ {val:.2f}" for label, val in zip(labels, valores)], 
        bbox_to_anchor=(1, 0.5), loc="center left"
    )

    buffer = BytesIO()
    plt.savefig(buffer, format="png", bbox_inches="tight")
    buffer.seek(0)
    plt.close()

    await update.message.reply_photo(photo=buffer)
# -------------------- RESUMO SEMANAL -------------------- #
async def resumo_semanal(update, context):
    chat_id = update.effective_chat.id
    user_id = get_user_id(chat_id)

    if not user_id:
        nome = update.effective_user.first_name
        user_id = add_user(chat_id, nome)
        await update.message.reply_text(
            f"Olá {nome}! Você foi cadastrado. Use 'adicionar' para registrar suas transações."
        )
        return

    saldo_atual = get_balance(user_id)
    transacoes = get_transactions_week(user_id)
    despesas = [t for t in transacoes if t["tipo"] == "despesa" and t["categoria"].lower() != "ajuste saldo"]

    if despesas:
        resumo = {}
        for d in despesas:
            resumo[d["categoria"]] = resumo.get(d["categoria"], 0) + float(d["valor"])
        mensagem = f"💰 Seu saldo atual: R$ {saldo_atual:.2f}\n\n📊 Gastos da semana:\n"
        for cat, val in resumo.items():
            mensagem += f"- {cat}: R$ {val:.2f}\n"
    else:
        mensagem = f"💰 Seu saldo atual: R$ {saldo_atual:.2f}\n\nVocê não teve despesas esta semana."

    await update.message.reply_text(mensagem)


# -------------------- BOT -------------------- #
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, responder))

    print("🤖 Bot iniciado...")
    app.run_polling()


if __name__ == "__main__":
    main()