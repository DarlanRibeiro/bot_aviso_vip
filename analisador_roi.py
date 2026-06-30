import re
import cv2
import easyocr
import numpy as np

from config import ROI_MINIMO

reader = easyocr.Reader(["en"], gpu=False)


def bbox_para_lista(bbox):
    xs = [p[0] for p in bbox]
    ys = [p[1] for p in bbox]
    return [min(xs), min(ys), max(xs), max(ys)]


def unir_bbox(bboxes):
    return [
        min(b[0] for b in bboxes),
        min(b[1] for b in bboxes),
        max(b[2] for b in bboxes),
        max(b[3] for b in bboxes),
    ]


def extrair_valor_percentual(texto):
    match = re.search(r"(\+?\d{1,5}(?:[.,]\d{1,2})?)\s*%", texto)
    if not match:
        return None

    try:
        return float(match.group(1).replace("+", "").replace(",", "."))
    except ValueError:
        return None


def destacar_verde(caminho):
    imagem = cv2.imread(caminho)

    if imagem is None:
        return None

    hsv = cv2.cvtColor(imagem, cv2.COLOR_BGR2HSV)

    verde_baixo = np.array([35, 30, 30])
    verde_alto = np.array([95, 255, 255])

    mascara = cv2.inRange(hsv, verde_baixo, verde_alto)
    resultado = cv2.bitwise_and(imagem, imagem, mask=mascara)

    cinza = cv2.cvtColor(resultado, cv2.COLOR_BGR2GRAY)
    cinza = cv2.resize(cinza, None, fx=2.5, fy=2.5, interpolation=cv2.INTER_CUBIC)

    return cinza


def analisar_roi(imagem_info):
    caminho = imagem_info["caminho"]

    imagem_original = cv2.imread(caminho)
    if imagem_original is None:
        return {**imagem_info, "roi": 0, "bbox_foco": None, "bbox_moeda": None, "valida": False}

    escala_ocr = 2.5
    imagem_processada = destacar_verde(caminho)

    if imagem_processada is None:
        return {**imagem_info, "roi": 0, "bbox_foco": None, "bbox_moeda": None, "valida": False}

    resultados_verde = reader.readtext(imagem_processada, detail=1)

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

    resultados_full = reader.readtext(caminho, detail=1)

    bboxes_importantes = []
    bbox_moeda = None

    if bbox_roi:
        bboxes_importantes.append(bbox_roi)

    for bbox, texto, conf in resultados_full:
        t = texto.upper()
        b = bbox_para_lista(bbox)

        # Começo da área útil: moeda/par
        if "USDT" in t:
            bbox_moeda = b
            bboxes_importantes.append(b)

        # Informações úteis, sem incluir usuário/data/hora
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

    bbox_foco = unir_bbox(bboxes_importantes) if bboxes_importantes else None

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
                print(f"Ignorada: {imagem.get('nome')} | ROI: {item['roi']}%")

        except Exception as erro:
            print(f"Erro analisando {imagem.get('nome')}: {erro}")

    analisadas = sorted(analisadas, key=lambda x: x["roi"], reverse=True)

    return analisadas[:quantidade]