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


def layout_4_hero_direita(fundo, imagens):
    m, e = 10, 8
    W, H = fundo.size

    col_w = 350
    hero_w = W - m * 2 - col_w - e
    card_h = (H - m * 2 - e * 2) // 3

    for i in range(3):
        colar_card(fundo, pegar(imagens, i + 1), m, m + i * (card_h + e), col_w, card_h)

    colar_card(fundo, pegar(imagens, 0), m + col_w + e, m, hero_w, H - m * 2, True)

    return fundo


def layout_4_hero_esquerda(fundo, imagens):
    m, e = 10, 8
    W, H = fundo.size

    col_w = 350
    hero_w = W - m * 2 - col_w - e
    card_h = (H - m * 2 - e * 2) // 3

    colar_card(fundo, pegar(imagens, 0), m, m, hero_w, H - m * 2, True)

    x = m + hero_w + e

    for i in range(3):
        colar_card(fundo, pegar(imagens, i + 1), x, m + i * (card_h + e), col_w, card_h)

    return fundo


def layout_4_grade_2x2(fundo, imagens):
    m, e = 10, 8
    W, H = fundo.size

    card_w = (W - m * 2 - e) // 2
    card_h = (H - m * 2 - e) // 2

    pos = [
        (m, m),
        (m + card_w + e, m),
        (m, m + card_h + e),
        (m + card_w + e, m + card_h + e),
    ]

    for i, (x, y) in enumerate(pos):
        colar_card(fundo, pegar(imagens, i), x, y, card_w, card_h, i == 0)

    return fundo


def layout_4_topo(fundo, imagens):
    m, e = 10, 8
    W, H = fundo.size

    hero_h = 560
    baixo_h = H - m * 2 - hero_h - e
    baixo_w = (W - m * 2 - e * 2) // 3

    colar_card(fundo, pegar(imagens, 0), m, m, W - m * 2, hero_h, True)

    y = m + hero_h + e

    for i in range(3):
        x = m + i * (baixo_w + e)
        colar_card(fundo, pegar(imagens, i + 1), x, y, baixo_w, baixo_h)

    return fundo


def layout_5_hero_topo_4baixo(fundo, imagens):
    m, e = 10, 8
    W, H = fundo.size

    hero_h = 500
    baixo_h = H - m * 2 - hero_h - e
    baixo_w = (W - m * 2 - e * 3) // 4

    colar_card(fundo, pegar(imagens, 0), m, m, W - m * 2, hero_h, True)

    y = m + hero_h + e

    for i in range(4):
        x = m + i * (baixo_w + e)
        colar_card(fundo, pegar(imagens, i + 1), x, y, baixo_w, baixo_h)

    return fundo


def layout_5_mosaico(fundo, imagens):
    m, e = 10, 8
    W, H = fundo.size

    hero_w = 640
    side_w = W - m * 2 - hero_w - e
    topo_h = 610
    baixo_h = H - m * 2 - topo_h - e

    colar_card(fundo, pegar(imagens, 0), m, m, hero_w, topo_h, True)

    x_side = m + hero_w + e
    side_h = (topo_h - e) // 2

    colar_card(fundo, pegar(imagens, 1), x_side, m, side_w, side_h)
    colar_card(fundo, pegar(imagens, 2), x_side, m + side_h + e, side_w, side_h)

    baixo_w = (W - m * 2 - e) // 2
    y = m + topo_h + e

    colar_card(fundo, pegar(imagens, 3), m, y, baixo_w, baixo_h)
    colar_card(fundo, pegar(imagens, 4), m + baixo_w + e, y, baixo_w, baixo_h)

    return fundo


def layout_5_hero_direita(fundo, imagens):
    m, e = 10, 8
    W, H = fundo.size

    left_w = 420
    hero_w = W - m * 2 - left_w - e

    small_h = (H - m * 2 - e * 3) // 4

    for i in range(4):
        colar_card(fundo, pegar(imagens, i + 1), m, m + i * (small_h + e), left_w, small_h)

    colar_card(fundo, pegar(imagens, 0), m + left_w + e, m, hero_w, H - m * 2, True)

    return fundo


def layout_6_grade_2x3(fundo, imagens):
    m, e = 10, 8
    W, H = fundo.size

    card_w = (W - m * 2 - e) // 2
    card_h = (H - m * 2 - e * 2) // 3

    for i in range(6):
        col = i % 2
        row = i // 2
        x = m + col * (card_w + e)
        y = m + row * (card_h + e)
        colar_card(fundo, pegar(imagens, i), x, y, card_w, card_h, i == 0)

    return fundo


def layout_6_hero_mais_5(fundo, imagens):
    m, e = 10, 8
    W, H = fundo.size

    hero_w = 620
    side_w = W - m * 2 - hero_w - e

    colar_card(fundo, pegar(imagens, 0), m, m, hero_w, H - m * 2, True)

    small_h = (H - m * 2 - e * 4) // 5
    x = m + hero_w + e

    for i in range(5):
        colar_card(fundo, pegar(imagens, i + 1), x, m + i * (small_h + e), side_w, small_h)

    return fundo


def layout_6_mosaico_cheio(fundo, imagens):
    m, e = 10, 8
    W, H = fundo.size

    topo_h = 520
    baixo_h = H - m * 2 - topo_h - e

    hero_w = 640
    side_w = W - m * 2 - hero_w - e

    colar_card(fundo, pegar(imagens, 0), m, m, hero_w, topo_h, True)

    x_side = m + hero_w + e
    side_h = (topo_h - e) // 2

    colar_card(fundo, pegar(imagens, 1), x_side, m, side_w, side_h)
    colar_card(fundo, pegar(imagens, 2), x_side, m + side_h + e, side_w, side_h)

    baixo_w = (W - m * 2 - e * 2) // 3
    y = m + topo_h + e

    for i in range(3):
        x = m + i * (baixo_w + e)
        colar_card(fundo, pegar(imagens, i + 3), x, y, baixo_w, baixo_h)

    return fundo


def escolher_layout(qtd):
    if qtd >= 6:
        return random.choice([
            layout_6_grade_2x3,
            layout_6_hero_mais_5,
            layout_6_mosaico_cheio,
        ])

    if qtd == 5:
        return random.choice([
            layout_5_hero_topo_4baixo,
            layout_5_mosaico,
            layout_5_hero_direita,
        ])

    return random.choice([
        layout_4_hero_direita,
        layout_4_hero_esquerda,
        layout_4_grade_2x2,
        layout_4_topo,
    ])


def criar_colagem(imagens_top):
    os.makedirs(PASTA_COLAGENS, exist_ok=True)

    imagens_ordenadas = sorted(
        imagens_top,
        key=lambda x: x["roi"],
        reverse=True,
    )

    imagens_ordenadas = imagens_ordenadas[:6]

    maior = imagens_ordenadas[0]
    demais = imagens_ordenadas[1:]
    random.shuffle(demais)

    imagens = [maior] + demais

    fundo = Image.new("RGB", (1080, 1080), FUNDO)

    layout = escolher_layout(len(imagens))
    fundo = layout(fundo, imagens)

    caminho_logo = baixar_logo()
    fundo = aplicar_marca_dagua(fundo, caminho_logo)

    nome_saida = f"colagem_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
    caminho_saida = os.path.join(PASTA_COLAGENS, nome_saida)

    fundo.save(caminho_saida, quality=95, optimize=True)

    return caminho_saida