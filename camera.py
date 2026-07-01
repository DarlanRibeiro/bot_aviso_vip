from PIL import Image

FUNDO = (5, 9, 22)


def limitar(valor, minimo, maximo):
    return max(minimo, min(valor, maximo))


def modo_seguro(img, tamanho):
    box_w, box_h = tamanho

    img_copy = img.copy()
    img_copy.thumbnail((box_w, box_h), Image.Resampling.LANCZOS)

    canvas = Image.new("RGB", (box_w, box_h), FUNDO)

    x = (box_w - img_copy.width) // 2
    y = (box_h - img_copy.height) // 2

    canvas.paste(img_copy, (x, y))
    return canvas


def imagem_fora_do_padrao(img_w, img_h, bbox_foco=None):
    proporcao = img_w / img_h

    if img_w < 400 or img_h < 400:
        return True

    if bbox_foco is None:
        return True

    if proporcao > 1.10:
        return True

    return False


def ajustar_crop_para_proporcao(x1, y1, x2, y2, img_w, img_h, box_w, box_h):
    target_ratio = box_w / box_h

    crop_w = x2 - x1
    crop_h = y2 - y1

    if crop_h <= 0 or crop_w <= 0:
        return 0, 0, img_w, img_h

    crop_ratio = crop_w / crop_h

    if crop_ratio < target_ratio:
        novo_w = crop_h * target_ratio
        cx = (x1 + x2) / 2
        x1 = cx - novo_w / 2
        x2 = cx + novo_w / 2
    else:
        novo_h = crop_w / target_ratio
        cy = (y1 + y2) / 2
        y1 = cy - novo_h / 2
        y2 = cy + novo_h / 2

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

    x1 = limitar(x1, 0, img_w - 1)
    y1 = limitar(y1, 0, img_h - 1)
    x2 = limitar(x2, x1 + 1, img_w)
    y2 = limitar(y2, y1 + 1, img_h)

    return int(x1), int(y1), int(x2), int(y2)


def calcular_crop_usuario_roi(img_w, img_h, box_w, box_h, bbox_foco=None):
    """
    Nova regra:
    - começa sempre no topo para preservar usuário/avatar/data;
    - termina abaixo do ROI/bloco útil;
    - evita pegar rodapé/QR Code demais;
    - mantém proporção para não distorcer.
    """

    fx1, fy1, fx2, fy2 = bbox_foco

    # Sempre começa no topo para mostrar usuário/avatar/data
    y1 = 0

    # Termina logo abaixo da região útil encontrada pelo OCR
    margem_baixo = img_h * 0.08
    y2 = min(img_h, fy2 + margem_baixo)

    # Garante altura suficiente para usuário + moeda + ROI
    altura_minima = img_h * 0.44
    if (y2 - y1) < altura_minima:
        y2 = min(img_h, y1 + altura_minima)

    # Evita capturar rodapé/QR Code/código de recomendação em excesso
    altura_maxima = img_h * 0.74
    if (y2 - y1) > altura_maxima:
        y2 = y1 + altura_maxima

    # Centraliza horizontalmente no bloco útil
    cx = (fx1 + fx2) / 2

    crop_h = y2 - y1
    crop_w = crop_h * (box_w / box_h)

    x1 = cx - crop_w / 2
    x2 = cx + crop_w / 2

    return ajustar_crop_para_proporcao(
        x1,
        y1,
        x2,
        y2,
        img_w,
        img_h,
        box_w,
        box_h,
    )


def encaixar_sem_distorcer(recorte, tamanho):
    box_w, box_h = tamanho

    recorte.thumbnail((box_w, box_h), Image.Resampling.LANCZOS)

    canvas = Image.new("RGB", (box_w, box_h), FUNDO)

    px = (box_w - recorte.width) // 2
    py = (box_h - recorte.height) // 2

    canvas.paste(recorte, (px, py))
    return canvas


def camera_virtual(img, tamanho, bbox_foco=None, bbox_moeda=None, destaque=False):
    box_w, box_h = tamanho
    img_w, img_h = img.size

    if imagem_fora_do_padrao(img_w, img_h, bbox_foco=bbox_foco):
        return modo_seguro(img, tamanho)

    x1, y1, x2, y2 = calcular_crop_usuario_roi(
        img_w=img_w,
        img_h=img_h,
        box_w=box_w,
        box_h=box_h,
        bbox_foco=bbox_foco,
    )

    recorte = img.crop((x1, y1, x2, y2))

    # Nunca estica: apenas encaixa mantendo proporção
    return encaixar_sem_distorcer(recorte, tamanho)