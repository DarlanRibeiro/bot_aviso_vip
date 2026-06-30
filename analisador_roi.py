import re
import cv2
import easyocr
import numpy as np

from config import ROI_MINIMO

reader = easyocr.Reader(["en"], gpu=False)


def extrair_porcentagens(texto):
    padrao = r"(\+?\d{1,5}(?:[.,]\d{1,2})?)\s*%"
    encontrados = re.findall(padrao, texto)

    valores = []

    for item in encontrados:
        try:
            valor = float(item.replace("+", "").replace(",", "."))
            valores.append(valor)
        except ValueError:
            pass

    return valores


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
    cinza = cv2.resize(cinza, None, fx=2.8, fy=2.8, interpolation=cv2.INTER_CUBIC)

    return cinza


def analisar_roi(imagem_info):
    caminho = imagem_info["caminho"]
    imagem_processada = destacar_verde(caminho)

    if imagem_processada is None:
        return {**imagem_info, "roi": 0, "texto_ocr": "", "valida": False}

    resultado = reader.readtext(imagem_processada, detail=0)
    texto = " ".join(resultado)

    porcentagens = extrair_porcentagens(texto)
    maior_roi = max(porcentagens) if porcentagens else 0

    return {
        **imagem_info,
        "roi": maior_roi,
        "texto_ocr": texto,
        "valida": maior_roi >= ROI_MINIMO,
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