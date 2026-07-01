from PIL import Image

FUNDO = (5, 9, 22)


def modo_seguro(img, tamanho):
    box_w, box_h = tamanho

    img_copy = img.copy()
    img_copy.thumbnail((box_w, box_h), Image.Resampling.LANCZOS)

    canvas = Image.new("RGB", (box_w, box_h), FUNDO)

    x = (box_w - img_copy.width) // 2
    y = (box_h - img_copy.height) // 2

    canvas.paste(img_copy, (x, y))
    return canvas


def calcular_crop_seguro(img_w, img_h, bbox_foco=None, destaque=False):
    """
    Regra principal:
    nunca cortar usuário, moeda e ROI.

    Estratégia:
    - começa sempre no topo da imagem;
    - mantém a largura inteira da imagem;
    - corta apenas a parte inferior desnecessária;
    - evita QR Code/rodapé quando possível.
    """

    x1 = 0
    x2 = img_w
    y1 = 0

    if bbox_foco:
        _, _, _, fy2 = bbox_foco

        margem_baixo = img_h * (0.10 if destaque else 0.08)

        y2 = fy2 + margem_baixo
    else:
        y2 = img_h * 0.70

    altura_minima = img_h * (0.58 if destaque else 0.52)

    if y2 < altura_minima:
        y2 = altura_minima

    altura_maxima = img_h * (0.82 if destaque else 0.76)

    if y2 > altura_maxima:
        y2 = altura_maxima

    y2 = min(img_h, max(y2, 1))

    return int(x1), int(y1), int(x2), int(y2)


def encaixar_sem_distorcer(recorte, tamanho):
    box_w, box_h = tamanho

    recorte.thumbnail((box_w, box_h), Image.Resampling.LANCZOS)

    canvas = Image.new("RGB", (box_w, box_h), FUNDO)

    px = (box_w - recorte.width) // 2
    py = (box_h - recorte.height) // 2

    canvas.paste(recorte, (px, py))
    return canvas


def camera_virtual(img, tamanho, bbox_foco=None, bbox_moeda=None, destaque=False):
    img_w, img_h = img.size

    x1, y1, x2, y2 = calcular_crop_seguro(
        img_w=img_w,
        img_h=img_h,
        bbox_foco=bbox_foco,
        destaque=destaque,
    )

    recorte = img.crop((x1, y1, x2, y2))

    return encaixar_sem_distorcer(recorte, tamanho)