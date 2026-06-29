import re
import cv2
import easyocr
import numpy as np

reader = easyocr.Reader(["en"], gpu=False)


def extrair_porcentagens(texto):
    padrao = r"(\d{1,5}(?:[.,]\d{1,2})?)\s*%"
    encontrados = re.findall(padrao, texto)

    valores = []

    for item in encontrados:
        try:
            valores.append(float(item.replace(",", ".")))
        except ValueError:
            pass

    return valores


def destacar_verde(caminho):
    imagem = cv2.imread(caminho)

    if imagem is None:
        return None

    hsv = cv2.cvtColor(imagem, cv2.COLOR_BGR2HSV)

    verde_baixo = np.array([35, 35, 35])
    verde_alto = np.array([95, 255, 255])

    mascara = cv2.inRange(hsv, verde_baixo, verde_alto)
    resultado = cv2.bitwise_and(imagem, imagem, mask=mascara)

    cinza = cv2.cvtColor(resultado, cv2.COLOR_BGR2GRAY)
    cinza = cv2.resize(cinza, None, fx=2.5, fy=2.5, interpolation=cv2.INTER_CUBIC)

    return cinza


def analisar_roi(imagem_info):
    caminho = imagem_info["caminho"]

    imagem_processada = destacar_verde(caminho)

    if imagem_processada is None:
        return {
            **imagem_info,
            "roi": 0,
            "texto_ocr": "",
        }

    resultado = reader.readtext(imagem_processada, detail=0)
    texto = " ".join(resultado)

    porcentagens = extrair_porcentagens(texto)
    maior_roi = max(porcentagens) if porcentagens else 0

    return {
        **imagem_info,
        "roi": maior_roi,
        "texto_ocr": texto,
    }


def selecionar_top_roi(imagens, quantidade=4):
    analisadas = []

    for imagem in imagens:
        try:
            analisadas.append(analisar_roi(imagem))
        except Exception as erro:
            print(f"Erro analisando {imagem.get('nome')}: {erro}")

    analisadas = sorted(analisadas, key=lambda x: x["roi"], reverse=True)

    return analisadas[:quantidade]