import warnings

# Oculta apenas o aviso repetitivo do PyTorch sobre pin_memory.
# Ele não representa erro e não afeta o funcionamento do OCR.
warnings.filterwarnings(
    "ignore",
    message=r".*pin_memory.*no accelerator.*",
    category=UserWarning,
)

import re
import cv2
import easyocr
import numpy as np

from config import ROI_MINIMO


reader = easyocr.Reader(
    ["en"],
    gpu=False,
    verbose=False,
)


def bbox_para_lista(bbox):
    xs = [p[0] for p in bbox]
    ys = [p[1] for p in bbox]

    return [
        min(xs),
        min(ys),
        max(xs),
        max(ys),
    ]


def unir_bbox(bboxes):
    return [
        min(b[0] for b in bboxes),
        min(b[1] for b in bboxes),
        max(b[2] for b in bboxes),
        max(b[3] for b in bboxes),
    ]


def normalizar_numero_percentual(valor):
    """
    Converte exemplos como:

    911,30       -> 911.30
    925.83       -> 925.83
    1.007,45     -> 1007.45
    3.014,48     -> 3014.48
    1,007.45     -> 1007.45
    """

    valor = (
        valor
        .replace("+", "")
        .replace(" ", "")
        .strip()
    )

    if not valor:
        return None

    if "," in valor and "." in valor:
        # O último separador é tratado como decimal.
        if valor.rfind(",") > valor.rfind("."):
            valor = valor.replace(".", "")
            valor = valor.replace(",", ".")
        else:
            valor = valor.replace(",", "")

    elif "," in valor:
        partes = valor.split(",")

        if len(partes) == 2 and len(partes[1]) <= 2:
            valor = valor.replace(",", ".")
        else:
            valor = valor.replace(",", "")

    elif "." in valor:
        partes = valor.split(".")

        # Um único ponto seguido de 3 algarismos é tratado
        # como separador de milhar: 1.007 -> 1007.
        if (
            len(partes) > 2
            or (
                len(partes) == 2
                and len(partes[1]) == 3
                and len(partes[0]) <= 3
            )
        ):
            valor = valor.replace(".", "")

    try:
        return float(valor)
    except ValueError:
        return None


def extrair_valor_percentual(texto):
    """
    Localiza um número seguido de % e normaliza
    separadores brasileiros e internacionais.
    """

    match = re.search(
        r"([+]?\s*\d[\d.,\s]{0,20})\s*%",
        texto,
    )

    if not match:
        return None

    return normalizar_numero_percentual(match.group(1))


def destacar_verde(caminho):
    imagem = cv2.imread(caminho)

    if imagem is None:
        return None

    hsv = cv2.cvtColor(imagem, cv2.COLOR_BGR2HSV)

    verde_baixo = np.array([35, 30, 30])
    verde_alto = np.array([95, 255, 255])

    mascara = cv2.inRange(
        hsv,
        verde_baixo,
        verde_alto,
    )

    resultado = cv2.bitwise_and(
        imagem,
        imagem,
        mask=mascara,
    )

    cinza = cv2.cvtColor(
        resultado,
        cv2.COLOR_BGR2GRAY,
    )

    cinza = cv2.resize(
        cinza,
        None,
        fx=2.5,
        fy=2.5,
        interpolation=cv2.INTER_CUBIC,
    )

    return cinza


def analisar_roi(imagem_info):
    caminho = imagem_info["caminho"]

    imagem_original = cv2.imread(caminho)

    if imagem_original is None:
        return {
            **imagem_info,
            "roi": 0,
            "bbox_foco": None,
            "bbox_moeda": None,
            "valida": False,
        }

    escala_ocr = 2.5
    imagem_processada = destacar_verde(caminho)

    if imagem_processada is None:
        return {
            **imagem_info,
            "roi": 0,
            "bbox_foco": None,
            "bbox_moeda": None,
            "valida": False,
        }

    resultados_verde = reader.readtext(
        imagem_processada,
        detail=1,
    )

    melhor_roi = 0
    bbox_roi = None

    for bbox, texto, conf in resultados_verde:
        valor = extrair_valor_percentual(texto)

        if valor is not None and valor > melhor_roi:
            melhor_roi = valor

            b = bbox_para_lista(bbox)

            bbox_roi = [
                b[0] / escala_ocr,
                b[1] / escala_ocr,
                b[2] / escala_ocr,
                b[3] / escala_ocr,
            ]

    resultados_full = reader.readtext(
        caminho,
        detail=1,
    )

    bboxes_importantes = []
    bbox_moeda = None

    if bbox_roi:
        bboxes_importantes.append(bbox_roi)

    for bbox, texto, conf in resultados_full:
        t = texto.upper()
        b = bbox_para_lista(bbox)

        if "USDT" in t:
            bbox_moeda = b
            bboxes_importantes.append(b)

        if (
            "LONG" in t
            or "SHORT" in t
            or "CURTA" in t
            or "LONGA" in t
            or "ROI" in t
            or "PREÇO" in t
            or "PRECO" in t
            or "ENTRADA" in t
            or "ÚLTIMO" in t
            or "ULTIMO" in t
            or "REF" in t
        ):
            bboxes_importantes.append(b)

    bbox_foco = (
        unir_bbox(bboxes_importantes)
        if bboxes_importantes
        else None
    )

    return {
        **imagem_info,
        "roi": melhor_roi,
        "bbox_foco": bbox_foco,
        "bbox_moeda": bbox_moeda,
        "valida": melhor_roi >= ROI_MINIMO,
    }


def selecionar_top_roi(imagens, quantidade=4):
    analisadas = []

    for imagem in imagens:
        try:
            item = analisar_roi(imagem)

            if item["valida"]:
                analisadas.append(item)
            else:
                print(
                    f"Ignorada: {imagem.get('nome')} "
                    f"| ROI: {item['roi']}%"
                )

        except Exception as erro:
            print(
                f"Erro analisando "
                f"{imagem.get('nome')}: {erro}"
            )

    analisadas = sorted(
        analisadas,
        key=lambda x: x["roi"],
        reverse=True,
    )

    return analisadas[:quantidade]