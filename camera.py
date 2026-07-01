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

    # Se for muito horizontal/quadrada, melhor não arriscar crop agressivo
    if proporcao > 1.05:
        return True

    return False


def calcular_crop_usuario_roi(img_w, img_h, box_w, box_h, bbox_foco=None, bbox_moeda=None):
    """
    Novo enquadramento:
    - mostra o topo do print, onde fica usuário/avatar/data;
    - mostra moeda/operação;
    - mostra ROI;
    - corta preferencialmente QR Code e rodapé.
    """

    proporcao_card = box_w / box_h

    if bbox_foco:
        fx1, fy1, fx2, fy2 = bbox_foco
    else:
        fx1, fy1, fx2, fy2 = 0, 0, img_w, img_h * 0.65

    # Começa no topo para preservar usuário/avatar
    y1 = 0

    # Termina um pouco abaixo do bloco útil detectado pelo OCR
    altura_extra = img_h * (0.10)
    y2 = fy2 + altura_extra

    # Se encontrou moeda, garante que a moeda fique dentro
    if bbox_moeda:
        mx1, my1, mx2, my2 = bbox_moeda
        y2 = max(y2, my2 + img_h * 0.22)

    # Limite inferior: evita pegar QR/rodapé demais
    y2 = min(y2, img_h * 0.72)

    # Limite mínimo: evita crop curto demais
    y2 = max(y2, img_h * 0.45)

    crop_h = y2 - y1
    crop_w = crop_h * proporcao_card

    # Centraliza horizontalmente no bloco útil
    cx = (fx1 + fx2) / 2

    # Para prints de trade, as informações costumam estar mais à esquerda
    # então puxamos levemente para a esquerda.
    cx = cx - img_w * 0.04

    x1 = cx - crop_w / 2
    x2 = cx + crop_w / 2

    # Ajustes para não sair da imagem
    if x1 < 0:
        x2 -= x1
        x1 = 0

    if x2 > img_w:
        excesso = x2 - img_w
        x1 -= excesso
        x2 = img_w

    x1 = limitar(x1, 0, img_w - 1)
    x2 = limitar(x2, x1 + 1, img_w)

    return int(x1), int(y1), int(x2), int(y2)


def camera_virtual(img, tamanho, bbox_foco=None, bbox_moeda=None, destaque=False):
    """
    Enquadramento novo:
    sempre prioriza usuário/avatar + moeda + ROI.
    Não tenta esconder usuário.
    """

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
        bbox_moeda=bbox_moeda,
    )

    recorte = img.crop((x1, y1, x2, y2))
    recorte = recorte.resize((box_w, box_h), Image.Resampling.LANCZOS)

    return recorte