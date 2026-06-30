from PIL import Image

FUNDO = (5, 9, 22)


def limitar(valor, minimo, maximo):
    return max(minimo, min(valor, maximo))


def imagem_fora_do_padrao(img_w, img_h, bbox_foco=None, bbox_moeda=None):
    proporcao = img_w / img_h

    if img_w < 500 or img_h < 500:
        return True

    if proporcao > 0.95:
        return True

    if bbox_foco is None and bbox_moeda is None:
        return True

    return False


def modo_seguro(img, tamanho):
    box_w, box_h = tamanho

    img_copy = img.copy()
    img_copy.thumbnail((box_w, box_h), Image.Resampling.LANCZOS)

    canvas = Image.new("RGB", (box_w, box_h), FUNDO)

    x = (box_w - img_copy.width) // 2
    y = (box_h - img_copy.height) // 2

    canvas.paste(img_copy, (x, y))
    return canvas


def calcular_centro_foco(img_w, img_h, bbox_foco=None):
    if bbox_foco:
        x1, y1, x2, y2 = bbox_foco

        cx = (x1 + x2) / 2
        cy = (y1 + y2) / 2

        cy += (y2 - y1) * 0.20

        return cx, cy

    return img_w * 0.42, img_h * 0.45


def camera_inteligente(img, tamanho, bbox_foco=None, bbox_moeda=None, destaque=False):
    box_w, box_h = tamanho
    img_w, img_h = img.size

    cx, cy = calcular_centro_foco(img_w, img_h, bbox_foco)

    proporcao_card = box_w / box_h

    zoom = 1.32 if destaque else 1.24

    crop_w = img_w / zoom
    crop_h = crop_w / proporcao_card

    if crop_h > img_h:
        crop_h = img_h / zoom
        crop_w = crop_h * proporcao_card

    x1 = cx - crop_w / 2
    y1 = cy - crop_h / 2
    x2 = cx + crop_w / 2
    y2 = cy + crop_h / 2

    if bbox_moeda:
        moeda_y = bbox_moeda[1]
        limite_topo = max(0, moeda_y - img_h * 0.04)

        if y1 < limite_topo:
            deslocamento = limite_topo - y1
            y1 += deslocamento
            y2 += deslocamento

    if x1 < 0:
        x2 -= x1
        x1 = 0

    if y1 < 0:
        y2 -= y1
        y1 = 0

    if x2 > img_w:
        excesso = x2 - img_w
        x1 -= excesso
        x2 = img_w

    if y2 > img_h:
        excesso = y2 - img_h
        y1 -= excesso
        y2 = img_h

    x1 = int(limitar(x1, 0, img_w - 1))
    y1 = int(limitar(y1, 0, img_h - 1))
    x2 = int(limitar(x2, x1 + 1, img_w))
    y2 = int(limitar(y2, y1 + 1, img_h))

    recorte = img.crop((x1, y1, x2, y2))
    recorte = recorte.resize((box_w, box_h), Image.Resampling.LANCZOS)

    return recorte


def camera_virtual(img, tamanho, bbox_foco=None, bbox_moeda=None, destaque=False):
    img_w, img_h = img.size

    if imagem_fora_do_padrao(
        img_w,
        img_h,
        bbox_foco=bbox_foco,
        bbox_moeda=bbox_moeda,
    ):
        return modo_seguro(img, tamanho)

    return camera_inteligente(
        img=img,
        tamanho=tamanho,
        bbox_foco=bbox_foco,
        bbox_moeda=bbox_moeda,
        destaque=destaque,
    )