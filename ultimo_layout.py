import os

try:
    from config import PASTA_TEMP
except Exception:
    PASTA_TEMP = "/tmp/bot_aviso_vip"


ARQUIVO_ULTIMO_LAYOUT = os.path.join(PASTA_TEMP, "ultimo_layout.txt")


def ler_ultimo_layout():
    try:
        if not os.path.exists(ARQUIVO_ULTIMO_LAYOUT):
            return None

        with open(ARQUIVO_ULTIMO_LAYOUT, "r", encoding="utf-8") as arquivo:
            return arquivo.read().strip() or None

    except Exception:
        return None


def salvar_ultimo_layout(nome_layout):
    try:
        os.makedirs(PASTA_TEMP, exist_ok=True)

        with open(ARQUIVO_ULTIMO_LAYOUT, "w", encoding="utf-8") as arquivo:
            arquivo.write(nome_layout)

    except Exception as erro:
        print(f"Não foi possível salvar último layout: {erro}")