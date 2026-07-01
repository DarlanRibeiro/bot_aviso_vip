import os
import io
import json
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload


from config import (
    GOOGLE_SERVICE_ACCOUNT_JSON,
    GOOGLE_SERVICE_ACCOUNT_FILE,
    GOOGLE_DRIVE_NOVOS_FOLDER_ID,
    GOOGLE_DRIVE_USADOS_FOLDER_ID,
    PASTA_PRINTS,GOOGLE_DRIVE_LOGOS_FOLDER_ID,
)

SCOPES = ["https://www.googleapis.com/auth/drive"]


def get_service():
    if GOOGLE_SERVICE_ACCOUNT_JSON:
        info = json.loads(GOOGLE_SERVICE_ACCOUNT_JSON)
        creds = service_account.Credentials.from_service_account_info(
            info,
            scopes=SCOPES,
        )
    else:
        creds = service_account.Credentials.from_service_account_file(
            GOOGLE_SERVICE_ACCOUNT_FILE,
            scopes=SCOPES,
        )

    return build("drive", "v3", credentials=creds)


def listar_imagens(folder_id, limite=80):
    service = get_service()

    query = (
        f"'{folder_id}' in parents "
        f"and trashed = false "
        f"and mimeType contains 'image/'"
    )

    resultado = service.files().list(
        q=query,
        fields="files(id,name,mimeType,modifiedTime,createdTime,parents)",
        orderBy="modifiedTime desc",
        pageSize=limite,
        supportsAllDrives=True,
    ).execute()

    return resultado.get("files", [])


def baixar_imagem(file_id, nome_arquivo):
    service = get_service()
    os.makedirs(PASTA_PRINTS, exist_ok=True)

    nome_limpo = f"{file_id}_{nome_arquivo}".replace("/", "_").replace("\\", "_")
    caminho = os.path.join(PASTA_PRINTS, nome_limpo)

    request = service.files().get_media(fileId=file_id, supportsAllDrives=True)

    with io.FileIO(caminho, "wb") as arquivo:
        downloader = MediaIoBaseDownload(arquivo, request)
        concluido = False

        while not concluido:
            _, concluido = downloader.next_chunk()

    return caminho


def baixar_imagens_novas(limite=80):
    arquivos = listar_imagens(GOOGLE_DRIVE_NOVOS_FOLDER_ID, limite=limite)
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


def mover_para_usados(imagens):
    service = get_service()

    for img in imagens:
        file_id = img["id"]

        arquivo = service.files().get(
            fileId=file_id,
            fields="parents",
            supportsAllDrives=True,
        ).execute()

        parents = ",".join(arquivo.get("parents", []))

        service.files().update(
            fileId=file_id,
            addParents=GOOGLE_DRIVE_USADOS_FOLDER_ID,
            removeParents=parents,
            fields="id, parents",
            supportsAllDrives=True,
        ).execute()


def reciclar_usados_para_novos():
    service = get_service()
    usados = listar_imagens(GOOGLE_DRIVE_USADOS_FOLDER_ID, limite=1000)

    for arquivo in usados:
        service.files().update(
            fileId=arquivo["id"],
            addParents=GOOGLE_DRIVE_NOVOS_FOLDER_ID,
            removeParents=GOOGLE_DRIVE_USADOS_FOLDER_ID,
            fields="id, parents",
            supportsAllDrives=True,
        ).execute()

    return len(usados)

def baixar_logo():
    service = get_service()

    query = (
        f"'{GOOGLE_DRIVE_LOGOS_FOLDER_ID}' in parents "
        f"and trashed = false "
        f"and mimeType contains 'image/'"
    )

    resultado = service.files().list(
        q=query,
        fields="files(id,name,mimeType,modifiedTime)",
        orderBy="modifiedTime desc",
        pageSize=10,
        supportsAllDrives=True,
    ).execute()

    arquivos = resultado.get("files", [])

    if not arquivos:
        print("Nenhuma logo encontrada na pasta 03_LOGOS.")
        return None

    logo = arquivos[0]

    os.makedirs(PASTA_PRINTS, exist_ok=True)

    caminho = os.path.join(PASTA_PRINTS, "logo.png")

    request = service.files().get_media(
        fileId=logo["id"],
        supportsAllDrives=True,
    )

    with io.FileIO(caminho, "wb") as arquivo:
        downloader = MediaIoBaseDownload(arquivo, request)
        concluido = False

        while not concluido:
            _, concluido = downloader.next_chunk()

    print(f"Logo baixada: {logo['name']}")

    return caminho