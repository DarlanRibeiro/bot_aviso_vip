import os
import random
from datetime import datetime
from PIL import Image, ImageOps, ImageDraw

from config import PASTA_COLAGENS


def abrir_e_corrigir(caminho):
    img = Image.open(caminho).convert("RGB")
    return ImageOps.exif_transpose(img)


def encaixar_crop(img, tamanho, centro=(0.5, 0.5)):
    return ImageOps.fit(
        img,
        tamanho,
        method=Image.Resampling.LANCZOS,
        centering=centro,
    )


def desenhar_borda_e_roi(draw, x, y, w, h, roi):
    draw.rounded_rectangle(
        [x, y, x + w, y + h],
        radius=28,
        outline=(0, 255, 150),
        width=4,
    )

    etiqueta = f"+{roi:.2f}%"

    draw.rounded_rectangle(
        [x + 18, y + 18, x + 235, y + 78],
        radius=18,
        fill=(0, 0, 0),
    )

    draw.text(
        (x + 38, y + 36),
        etiqueta,
        fill=(0, 255, 150),
    )


def layout_2x2(fundo, imagens_top):
    largura, altura = fundo.size
    draw = ImageDraw.Draw(fundo)

    margem = 28
    espaco = 18

    bloco_largura = (largura - margem * 2 - espaco) // 2
    bloco_altura = (altura - margem * 2 - espaco) // 2

    posicoes = [
        (margem, margem),
        (margem + bloco_largura + espaco, margem),
        (margem, margem + bloco_altura + espaco),
        (margem + bloco_largura + espaco, margem + bloco_altura + espaco),
    ]

    for i, item in enumerate(imagens_top[:4]):
        img = abrir_e_corrigir(item["caminho"])
        img = encaixar_crop(img, (bloco_largura, bloco_altura))

        x, y = posicoes[i]

        fundo.paste(img, (x, y))
        desenhar_borda_e_roi(draw, x, y, bloco_largura, bloco_altura, item["roi"])

    return fundo


def layout_destaque(fundo, imagens_top):
    largura, altura = fundo.size
    draw = ImageDraw.Draw(fundo)

    margem = 28
    espaco = 18

    grande_w = largura - margem * 2
    grande_h = 520

    img = abrir_e_corrigir(imagens_top[0]["caminho"])
    img = encaixar_crop(img, (grande_w, grande_h))
    fundo.paste(img, (margem, margem))
    desenhar_borda_e_roi(draw, margem, margem, grande_w, grande_h, imagens_top[0]["roi"])

    pequeno_w = (largura - margem * 2 - espaco * 2) // 3
    pequeno_h = altura - margem * 2 - grande_h - espaco
    y = margem + grande_h + espaco

    for i, item in enumerate(imagens_top[1:4]):
        x = margem + i * (pequeno_w + espaco)

        img = abrir_e_corrigir(item["caminho"])
        img = encaixar_crop(img, (pequeno_w, pequeno_h))

        fundo.paste(img, (x, y))
        desenhar_borda_e_roi(draw, x, y, pequeno_w, pequeno_h, item["roi"])

    return fundo


def layout_mosaico_vertical(fundo, imagens_top):
    largura, altura = fundo.size
    draw = ImageDraw.Draw(fundo)

    margem = 28
    espaco = 18

    esquerda_w = 640
    esquerda_h = altura - margem * 2
    direita_w = largura - esquerda_w - margem * 2 - espaco

    img = abrir_e_corrigir(imagens_top[0]["caminho"])
    img = encaixar_crop(img, (esquerda_w, esquerda_h))

    fundo.paste(img, (margem, margem))
    desenhar_borda_e_roi(draw, margem, margem, esquerda_w, esquerda_h, imagens_top[0]["roi"])

    bloco_h = (altura - margem * 2 - espaco * 2) // 3
    x = margem + esquerda_w + espaco

    for i, item in enumerate(imagens_top[1:4]):
        y = margem + i * (bloco_h + espaco)

        img = abrir_e_corrigir(item["caminho"])
        img = encaixar_crop(img, (direita_w, bloco_h))

        fundo.paste(img, (x, y))
        desenhar_borda_e_roi(draw, x, y, direita_w, bloco_h, item["roi"])

    return fundo


def criar_colagem(imagens_top):
    os.makedirs(PASTA_COLAGENS, exist_ok=True)

    largura = 1080
    altura = 1080

    fundo = Image.new("RGB", (largura, altura), (6, 10, 24))

    imagens_embaralhadas = imagens_top[:]
    random.shuffle(imagens_embaralhadas)

    layouts = [
        layout_2x2,
        layout_destaque,
        layout_mosaico_vertical,
    ]

    layout_escolhido = random.choice(layouts)
    fundo = layout_escolhido(fundo, imagens_embaralhadas)

    nome_saida = f"colagem_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
    caminho_saida = os.path.join(PASTA_COLAGENS, nome_saida)

    fundo.save(caminho_saida, quality=95, optimize=True)

    return caminho_saida