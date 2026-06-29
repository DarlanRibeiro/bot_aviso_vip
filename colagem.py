import os
from datetime import datetime
from PIL import Image, ImageOps, ImageDraw

from config import PASTA_COLAGENS


def abrir_e_corrigir(caminho):
    img = Image.open(caminho).convert("RGB")
    img = ImageOps.exif_transpose(img)
    return img


def encaixar_crop(img, tamanho):
    return ImageOps.fit(
        img,
        tamanho,
        method=Image.Resampling.LANCZOS,
        centering=(0.5, 0.5),
    )


def criar_colagem(imagens_top):
    os.makedirs(PASTA_COLAGENS, exist_ok=True)

    largura = 1080
    altura = 1080

    fundo = Image.new("RGB", (largura, altura), (6, 10, 24))
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

        draw.rounded_rectangle(
            [x, y, x + bloco_largura, y + bloco_altura],
            radius=28,
            outline=(0, 255, 150),
            width=4,
        )

        etiqueta = f"+{item['roi']:.2f}%"

        draw.rounded_rectangle(
            [x + 18, y + 18, x + 230, y + 78],
            radius=18,
            fill=(0, 0, 0),
        )

        draw.text(
            (x + 38, y + 36),
            etiqueta,
            fill=(0, 255, 150),
        )

    nome_saida = f"colagem_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
    caminho_saida = os.path.join(PASTA_COLAGENS, nome_saida)

    fundo.save(caminho_saida, quality=95, optimize=True)

    return caminho_saida