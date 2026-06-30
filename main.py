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
    mover_para_usados,
    reciclar_usados_para_novos,
)

from analisador_roi import selecionar_top_roi
from colagem import criar_colagem
from telegram_post import enviar_post


def limpar_temp():
    if os.path.exists(PASTA_TEMP):
        shutil.rmtree(PASTA_TEMP, ignore_errors=True)

    os.makedirs(PASTA_TEMP, exist_ok=True)


def obter_imagens_para_post():
    imagens = baixar_imagens_novas(limite=LIMITE_IMAGENS_RECENTES)

    if len(imagens) >= QUANTIDADE_COLAGEM:
        return imagens

    print("Poucas imagens em 01_NOVOS. Reciclando 02_USADOS...")

    total = reciclar_usados_para_novos()
    print(f"{total} imagens recicladas de 02_USADOS para 01_NOVOS.")

    return baixar_imagens_novas(limite=LIMITE_IMAGENS_RECENTES)


def executar():
    print("=" * 60)
    print(f"Execução iniciada: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")

    try:
        limpar_temp()

        print("Buscando imagens...")
        imagens = obter_imagens_para_post()

        if len(imagens) < QUANTIDADE_COLAGEM:
            print("Não há imagens suficientes para criar a colagem.")
            return

        print(f"{len(imagens)} imagens encontradas.")

        print("Analisando ROI e escolhendo maiores rentabilidades...")
        top = selecionar_top_roi(imagens, quantidade=QUANTIDADE_COLAGEM)

        if len(top) < QUANTIDADE_COLAGEM:
            print("Poucas imagens passaram no ROI mínimo.")
            return

        print("Selecionadas:")
        for item in top:
            print(f"{item['nome']} | ROI: {item['roi']}%")

        print("Criando colagem com maior ROI em destaque...")
        colagem = criar_colagem(top)

        print("Enviando para Telegram...")
        asyncio.run(enviar_post(colagem))

        print("Movendo imagens usadas para 02_USADOS...")
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