import os
import json
from datetime import datetime

from config import ARQUIVO_HISTORICO, PASTA_DATA


def carregar_historico():
    os.makedirs(PASTA_DATA, exist_ok=True)

    if not os.path.exists(ARQUIVO_HISTORICO):
        return {
            "imagens_usadas": []
        }

    with open(ARQUIVO_HISTORICO, "r", encoding="utf-8") as arquivo:
        return json.load(arquivo)


def salvar_historico(historico):
    os.makedirs(PASTA_DATA, exist_ok=True)

    with open(ARQUIVO_HISTORICO, "w", encoding="utf-8") as arquivo:
        json.dump(historico, arquivo, ensure_ascii=False, indent=2)


def filtrar_nao_usadas(imagens):
    historico = carregar_historico()
    usadas = set(historico.get("imagens_usadas", []))

    return [
        img for img in imagens
        if img.get("id") not in usadas
    ]


def registrar_usadas(imagens):
    historico = carregar_historico()
    usadas = set(historico.get("imagens_usadas", []))

    for img in imagens:
        if img.get("id"):
            usadas.add(img.get("id"))

    historico["imagens_usadas"] = list(usadas)
    historico["ultima_atualizacao"] = datetime.now().isoformat()

    salvar_historico(historico)