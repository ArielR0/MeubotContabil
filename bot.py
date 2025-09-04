from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters
from db import (
    add_user,
    get_user_id,
    add_transaction,
    get_balance,
    get_transactions,
    get_transactions_week,
    get_alert,
    set_alert,
    remove_alert,
)
import matplotlib.pyplot as plt
from io import BytesIO
from config import BOT_TOKEN
from services.extra import exportar_planilha
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
        await update.message.reply_text(f"💰 Seu saldo atual é: R$ {saldo_atual:.2f}")
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
            f"Olá {update.effective_user.first_name}! Quer adicionar uma transação ou ver seu saldo?"
        )

    elif "saldo" in texto:
        saldo_atual = get_balance(user_id)
        await update.message.reply_text(f"💰 Seu saldo atual é: R$ {saldo_atual:.2f}")

    elif "adicionar" in texto:
        partes = texto.split()
        if len(partes) >= 4:
            try:
                valor = float(partes[1])
                tipo = partes[-1].lower()
                categoria = " ".join(partes[2:-1])

                if tipo not in ["receita", "despesa"]:
                    await update.message.reply_text("Tipo inválido! Use 'receita' ou 'despesa'.")
                    return

                add_transaction(user_id, valor, categoria, tipo)
                await update.message.reply_text(
                    f"✅ {tipo.capitalize()} de R$ {valor:.2f} adicionada na categoria '{categoria}'!"
                )

                # -------------------- ALERTA -------------------- #
                if tipo == "despesa":
                    alerta = get_alert(user_id, categoria)
                    if alerta and valor > alerta["limite"]:
                        await update.message.reply_text(
                            f"⚠️ Atenção! Você ultrapassou o limite de R$ {alerta['limite']} na categoria '{categoria}'"
                        )

            except ValueError:
                await update.message.reply_text(
                    "Não consegui entender o valor. Exemplo: adicionar 50 alimentação despesa"
                )
        else:
            await update.message.reply_text("Formato correto: adicionar <valor> <categoria> <tipo>")

    elif "limite" in texto:
        partes = texto.split()
        if len(partes) >= 2:
            if partes[1].lower() == "remover":
                categoria = " ".join(partes[2:]) if len(partes) > 2 else None
                remove_alert(user_id, categoria)
                msg = "✅ Limite removido"
                if categoria:
                    msg += f" para a categoria '{categoria}'"
                await update.message.reply_text(msg)
            else:
                try:
                    valor = float(partes[1])
                    categoria = " ".join(partes[2:]) if len(partes) > 2 else None
                    set_alert(user_id, valor, categoria)
                    msg = f"✅ Limite de R$ {valor:.2f} "
                    msg += f"para categoria '{categoria}'" if categoria else "para todas as despesas"
                    await update.message.reply_text(msg)
                except ValueError:
                    await update.message.reply_text("Não consegui entender o valor do limite.")
        else:
            await update.message.reply_text(
                "Formato correto: limite <valor> <categoria opcional> ou limite remover <categoria opcional>"
            )

    elif "grafico" in texto or "gráfico" in texto:
        await gerar_grafico(update, context)

    elif "resumo" in texto:
        await resumo_semanal(update, context)

    elif "exportar excel" in texto or "exportar planilha" in texto:
        await exportar_planilha(update, context)

    else:
        await update.message.reply_text(
            "Desculpe, não entendi 😅. Você pode me mandar 'saldo', 'adicionar <valor> <categoria> <tipo>', 'grafico' ou 'resumo' para ver seus gastos."
        )


# -------------------- GRÁFICOS -------------------- #
async def gerar_grafico(update, context):
    chat_id = update.effective_chat.id
    user_id = get_user_id(chat_id)

    if not user_id:
        await update.message.reply_text("Usuário não encontrado. Use /start primeiro.")
        return

    transacoes = get_transactions(user_id)
    despesas = [t for t in transacoes if t['tipo'] == 'despesa']

    if not despesas:
        await update.message.reply_text("Você ainda não tem despesas cadastradas.")
        return

    categorias = {}
    for d in despesas:
        categorias[d['categoria']] = categorias.get(d['categoria'], 0) + float(d['valor'])

    labels = list(categorias.keys())
    valores = list(categorias.values())

    plt.figure(figsize=(6, 6))
    plt.pie(valores, labels=labels, autopct="%1.1f%%", startangle=140)
    plt.title("Gastos por Categoria")

    buffer = BytesIO()
    plt.savefig(buffer, format="png")
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
    despesas = [t for t in transacoes if t["tipo"] == "despesa"]

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