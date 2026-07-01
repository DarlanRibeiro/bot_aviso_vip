import os
import random
from datetime import datetime
from PIL import Image, ImageOps, ImageDraw

from config import PASTA_COLAGENS
from camera import camera_virtual
from drive_google import baixar_logo

FUNDO = (5, 9, 22)


def abrir_e_corrigir(caminho):
    img = Image.open(caminho).convert("RGB")
    return ImageOps.exif_transpose(img)


def abrir_logo(caminho_logo):
    if not caminho_logo or not os.path.exists(caminho_logo):
        return None

    logo = Image.open(caminho_logo).convert("RGBA")
    return ImageOps.exif_transpose(logo)


def redimensionar_logo(logo, largura_max=520, altura_max=130):
    logo = logo.copy()
    logo.thumbnail((largura_max, altura_max), Image.Resampling.LANCZOS)
    return logo


def colar_logo_topo(fundo, caminho_logo):
    logo = abrir_logo(caminho_logo)

    if logo is None:
        return fundo

    logo = redimensionar_logo(logo)

    largura_fundo, _ = fundo.size

    x = (largura_fundo - logo.width) // 2
    y = 25

    fundo.paste(logo, (x, y), logo)

    return fundo


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


def layout_01_topo(fundo, imagens, offset_y):
    margem = 10
    espaco = 8
    largura, altura = fundo.size

    area_h = altura - offset_y - margem
    grande_w = largura - margem * 2
    grande_h = int(area_h * 0.58)

    y_grande = offset_y

    colar_card(fundo, imagens[0], margem, y_grande, grande_w, grande_h, True)

    pequeno_w = (largura - margem * 2 - espaco * 2) // 3
    pequeno_h = area_h - grande_h - espaco
    y = y_grande + grande_h + espaco

    for i, item in enumerate(imagens[1:4]):
        x = margem + i * (pequeno_w + espaco)
        colar_card(fundo, item, x, y, pequeno_w, pequeno_h)

    return fundo


def layout_02_esquerda(fundo, imagens, offset_y):
    margem = 10
    espaco = 8
    largura, altura = fundo.size

    area_h = altura - offset_y - margem
    grande_w = 650
    grande_h = area_h

    colar_card(fundo, imagens[0], margem, offset_y, grande_w, grande_h, True)

    pequeno_w = largura - margem * 2 - grande_w - espaco
    pequeno_h = (area_h - espaco * 2) // 3

    x = margem + grande_w + espaco

    for i, item in enumerate(imagens[1:4]):
        y = offset_y + i * (pequeno_h + espaco)
        colar_card(fundo, item, x, y, pequeno_w, pequeno_h)

    return fundo


def layout_03_direita(fundo, imagens, offset_y):
    margem = 10
    espaco = 8
    largura, altura = fundo.size

    area_h = altura - offset_y - margem

    pequeno_w = 390
    grande_w = largura - margem * 2 - pequeno_w - espaco
    grande_h = area_h

    x_grande = margem + pequeno_w + espaco
    colar_card(fundo, imagens[0], x_grande, offset_y, grande_w, grande_h, True)

    pequeno_h = (area_h - espaco * 2) // 3

    for i, item in enumerate(imagens[1:4]):
        x = margem
        y = offset_y + i * (pequeno_h + espaco)
        colar_card(fundo, item, x, y, pequeno_w, pequeno_h)

    return fundo


def layout_04_mosaico(fundo, imagens, offset_y):
    margem = 10
    espaco = 8
    largura, altura = fundo.size

    area_h = altura - offset_y - margem

    grande_h = int(area_h * 0.55)
    pequeno_h = area_h - grande_h - espaco

    esquerda_w = 680
    direita_w = largura - margem * 2 - esquerda_w - espaco

    colar_card(fundo, imagens[0], margem, offset_y, esquerda_w, grande_h, True)

    x_dir = margem + esquerda_w + espaco
    meio_h = (grande_h - espaco) // 2

    colar_card(fundo, imagens[1], x_dir, offset_y, direita_w, meio_h)
    colar_card(fundo, imagens[2], x_dir, offset_y + meio_h + espaco, direita_w, meio_h)

    y_baixo = offset_y + grande_h + espaco
    colar_card(fundo, imagens[3], margem, y_baixo, largura - margem * 2, pequeno_h)

    return fundo


def layout_05_duplo(fundo, imagens, offset_y):
    margem = 10
    espaco = 8
    largura, altura = fundo.size

    area_h = altura - offset_y - margem

    grande_h = int(area_h * 0.56)
    baixo_h = area_h - grande_h - espaco

    grande_w = int((largura - margem * 2 - espaco) * 0.68)
    lateral_w = largura - margem * 2 - grande_w - espaco

    colar_card(fundo, imagens[0], margem, offset_y, grande_w, grande_h, True)
    colar_card(fundo, imagens[1], margem + grande_w + espaco, offset_y, lateral_w, grande_h)

    pequeno_w = (largura - margem * 2 - espaco) // 2
    y = offset_y + grande_h + espaco

    colar_card(fundo, imagens[2], margem, y, pequeno_w, baixo_h)
    colar_card(fundo, imagens[3], margem + pequeno_w + espaco, y, pequeno_w, baixo_h)

    return fundo


def criar_colagem(imagens_top):
    os.makedirs(PASTA_COLAGENS, exist_ok=True)

    imagens_ordenadas = sorted(
        imagens_top,
        key=lambda x: x["roi"],
        reverse=True,
    )

    maior = imagens_ordenadas[0]
    demais = imagens_ordenadas[1:]
    random.shuffle(demais)

    imagens = [maior] + demais

    fundo = Image.new("RGB", (1080, 1080), FUNDO)

    caminho_logo = baixar_logo()

    fundo = colar_logo_topo(fundo, caminho_logo)

    offset_y = 170

    layouts = [
        layout_01_topo,
        layout_02_esquerda,
        layout_03_direita,
        layout_04_mosaico,
        layout_05_duplo,
    ]

    layout = random.choice(layouts)
    fundo = layout(fundo, imagens, offset_y)

    nome_saida = f"colagem_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
    caminho_saida = os.path.join(PASTA_COLAGENS, nome_saida)

    fundo.save(caminho_saida, quality=95, optimize=True)

    return caminho_saida