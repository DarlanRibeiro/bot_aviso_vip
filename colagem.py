import os
import random
from datetime import datetime
from PIL import Image, ImageOps, ImageDraw

from config import PASTA_COLAGENS
from camera import camera_virtual
from drive_google import baixar_logo
from layout_engine import escolher_layout_4

FUNDO = (5, 9, 22)


def abrir_e_corrigir(caminho):
    img = Image.open(caminho).convert("RGB")
    return ImageOps.exif_transpose(img)


def abrir_logo(caminho_logo):
    if not caminho_logo or not os.path.exists(caminho_logo):
        return None

    logo = Image.open(caminho_logo).convert("RGBA")
    return ImageOps.exif_transpose(logo)


def redimensionar_logo_marca_dagua(logo, largura_alvo=950):
    proporcao = largura_alvo / logo.width
    nova_altura = int(logo.height * proporcao)

    return logo.resize(
        (largura_alvo, nova_altura),
        Image.Resampling.LANCZOS,
    )


def aplicar_transparencia(logo, opacidade=0.30):
    logo = logo.copy()
    alpha = logo.getchannel("A")
    alpha = alpha.point(lambda p: int(p * opacidade))
    logo.putalpha(alpha)
    return logo


def aplicar_marca_dagua(fundo, caminho_logo):
    logo = abrir_logo(caminho_logo)

    if logo is None:
        print("Marca d'água não aplicada: logo não encontrada.")
        return fundo

    logo = redimensionar_logo_marca_dagua(logo, largura_alvo=950)
    logo = aplicar_transparencia(logo, opacidade=0.30)

    largura_fundo, altura_fundo = fundo.size
    x = (largura_fundo - logo.width) // 2
    y = (altura_fundo - logo.height) // 2

    fundo_rgba = fundo.convert("RGBA")
    fundo_rgba.paste(logo, (x, y), logo)

    return fundo_rgba.convert("RGB")


def arredondar(img, raio=22):
    w, h = img.size

    mask = Image.new("L", (w, h), 0)
    draw = ImageDraw.Draw(mask)
    draw.rounded_rectangle([0, 0, w, h], radius=raio, fill=255)

    card = Image.new("RGB", (w, h), FUNDO)
    card.paste(img, (0, 0), mask)

    return card, mask


def colar_card(fundo, item, x, y, w, h, destaque=False):
    img = abrir_e_corrigir(item["caminho"])

    card_img = camera_virtual(
        img=img,
        tamanho=(w, h),
        bbox_foco=item.get("bbox_foco"),
        bbox_moeda=item.get("bbox_moeda"),
        destaque=destaque,
    )

    card, mask = arredondar(card_img, raio=22)
    fundo.paste(card, (x, y), mask)


def pegar(imagens, indice):
    return imagens[indice % len(imagens)]


def desenhar_layout(fundo, imagens, layout):
    for card in layout["cards"]:
        item = pegar(imagens, card["i"])

        colar_card(
            fundo=fundo,
            item=item,
            x=card["x"],
            y=card["y"],
            w=card["w"],
            h=card["h"],
            destaque=card.get("destaque", False),
        )

    return fundo


def criar_colagem(imagens_top):
    os.makedirs(PASTA_COLAGENS, exist_ok=True)

    imagens_ordenadas = sorted(
        imagens_top,
        key=lambda x: x["roi"],
        reverse=True,
    )

    imagens_ordenadas = imagens_ordenadas[:4]

    if len(imagens_ordenadas) < 4:
        print("Menos de 4 imagens disponíveis para colagem.")
        return None

    maior = imagens_ordenadas[0]
    demais = imagens_ordenadas[1:]
    random.shuffle(demais)

    imagens = [maior] + demais

    fundo = Image.new("RGB", (1080, 1080), FUNDO)

    layout = escolher_layout_4()
    fundo = desenhar_layout(fundo, imagens, layout)

    caminho_logo = baixar_logo()
    fundo = aplicar_marca_dagua(fundo, caminho_logo)

    nome_saida = f"colagem_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
    caminho_saida = os.path.join(PASTA_COLAGENS, nome_saida)

    fundo.save(caminho_saida, quality=95, optimize=True)

    return caminho_saida