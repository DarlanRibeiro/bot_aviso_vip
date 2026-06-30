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


def borda(draw, x, y, w, h, roi, destaque=False):
    cor = (0, 255, 150)
    largura = 7 if destaque else 4

    draw.rounded_rectangle(
        [x, y, x + w, y + h],
        radius=30,
        outline=cor,
        width=largura,
    )

    etiqueta = f"+{roi:.2f}%"

    box_w = 260 if destaque else 225
    box_h = 72 if destaque else 60

    draw.rounded_rectangle(
        [x + 18, y + 18, x + 18 + box_w, y + 18 + box_h],
        radius=18,
        fill=(0, 0, 0),
    )

    draw.text(
        (x + 38, y + 38),
        etiqueta,
        fill=cor,
    )


def layout_direita_destaque(fundo, imagens):
    largura, altura = fundo.size
    draw = ImageDraw.Draw(fundo)

    margem = 26
    espaco = 16

    esquerda_w = 450
    direita_w = largura - esquerda_w - margem * 2 - espaco
    bloco_h = (altura - margem * 2 - espaco * 2) // 3

    for i, item in enumerate(imagens[1:4]):
        x = margem
        y = margem + i * (bloco_h + espaco)
        img = encaixar_crop(abrir_e_corrigir(item["caminho"]), (esquerda_w, bloco_h))
        fundo.paste(img, (x, y))
        borda(draw, x, y, esquerda_w, bloco_h, item["roi"])

    x = margem + esquerda_w + espaco
    y = margem
    img = encaixar_crop(abrir_e_corrigir(imagens[0]["caminho"]), (direita_w, altura - margem * 2))
    fundo.paste(img, (x, y))
    borda(draw, x, y, direita_w, altura - margem * 2, imagens[0]["roi"], destaque=True)

    return fundo


def layout_topo_destaque(fundo, imagens):
    largura, altura = fundo.size
    draw = ImageDraw.Draw(fundo)

    margem = 26
    espaco = 16

    grande_w = largura - margem * 2
    grande_h = 610

    x = margem
    y = margem

    img = encaixar_crop(abrir_e_corrigir(imagens[0]["caminho"]), (grande_w, grande_h))
    fundo.paste(img, (x, y))
    borda(draw, x, y, grande_w, grande_h, imagens[0]["roi"], destaque=True)

    pequeno_w = (largura - margem * 2 - espaco * 2) // 3
    pequeno_h = altura - margem * 2 - grande_h - espaco
    y = margem + grande_h + espaco

    for i, item in enumerate(imagens[1:4]):
        x = margem + i * (pequeno_w + espaco)
        img = encaixar_crop(abrir_e_corrigir(item["caminho"]), (pequeno_w, pequeno_h))
        fundo.paste(img, (x, y))
        borda(draw, x, y, pequeno_w, pequeno_h, item["roi"])

    return fundo


def layout_esquerda_destaque(fundo, imagens):
    largura, altura = fundo.size
    draw = ImageDraw.Draw(fundo)

    margem = 26
    espaco = 16

    esquerda_w = 640
    direita_w = largura - esquerda_w - margem * 2 - espaco
    bloco_h = (altura - margem * 2 - espaco * 2) // 3

    x = margem
    y = margem

    img = encaixar_crop(abrir_e_corrigir(imagens[0]["caminho"]), (esquerda_w, altura - margem * 2))
    fundo.paste(img, (x, y))
    borda(draw, x, y, esquerda_w, altura - margem * 2, imagens[0]["roi"], destaque=True)

    x = margem + esquerda_w + espaco

    for i, item in enumerate(imagens[1:4]):
        y = margem + i * (bloco_h + espaco)
        img = encaixar_crop(abrir_e_corrigir(item["caminho"]), (direita_w, bloco_h))
        fundo.paste(img, (x, y))
        borda(draw, x, y, direita_w, bloco_h, item["roi"])

    return fundo


def layout_2x2_com_destaque(fundo, imagens):
    largura, altura = fundo.size
    draw = ImageDraw.Draw(fundo)

    margem = 26
    espaco = 16

    bloco_w = (largura - margem * 2 - espaco) // 2
    bloco_h = (altura - margem * 2 - espaco) // 2

    posicoes = [
        (margem, margem),
        (margem + bloco_w + espaco, margem),
        (margem, margem + bloco_h + espaco),
        (margem + bloco_w + espaco, margem + bloco_h + espaco),
    ]

    for i, item in enumerate(imagens[:4]):
        x, y = posicoes[i]
        img = encaixar_crop(abrir_e_corrigir(item["caminho"]), (bloco_w, bloco_h))
        fundo.paste(img, (x, y))
        borda(draw, x, y, bloco_w, bloco_h, item["roi"], destaque=(i == 0))

    return fundo


def criar_colagem(imagens_top):
    os.makedirs(PASTA_COLAGENS, exist_ok=True)

    imagens_ordenadas = sorted(imagens_top, key=lambda x: x["roi"], reverse=True)

    maior = imagens_ordenadas[0]
    demais = imagens_ordenadas[1:]
    random.shuffle(demais)

    imagens = [maior] + demais

    fundo = Image.new("RGB", (1080, 1080), (5, 9, 22))

    layouts = [
        layout_direita_destaque,
        layout_topo_destaque,
        layout_esquerda_destaque,
        layout_2x2_com_destaque,
    ]

    layout = random.choice(layouts)
    fundo = layout(fundo, imagens)

    nome_saida = f"colagem_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
    caminho_saida = os.path.join(PASTA_COLAGENS, nome_saida)

    fundo.save(caminho_saida, quality=95, optimize=True)

    return caminho_saida