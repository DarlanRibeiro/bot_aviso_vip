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

from drive_publico import baixar_imagens_recentes
from analisador_roi import selecionar_top_roi
from colagem import criar_colagem
from telegram_post import enviar_post
from historico import filtrar_nao_usadas, registrar_usadas


def limpar_temp():
    if os.path.exists(PASTA_TEMP):
        shutil.rmtree(PASTA_TEMP, ignore_errors=True)

    os.makedirs(PASTA_TEMP, exist_ok=True)


def executar():
    print("=" * 60)
    print(f"Execução iniciada: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")

    try:
        limpar_temp()

        print("Baixando imagens recentes do Google Drive...")
        imagens = baixar_imagens_recentes(limite=LIMITE_IMAGENS_RECENTES)

        if not imagens:
            print("Nenhuma imagem encontrada.")
            return

        print(f"{len(imagens)} imagens baixadas.")

        imagens_nao_usadas = filtrar_nao_usadas(imagens)

        print(f"{len(imagens_nao_usadas)} imagens novas ainda não usadas.")

        if len(imagens_nao_usadas) >= QUANTIDADE_COLAGEM:
            print("Usando apenas imagens novas.")
            imagens_para_analisar = imagens_nao_usadas
            deve_registrar_historico = True
        else:
            print("Poucas imagens novas. Reutilizando imagens existentes.")
            imagens_para_analisar = imagens
            deve_registrar_historico = False

        print("Analisando porcentagens verdes...")
        top = selecionar_top_roi(
            imagens_para_analisar,
            quantidade=QUANTIDADE_COLAGEM
        )

        print("Top imagens selecionadas:")
        for item in top:
            print(f"{item['nome']} | ROI: {item['roi']}%")

        if len(top) < QUANTIDADE_COLAGEM:
            print("Menos imagens do que o necessário para montar a colagem.")
            return

        print("Criando colagem com layout variável...")
        colagem = criar_colagem(top)

        print(f"Colagem criada: {colagem}")

        print("Enviando post no Telegram...")
        asyncio.run(enviar_post(colagem))

        if deve_registrar_historico:
            registrar_usadas(top)
            print("Histórico atualizado com imagens novas.")
        else:
            print("Post feito com imagens reutilizadas. Histórico não alterado.")

        print("Post enviado com sucesso.")

    except Exception as erro:
        print(f"ERRO GERAL: {erro}")

    print("=" * 60)


def iniciar_agendador():
    print("BOT AVISO VIP iniciado no Railway.")
    print(f"Intervalo: a cada {INTERVALO_HORAS} horas.")

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