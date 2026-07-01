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


def redimensionar_logo_marca_dagua(logo, largura_alvo=760):
    proporcao = largura_alvo / logo.width
    nova_altura = int(logo.height * proporcao)

    return logo.resize(
        (largura_alvo, nova_altura),
        Image.Resampling.LANCZOS,
    )


def aplicar_transparencia(logo, opacidade=0.22):
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

    logo = redimensionar_logo_marca_dagua(logo, largura_alvo=760)
    logo = aplicar_transparencia(logo, opacidade=0.22)

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
    if not imagens:
        return None

    return imagens[indice % len(imagens)]


def layout_01_grade_2x3(fundo, imagens):
    margem = 10
    espaco = 8
    largura, altura = fundo.size

    card_w = (largura - margem * 2 - espaco) // 2
    card_h = (altura - margem * 2 - espaco * 2) // 3

    posicoes = [
        (margem, margem),
        (margem + card_w + espaco, margem),
        (margem, margem + card_h + espaco),
        (margem + card_w + espaco, margem + card_h + espaco),
        (margem, margem + (card_h + espaco) * 2),
        (margem + card_w + espaco, margem + (card_h + espaco) * 2),
    ]

    for i, pos in enumerate(posicoes):
        item = pegar(imagens, i)
        colar_card(fundo, item, pos[0], pos[1], card_w, card_h, destaque=(i == 0))

    return fundo


def layout_02_destaque_direita_com_coluna(fundo, imagens):
    margem = 10
    espaco = 8
    largura, altura = fundo.size

    coluna_w = 360
    destaque_w = largura - margem * 2 - coluna_w - espaco

    card_col_h = (altura - margem * 2 - espaco * 2) // 3

    for i in range(3):
        item = pegar(imagens, i + 1)
        y = margem + i * (card_col_h + espaco)
        colar_card(fundo, item, margem, y, coluna_w, card_col_h)

    x_destaque = margem + coluna_w + espaco
    colar_card(
        fundo,
        pegar(imagens, 0),
        x_destaque,
        margem,
        destaque_w,
        altura - margem * 2,
        destaque=True,
    )

    return fundo


def layout_03_destaque_esquerda_com_coluna(fundo, imagens):
    margem = 10
    espaco = 8
    largura, altura = fundo.size

    coluna_w = 360
    destaque_w = largura - margem * 2 - coluna_w - espaco

    colar_card(
        fundo,
        pegar(imagens, 0),
        margem,
        margem,
        destaque_w,
        altura - margem * 2,
        destaque=True,
    )

    x_coluna = margem + destaque_w + espaco
    card_col_h = (altura - margem * 2 - espaco * 2) // 3

    for i in range(3):
        item = pegar(imagens, i + 1)
        y = margem + i * (card_col_h + espaco)
        colar_card(fundo, item, x_coluna, y, coluna_w, card_col_h)

    return fundo


def layout_04_destaque_topo_mais_4(fundo, imagens):
    margem = 10
    espaco = 8
    largura, altura = fundo.size

    destaque_h = 520
    baixo_h = altura - margem * 2 - destaque_h - espaco

    colar_card(
        fundo,
        pegar(imagens, 0),
        margem,
        margem,
        largura - margem * 2,
        destaque_h,
        destaque=True,
    )

    card_w = (largura - margem * 2 - espaco * 3) // 4
    y = margem + destaque_h + espaco

    for i in range(4):
        x = margem + i * (card_w + espaco)
        colar_card(fundo, pegar(imagens, i + 1), x, y, card_w, baixo_h)

    return fundo


def layout_05_mosaico_cheio(fundo, imagens):
    margem = 10
    espaco = 8
    largura, altura = fundo.size

    esquerda_w = 620
    direita_w = largura - margem * 2 - esquerda_w - espaco

    topo_h = 560
    baixo_h = altura - margem * 2 - topo_h - espaco

    colar_card(
        fundo,
        pegar(imagens, 0),
        margem,
        margem,
        esquerda_w,
        topo_h,
        destaque=True,
    )

    x_dir = margem + esquerda_w + espaco
    dir_card_h = (topo_h - espaco) // 2

    colar_card(fundo, pegar(imagens, 1), x_dir, margem, direita_w, dir_card_h)
    colar_card(
        fundo,
        pegar(imagens, 2),
        x_dir,
        margem + dir_card_h + espaco,
        direita_w,
        dir_card_h,
    )

    card_baixo_w = (largura - margem * 2 - espaco * 2) // 3
    y_baixo = margem + topo_h + espaco

    for i in range(3):
        x = margem + i * (card_baixo_w + espaco)
        colar_card(fundo, pegar(imagens, i + 3), x, y_baixo, card_baixo_w, baixo_h)

    return fundo


def layout_06_destaque_centro_com_laterais(fundo, imagens):
    margem = 10
    espaco = 8
    largura, altura = fundo.size

    lateral_w = 250
    centro_w = largura - margem * 2 - lateral_w * 2 - espaco * 2

    card_lat_h = (altura - margem * 2 - espaco * 2) // 3

    for i in range(3):
        y = margem + i * (card_lat_h + espaco)
        colar_card(fundo, pegar(imagens, i + 1), margem, y, lateral_w, card_lat_h)

    x_centro = margem + lateral_w + espaco

    colar_card(
        fundo,
        pegar(imagens, 0),
        x_centro,
        margem,
        centro_w,
        altura - margem * 2,
        destaque=True,
    )

    x_dir = x_centro + centro_w + espaco

    for i in range(3):
        y = margem + i * (card_lat_h + espaco)
        colar_card(fundo, pegar(imagens, i + 4), x_dir, y, lateral_w, card_lat_h)

    return fundo


def layout_07_quadros_compactos(fundo, imagens):
    margem = 10
    espaco = 8
    largura, altura = fundo.size

    topo_h = 510
    baixo_h = altura - margem * 2 - topo_h - espaco

    destaque_w = 650
    lateral_w = largura - margem * 2 - destaque_w - espaco

    colar_card(
        fundo,
        pegar(imagens, 0),
        margem,
        margem,
        destaque_w,
        topo_h,
        destaque=True,
    )

    x_lateral = margem + destaque_w + espaco
    lateral_h = (topo_h - espaco) // 2

    colar_card(fundo, pegar(imagens, 1), x_lateral, margem, lateral_w, lateral_h)
    colar_card(
        fundo,
        pegar(imagens, 2),
        x_lateral,
        margem + lateral_h + espaco,
        lateral_w,
        lateral_h,
    )

    baixo_w = (largura - margem * 2 - espaco * 2) // 3
    y = margem + topo_h + espaco

    for i in range(3):
        x = margem + i * (baixo_w + espaco)
        colar_card(fundo, pegar(imagens, i + 3), x, y, baixo_w, baixo_h)

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

    if len(imagens) >= 6:
        layouts = [
            layout_01_grade_2x3,
            layout_05_mosaico_cheio,
            layout_06_destaque_centro_com_laterais,
            layout_07_quadros_compactos,
        ]
    elif len(imagens) >= 5:
        layouts = [
            layout_04_destaque_topo_mais_4,
            layout_05_mosaico_cheio,
            layout_07_quadros_compactos,
        ]
    else:
        layouts = [
            layout_02_destaque_direita_com_coluna,
            layout_03_destaque_esquerda_com_coluna,
            layout_04_destaque_topo_mais_4,
        ]

    layout = random.choice(layouts)
    fundo = layout(fundo, imagens)

    caminho_logo = baixar_logo()
    fundo = aplicar_marca_dagua(fundo, caminho_logo)

    nome_saida = f"colagem_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
    caminho_saida = os.path.join(PASTA_COLAGENS, nome_saida)

    fundo.save(caminho_saida, quality=95, optimize=True)

    return caminho_saida