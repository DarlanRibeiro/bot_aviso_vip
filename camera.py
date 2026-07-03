from PIL import Image

FUNDO = (5, 9, 22)


def limitar(valor, minimo, maximo):
    return max(minimo, min(valor, maximo))


def calcular_crop_seguro(img_w, img_h, bbox_foco=None, destaque=False):
    """
    Regra:
    - preservar usuário no topo;
    - preservar moeda e ROI;
    - cortar excesso inferior quando possível;
    - permitir mais zoom sem cortar informações importantes.
    """

    x1 = 0
    x2 = img_w
    y1 = 0

    if bbox_foco:
        _, _, _, fy2 = bbox_foco
        margem_baixo = img_h * (0.06 if destaque else 0.05)
        y2 = fy2 + margem_baixo
    else:
        y2 = img_h * 0.68

    altura_minima = img_h * (0.50 if destaque else 0.46)
    altura_maxima = img_h * (0.76 if destaque else 0.72)

    y2 = max(y2, altura_minima)
    y2 = min(y2, altura_maxima)
    y2 = min(y2, img_h)

    return int(x1), int(y1), int(x2), int(y2)


def expandir_para_proporcao(x1, y1, x2, y2, img_w, img_h, box_w, box_h):
    """
    Ajusta o crop para a proporção do card.
    Não corta topo.
    Expande largura/altura quando necessário.
    """

    target_ratio = box_w / box_h

    crop_w = x2 - x1
    crop_h = y2 - y1

    if crop_w <= 0 or crop_h <= 0:
        return 0, 0, img_w, img_h

    crop_ratio = crop_w / crop_h

    if crop_ratio < target_ratio:
        novo_w = crop_h * target_ratio
        cx = (x1 + x2) / 2

        x1 = cx - novo_w / 2
        x2 = cx + novo_w / 2

    elif crop_ratio > target_ratio:
        novo_h = crop_w / target_ratio

        # Mantém o topo fixo para não cortar usuário
        y2 = y1 + novo_h

    if x1 < 0:
        x2 -= x1
        x1 = 0

    if x2 > img_w:
        excesso = x2 - img_w
        x1 -= excesso
        x2 = img_w

    if y2 > img_h:
        y2 = img_h

    x1 = limitar(x1, 0, img_w - 1)
    x2 = limitar(x2, x1 + 1, img_w)
    y1 = limitar(y1, 0, img_h - 1)
    y2 = limitar(y2, y1 + 1, img_h)

    return int(x1), int(y1), int(x2), int(y2)


def preencher_card_sem_distorcer(recorte, tamanho):
    """
    Preenche o card sem distorcer.
    Usa resize proporcional e crop central se sobrar.
    """

    box_w, box_h = tamanho
    img_w, img_h = recorte.size

    escala = max(box_w / img_w, box_h / img_h)

    novo_w = int(img_w * escala)
    novo_h = int(img_h * escala)

    recorte = recorte.resize((novo_w, novo_h), Image.Resampling.LANCZOS)

    x = (novo_w - box_w) // 2
    y = 0  # topo preservado

    if y + box_h > novo_h:
        y = max(0, novo_h - box_h)

    recorte = recorte.crop((x, y, x + box_w, y + box_h))

    return recorte


def camera_virtual(img, tamanho, bbox_foco=None, bbox_moeda=None, destaque=False):
    img_w, img_h = img.size
    box_w, box_h = tamanho

    x1, y1, x2, y2 = calcular_crop_seguro(
        img_w=img_w,
        img_h=img_h,
        bbox_foco=bbox_foco,
        destaque=destaque,
    )

    x1, y1, x2, y2 = expandir_para_proporcao(
        x1=x1,
        y1=y1,
        x2=x2,
        y2=y2,
        img_w=img_w,
        img_h=img_h,
        box_w=box_w,
        box_h=box_h,
    )

    recorte = img.crop((x1, y1, x2, y2))

    return preencher_card_sem_distorcer(recorte, tamanho)