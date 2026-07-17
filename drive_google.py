import os
import io
import json
import time

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import (
    MediaIoBaseDownload,
    MediaIoBaseUpload,
)

from config import (
    GOOGLE_SERVICE_ACCOUNT_JSON,
    GOOGLE_SERVICE_ACCOUNT_FILE,
    GOOGLE_DRIVE_NOVOS_FOLDER_ID,
    GOOGLE_DRIVE_USADOS_FOLDER_ID,
    GOOGLE_DRIVE_LOGOS_FOLDER_ID,
    PASTA_PRINTS,
)

SCOPES = ["https://www.googleapis.com/auth/drive"]

NOME_ARQUIVO_HISTORICO = "_historico_postagens.json"


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

    return build(
        "drive",
        "v3",
        credentials=creds,
        cache_discovery=False,
    )


def listar_imagens(folder_id, limite=80):
    service = get_service()

    query = (
        f"'{folder_id}' in parents "
        f"and trashed = false "
        f"and mimeType contains 'image/'"
    )

    resultado = service.files().list(
        q=query,
        fields=(
            "files("
            "id,"
            "name,"
            "mimeType,"
            "modifiedTime,"
            "createdTime,"
            "parents"
            ")"
        ),
        orderBy="modifiedTime desc",
        pageSize=limite,
        supportsAllDrives=True,
        includeItemsFromAllDrives=True,
    ).execute()

    return resultado.get("files", [])


def baixar_imagem(
    file_id,
    nome_arquivo,
    max_tentativas=4,
):
    os.makedirs(PASTA_PRINTS, exist_ok=True)

    nome_limpo = (
        f"{file_id}_{nome_arquivo}"
        .replace("/", "_")
        .replace("\\", "_")
    )

    caminho = os.path.join(
        PASTA_PRINTS,
        nome_limpo,
    )

    for tentativa in range(1, max_tentativas + 1):
        try:
            service = get_service()

            request = service.files().get_media(
                fileId=file_id,
                supportsAllDrives=True,
            )

            # Recomeça o arquivo do zero em cada tentativa.
            with io.FileIO(caminho, "wb") as arquivo:
                downloader = MediaIoBaseDownload(
                    arquivo,
                    request,
                    chunksize=1024 * 1024,
                )

                concluido = False

                while not concluido:
                    _, concluido = downloader.next_chunk(
                        num_retries=3
                    )

            return caminho

        except HttpError as erro:
            status = getattr(
                erro.resp,
                "status",
                None,
            )

            erro_temporario = status in {
                429,
                500,
                502,
                503,
                504,
            }

            if (
                not erro_temporario
                or tentativa >= max_tentativas
            ):
                if os.path.exists(caminho):
                    try:
                        os.remove(caminho)
                    except OSError:
                        pass

                raise

            espera = 2 ** tentativa

            print(
                f"Falha temporária baixando "
                f"{nome_arquivo} "
                f"(HTTP {status}). "
                f"Nova tentativa em {espera}s "
                f"[{tentativa}/{max_tentativas}]..."
            )

            time.sleep(espera)

        except Exception:
            if os.path.exists(caminho):
                try:
                    os.remove(caminho)
                except OSError:
                    pass

            raise

    raise RuntimeError(
        f"Não foi possível baixar {nome_arquivo}."
    )


def baixar_imagens_da_pasta(folder_id, origem, limite=80):
    arquivos = listar_imagens(
        folder_id=folder_id,
        limite=limite,
    )

    imagens = []

    for arquivo in arquivos:
        try:
            caminho = baixar_imagem(
                file_id=arquivo["id"],
                nome_arquivo=arquivo["name"],
            )

            imagens.append({
                "id": arquivo["id"],
                "nome": arquivo["name"],
                "modifiedTime": arquivo.get("modifiedTime"),
                "createdTime": arquivo.get("createdTime"),
                "caminho": caminho,
                "origem": origem,
            })

        except Exception as erro:
            print(
                f"Erro baixando {arquivo.get('name')}: {erro}"
            )

    return imagens


def baixar_imagens_novas(limite=80):
    return baixar_imagens_da_pasta(
        folder_id=GOOGLE_DRIVE_NOVOS_FOLDER_ID,
        origem="novos",
        limite=limite,
    )


def baixar_imagens_usadas(limite=80):
    return baixar_imagens_da_pasta(
        folder_id=GOOGLE_DRIVE_USADOS_FOLDER_ID,
        origem="usados",
        limite=limite,
    )


def mover_para_usados(imagens):
    """
    Move para 02_USADOS todas as imagens recebidas
    cuja origem seja 01_NOVOS.

    Não existe nenhuma regra para manter uma imagem
    obrigatoriamente em 01_NOVOS.
    """

    if not imagens:
        return 0

    service = get_service()
    total_movidas = 0

    print("=" * 60)
    print("MOVENDO IMAGENS DE 01_NOVOS PARA 02_USADOS")

    for img in imagens:
        nome = img.get("nome", "sem nome")
        origem = img.get("origem")
        file_id = img.get("id")

        if origem != "novos":
            continue

        if not file_id:
            print(f"Não foi possível mover {nome}: ID ausente.")
            continue

        try:
            arquivo = service.files().get(
                fileId=file_id,
                fields="id,name,parents",
                supportsAllDrives=True,
            ).execute()

            parents = arquivo.get("parents", [])

            if GOOGLE_DRIVE_USADOS_FOLDER_ID in parents:
                print(f"Já está em 02_USADOS: {nome}")
                continue

            parents_para_remover = [
                parent_id
                for parent_id in parents
                if parent_id != GOOGLE_DRIVE_USADOS_FOLDER_ID
            ]

            parametros = {
                "fileId": file_id,
                "addParents": GOOGLE_DRIVE_USADOS_FOLDER_ID,
                "fields": "id,name,parents",
                "supportsAllDrives": True,
            }

            if parents_para_remover:
                parametros["removeParents"] = ",".join(
                    parents_para_remover
                )

            service.files().update(**parametros).execute()

            total_movidas += 1
            print(f"Movida para 02_USADOS: {nome}")

        except Exception as erro:
            print(f"ERRO movendo {nome}: {erro}")

    print(f"Total movidas para 02_USADOS: {total_movidas}")
    print("=" * 60)

    return total_movidas


def reciclar_usados_para_novos():
    service = get_service()

    usados = listar_imagens(
        GOOGLE_DRIVE_USADOS_FOLDER_ID,
        limite=1000,
    )

    total = 0

    for arquivo in usados:
        try:
            service.files().update(
                fileId=arquivo["id"],
                addParents=GOOGLE_DRIVE_NOVOS_FOLDER_ID,
                removeParents=GOOGLE_DRIVE_USADOS_FOLDER_ID,
                fields="id,parents",
                supportsAllDrives=True,
            ).execute()

            total += 1

        except Exception as erro:
            print(
                f"Erro reciclando {arquivo.get('name')}: {erro}"
            )

    return total


def buscar_arquivo_historico(service):
    nome_seguro = NOME_ARQUIVO_HISTORICO.replace("'", "\\'")

    query = (
        f"'{GOOGLE_DRIVE_USADOS_FOLDER_ID}' in parents "
        f"and name = '{nome_seguro}' "
        f"and trashed = false"
    )

    resultado = service.files().list(
        q=query,
        fields="files(id,name,mimeType,modifiedTime)",
        pageSize=10,
        supportsAllDrives=True,
        includeItemsFromAllDrives=True,
    ).execute()

    arquivos = resultado.get("files", [])

    if not arquivos:
        return None

    return arquivos[0]


def historico_padrao():
    return {
        "usadas_no_ciclo": [],
        "ultimo_lote": [],
        "numero_ciclo": 1,
    }


def carregar_historico_postagens():
    """
    Carrega o histórico persistente salvo no Google Drive.
    """

    service = get_service()

    try:
        arquivo = buscar_arquivo_historico(service)

        if not arquivo:
            print(
                "Histórico ainda não existe. "
                "Será iniciado um novo ciclo."
            )
            return historico_padrao()

        request = service.files().get_media(
            fileId=arquivo["id"],
            supportsAllDrives=True,
        )

        buffer = io.BytesIO()
        downloader = MediaIoBaseDownload(buffer, request)

        concluido = False

        while not concluido:
            _, concluido = downloader.next_chunk()

        buffer.seek(0)

        conteudo = buffer.read().decode("utf-8")
        historico = json.loads(conteudo)

        if not isinstance(historico, dict):
            return historico_padrao()

        print(
            "Histórico carregado: "
            f"ciclo {historico.get('numero_ciclo', 1)} | "
            f"{len(historico.get('usadas_no_ciclo', []))} "
            "imagens usadas."
        )

        return historico

    except Exception as erro:
        print(f"Erro carregando histórico: {erro}")
        print("Usando histórico vazio temporariamente.")

        return historico_padrao()


def salvar_historico_postagens(historico):
    """
    Salva o histórico no Google Drive.

    O JSON fica dentro de 02_USADOS, mas não aparece
    na seleção porque listar_imagens busca somente imagens.
    """

    service = get_service()

    conteudo = json.dumps(
        historico,
        ensure_ascii=False,
        indent=2,
    ).encode("utf-8")

    media = MediaIoBaseUpload(
        io.BytesIO(conteudo),
        mimetype="application/json",
        resumable=False,
    )

    try:
        arquivo = buscar_arquivo_historico(service)

        if arquivo:
            service.files().update(
                fileId=arquivo["id"],
                media_body=media,
                fields="id,name,modifiedTime",
                supportsAllDrives=True,
            ).execute()

            print("Histórico de postagens atualizado no Drive.")

        else:
            metadata = {
                "name": NOME_ARQUIVO_HISTORICO,
                "mimeType": "application/json",
                "parents": [GOOGLE_DRIVE_USADOS_FOLDER_ID],
            }

            service.files().create(
                body=metadata,
                media_body=media,
                fields="id,name",
                supportsAllDrives=True,
            ).execute()

            print("Histórico de postagens criado no Drive.")

        return True

    except Exception as erro:
        print(f"ERRO salvando histórico: {erro}")
        return False


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
        includeItemsFromAllDrives=True,
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