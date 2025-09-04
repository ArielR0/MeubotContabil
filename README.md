# 💰 FinançasBot - Controle suas despesas e receitas no Telegram

Um bot **simples, prático e funcional** para controlar seu dinheiro diretamente no Telegram!  
Adicione transações, veja saldo, gere gráficos e resumo semanal, e até exporte tudo para Excel.

---

## 📹 Demonstração do Bot

Veja o bot em ação (vídeo curto de **~35 segundos**) mostrando as principais funcionalidades:

<video src="assets/readme.mp4" controls width="500"></video>

No vídeo você vê:  
1. Adicionando receita: `adicionar 5000 salario receita`  
2. Adicionando despesa: `adicionar 50 alimentação despesa`  
3. Verificando saldo: `saldo`  
4. Gerando gráfico: `grafico`  
5. Resumo semanal: `resumo`  
6. Exportando planilha: `exportar excel`  

---

## ⚡ Funcionalidades

- Adicionar **receitas** e **despesas** por categoria  
- Ver **saldo atual** a qualquer momento  
- Gerar **gráficos de gastos por categoria**  
- Resumo **semanal de despesas**  
- Exportar todas as transações para **planilha CSV/Excel**  
- Comandos simples e intuitivos no Telegram  

---

## 🛠 Como usar

1. Adicione o bot no Telegram  
2. Comece digitando mensagens como:
   
 -adicionar 5000 salario receita
 -adicionar 50 alimentação despesa
 -saldo
 -grafico
 -resumo
 -exportar excel
 -zerar despesas

4. O bot irá responder com mensagens claras e atualizar seu saldo automaticamente  

---

## 💻 Tecnologias

- Python 3.11  
- Telegram Bot API (`python-telegram-bot`)  
- PostgreSQL / Supabase  
- Matplotlib (para gráficos)  
- CSV para exportação de planilhas  

---

## 📂 Estrutura do Projeto
financasbot/
├─ db.py # Conexão e funções de banco de dados

├─ bot.py # Script principal do bot

├─ services/

│ ├─ extra.py # Normalização de valores e exportação

│ └─ security.py # Validações de entradas do usuário

├─ config.py # Token e configurações

├─ assests/

│ ├─ reame.mp4 #video para demonstração

└─ README.md # Este arquivo

---

## 🚀 Observações

- O vídeo é **curto** (30-40s) para mostrar rapidamente o bot funcionando  
- Funciona **direto no Telegram**, sem necessidade de interface web  
- Permite que recrutadores vejam seu **controle de dados financeiros e interface amigável**  

---
