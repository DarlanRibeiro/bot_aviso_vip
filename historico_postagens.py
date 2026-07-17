import random


def normalizar_historico(historico):
    if not isinstance(historico, dict):
        historico = {}

    usadas_no_ciclo = historico.get("usadas_no_ciclo", [])
    ultimo_lote = historico.get("ultimo_lote", [])
    numero_ciclo = historico.get("numero_ciclo", 1)

    if not isinstance(usadas_no_ciclo, list):
        usadas_no_ciclo = []

    if not isinstance(ultimo_lote, list):
        ultimo_lote = []

    try:
        numero_ciclo = int(numero_ciclo)
    except (TypeError, ValueError):
        numero_ciclo = 1

    return {
        "usadas_no_ciclo": usadas_no_ciclo,
        "ultimo_lote": ultimo_lote,
        "numero_ciclo": numero_ciclo,
    }


def remover_duplicadas_por_id(imagens):
    unicas = []
    ids_vistos = set()

    for imagem in imagens:
        file_id = imagem.get("id")

        if not file_id:
            continue

        if file_id in ids_vistos:
            continue

        ids_vistos.add(file_id)
        unicas.append(imagem)

    return unicas


def lote_e_igual_ao_anterior(imagens, ultimo_lote):
    ids_atuais = {imagem["id"] for imagem in imagens}
    ids_anteriores = set(ultimo_lote)

    return ids_atuais == ids_anteriores


def escolher_amostra(
    imagens,
    quantidade,
    ultimo_lote=None,
    prefixo=None,
):
    """
    Escolhe uma amostra aleatória.

    Quando possível, evita que o conjunto final seja exatamente
    igual ao último conjunto publicado.
    """

    ultimo_lote = ultimo_lote or []
    prefixo = prefixo or []

    if quantidade <= 0:
        return []

    if len(imagens) <= quantidade:
        resultado = imagens.copy()
        random.shuffle(resultado)
        return resultado[:quantidade]

    tentativas = 40

    for _ in range(tentativas):
        sorteadas = random.sample(imagens, quantidade)
        lote_completo = prefixo + sorteadas

        if not lote_e_igual_ao_anterior(lote_completo, ultimo_lote):
            return sorteadas

    return random.sample(imagens, quantidade)


def escolher_imagens_do_ciclo(
    imagens,
    quantidade,
    historico,
):
    """
    Regras:

    1. Não repetir imagem enquanto ainda houver outras não utilizadas.
    2. Embaralhar as imagens em cada ciclo.
    3. Quando o ciclo terminar, iniciar outro automaticamente.
    4. Evitar repetir exatamente o último lote, quando houver
       imagens suficientes para isso.
    """

    imagens = remover_duplicadas_por_id(imagens)
    historico = normalizar_historico(historico)

    if len(imagens) < quantidade:
        return [], historico

    ids_validos = {imagem["id"] for imagem in imagens}

    usadas_no_ciclo = {
        file_id
        for file_id in historico["usadas_no_ciclo"]
        if file_id in ids_validos
    }

    ultimo_lote = [
        file_id
        for file_id in historico["ultimo_lote"]
        if file_id in ids_validos
    ]

    ainda_nao_usadas = [
        imagem
        for imagem in imagens
        if imagem["id"] not in usadas_no_ciclo
    ]

    selecionadas = []
    novo_ciclo_iniciado = False

    # Ainda há imagens suficientes para formar o lote dentro do ciclo atual.
    if len(ainda_nao_usadas) >= quantidade:
        selecionadas = escolher_amostra(
            imagens=ainda_nao_usadas,
            quantidade=quantidade,
            ultimo_lote=ultimo_lote,
        )

        usadas_no_ciclo.update(
            imagem["id"] for imagem in selecionadas
        )

    else:
        # Usa tudo o que ainda falta no ciclo atual.
        restantes_ciclo_anterior = ainda_nao_usadas.copy()
        random.shuffle(restantes_ciclo_anterior)

        selecionadas.extend(restantes_ciclo_anterior)

        faltam = quantidade - len(selecionadas)

        # O ciclo anterior acabou. Começa um novo.
        novo_ciclo_iniciado = True

        ids_ja_selecionados = {
            imagem["id"] for imagem in selecionadas
        }

        candidatas_novo_ciclo = [
            imagem
            for imagem in imagens
            if imagem["id"] not in ids_ja_selecionados
        ]

        complemento = escolher_amostra(
            imagens=candidatas_novo_ciclo,
            quantidade=faltam,
            ultimo_lote=ultimo_lote,
            prefixo=selecionadas,
        )

        selecionadas.extend(complemento)

        # No novo ciclo, somente as imagens usadas como complemento
        # devem ficar marcadas. As anteriores pertenciam ao ciclo encerrado.
        usadas_no_ciclo = {
            imagem["id"] for imagem in complemento
        }

    if novo_ciclo_iniciado:
        numero_ciclo = historico["numero_ciclo"] + 1
    else:
        numero_ciclo = historico["numero_ciclo"]

    novo_historico = {
        "usadas_no_ciclo": list(usadas_no_ciclo),
        "ultimo_lote": [
            imagem["id"] for imagem in selecionadas
        ],
        "numero_ciclo": numero_ciclo,
    }

    return selecionadas, novo_historico