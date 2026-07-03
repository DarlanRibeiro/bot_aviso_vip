import os
import shutil
import asyncio
from datetime import datetime

from apscheduler.schedulers.blocking import BlockingScheduler

from config import (
    INTERVALO_HORAS,
    LIMITE_IMAGENS_RECENTES,
    QUANTIDADE_COLAGEM,
    PASTA_TEMP,
)

from drive_google import (
    baixar_imagens_novas,
    baixar_imagens_usadas,
    mover_para_usados,
)

from analisador_roi import selecionar_top_roi
from colagem import criar_colagem
from telegram_post import enviar_post


def limpar_temp():
    if os.path.exists(PASTA_TEMP):
        shutil.rmtree(PASTA_TEMP, ignore_errors=True)

    os.makedirs(PASTA_TEMP, exist_ok=True)


def remover_duplicadas(imagens):
    vistos = set()
    resultado = []

    for img in imagens:
        file_id = img.get("id")

        if file_id in vistos:
            continue

        vistos.add(file_id)
        resultado.append(img)

    return resultado


def completar_com_usadas(top_novas):
    faltam = QUANTIDADE_COLAGEM - len(top_novas)

    if faltam <= 0:
        return top_novas

    print(f"Faltam {faltam} imagens. Buscando complemento em 02_USADOS...")

    usadas = baixar_imagens_usadas(limite=LIMITE_IMAGENS_RECENTES)

    if not usadas:
        print("Nenhuma imagem encontrada em 02_USADOS.")
        return top_novas

    ids_ja_usados = {img["id"] for img in top_novas}
    usadas = [img for img in usadas if img["id"] not in ids_ja_usados]

    if not usadas:
        print("02_USADOS não possui imagens diferentes das já selecionadas.")
        return top_novas

    print(f"{len(usadas)} imagens encontradas em 02_USADOS.")

    top_usadas = selecionar_top_roi(usadas, quantidade=faltam)

    if not top_usadas:
        print("Nenhuma imagem de 02_USADOS passou no ROI mínimo.")
        return top_novas

    print("Complemento vindo de 02_USADOS:")
    for item in top_usadas:
        print(f"{item['nome']} | ROI: {item['roi']}%")

    return remover_duplicadas(top_novas + top_usadas)[:QUANTIDADE_COLAGEM]


def selecionar_imagens_para_post():
    print("Buscando imagens em 01_NOVOS...")
    novas = baixar_imagens_novas(limite=LIMITE_IMAGENS_RECENTES)

    print(f"{len(novas)} imagens encontradas em 01_NOVOS.")

    if not novas:
        top_novas = []
    else:
        print("Analisando ROI das imagens novas...")
        top_novas = selecionar_top_roi(novas, quantidade=QUANTIDADE_COLAGEM)

    if len(top_novas) >= QUANTIDADE_COLAGEM:
        return top_novas[:QUANTIDADE_COLAGEM]

    print("Poucas imagens novas passaram no ROI mínimo.")
    selecionadas = completar_com_usadas(top_novas)

    return selecionadas


def executar():
    print("=" * 60)
    print(f"Execução iniciada: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")

    try:
        limpar_temp()

        top = selecionar_imagens_para_post()

        if len(top) < QUANTIDADE_COLAGEM:
            print("Não há imagens suficientes nem em 01_NOVOS nem em 02_USADOS.")
            return

        print("Selecionadas finais:")
        for item in top:
            origem = item.get("origem", "desconhecida")
            print(f"{item['nome']} | ROI: {item['roi']}% | origem: {origem}")

        print("Criando colagem com maior ROI em destaque...")
        colagem = criar_colagem(top)

        if not colagem:
            print("Falha ao criar colagem.")
            return

        print("Enviando para Telegram...")
        asyncio.run(enviar_post(colagem))

        print("Movendo somente imagens novas para 02_USADOS...")
        mover_para_usados(top)

        print("Finalizado com sucesso.")

    except Exception as erro:
        print(f"ERRO GERAL: {erro}")

    print("=" * 60)


def iniciar_agendador():
    print("BOT AVISO VIP iniciado no Railway.")
    print(f"Intervalo: {INTERVALO_HORAS} horas.")

    scheduler = BlockingScheduler()

    scheduler.add_job(
        executar,
        "interval",
        hours=INTERVALO_HORAS,
        next_run_time=datetime.now(),
    )

    scheduler.start()


if __name__ == "__main__":
    iniciar_agendador()