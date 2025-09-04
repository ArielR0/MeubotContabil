import re

# -------------------- Validação de entrada --------------------

def validar_valor(valor):
    """
    Garante que o valor seja um número positivo.
    """
    try:
        v = float(valor)
        if v < 0:
            return False
        return True
    except ValueError:
        return False


def validar_tipo(tipo):
    """
    Garante que o tipo seja 'receita' ou 'despesa'.
    """
    return tipo.lower() in ["receita", "despesa"]


def validar_categoria(categoria):
    """
    Evita caracteres suspeitos na categoria para prevenir injeção.
    Aceita apenas letras, números e espaços.
    """
    if not categoria:
        return False
    if re.fullmatch(r"[A-Za-z0-9\s]+", categoria):
        return True
    return False


# -------------------- Filtragem de mensagens --------------------

def sanitizar_texto(texto):
    """
    Remove caracteres que podem ser usados para exploits ou injeções.
    """

    texto = re.sub(r"<.*?>", "", texto)
    texto = re.sub(r"script", "", texto, flags=re.IGNORECASE)
    texto = re.sub(r"[^\w\s\-.,]", "", texto)
    return texto.strip()


# -------------------- Controle de acesso --------------------

def verificar_usuario(user_id, lista_usuarios_permitidos=None):
    """
    Opcional: verifica se o user_id está autorizado.
    """
    if lista_usuarios_permitidos is None:
        return True  
    return user_id in lista_usuarios_permitidos


# -------------------- Segurança para variáveis sensíveis --------------------

def esconder_chave(chave, mostrar_ultimos=4):
    """
    Retorna a chave parcialmente mascarada para logs.
    """
    if not chave or len(chave) <= mostrar_ultimos:
        return "*" * len(chave)
    return "*" * (len(chave) - mostrar_ultimos) + chave[-mostrar_ultimos:]

