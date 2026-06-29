import os
import requests
from config import (
    GOOGLE_API_KEY,
    GOOGLE_DRIVE_FOLDER_ID,
    PASTA_PRINTS,
)


def listar_imagens_recentes(limite=25):
    url = "https://www.googleapis.com/drive/v3/files"

    query = (
        f"'{GOOGLE_DRIVE_FOLDER_ID}' in parents "
        f"and trashed = false "
        f"and mimeType contains 'image/'"
    )

    params = {
        "key": GOOGLE_API_KEY,
        "q": query,
        "fields": "files(id,name,mimeType,modifiedTime,createdTime)",
        "orderBy": "modifiedTime desc",
        "pageSize": limite,
    }

    resposta = requests.get(url, params=params, timeout=30)
    resposta.raise_for_status()

    return resposta.json().get("files", [])


def baixar_imagem(file_id, nome_arquivo):
    os.makedirs(PASTA_PRINTS, exist_ok=True)

    nome_limpo = nome_arquivo.replace("/", "_").replace("\\", "_")
    caminho = os.path.join(PASTA_PRINTS, nome_limpo)

    url = f"https://www.googleapis.com/drive/v3/files/{file_id}?alt=media&key={GOOGLE_API_KEY}"

    resposta = requests.get(url, timeout=60)
    resposta.raise_for_status()

    with open(caminho, "wb") as arquivo:
        arquivo.write(resposta.content)

    return caminho


def baixar_imagens_recentes(limite=25):
    arquivos = listar_imagens_recentes(limite=limite)

    imagens = []

    for arquivo in arquivos:
        caminho = baixar_imagem(arquivo["id"], arquivo["name"])

        imagens.append({
            "id": arquivo["id"],
            "nome": arquivo["name"],
            "modifiedTime": arquivo.get("modifiedTime"),
            "caminho": caminho,
        })

    return imagens