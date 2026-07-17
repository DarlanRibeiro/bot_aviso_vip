import os
import shutil
import asyncio

from datetime import datetime
from zoneinfo import ZoneInfo

from apscheduler.schedulers.blocking import BlockingScheduler

from config import (
    LIMITE_IMAGENS_RECENTES,
    QUANTIDADE_COLAGEM,
    PASTA_TEMP,
)

from drive_google import (
    baixar_imagens_novas,
    baixar_imagens_usadas,
    mover_para_usados,
    carregar_historico_postagens,
    salvar_historico_postagens,
)

from analisador_roi import selecionar_top_roi
from historico_postagens import escolher_imagens_do_ciclo
from colagem import criar_colagem
from telegram_post import enviar_post


FUSO_BRASIL = ZoneInfo("America/Bahia")


def agora_brasil():
    return datetime.now(FUSO_BRASIL)


def limpar_temp():
    if os.path.exists(PASTA_TEMP):
        shutil.rmtree(
            PASTA_TEMP,
            ignore_errors=True,
        )

    os.makedirs(
        PASTA_TEMP,
        exist_ok=True,
    )


def remover_duplicadas(imagens):
    vistos = set()
    resultado = []

    for img in imagens:
        file_id = img.get("id")

        if not file_id:
            continue

        if file_id in vistos:
            continue

        vistos.add(file_id)
        resultado.append(img)

    return resultado


def buscar_todas_as_imagens():
    print("Buscando imagens em 01_NOVOS...")

    novas = baixar_imagens_novas(
        limite=LIMITE_IMAGENS_RECENTES,
    )

    print(
        f"{len(novas)} imagens encontradas em 01_NOVOS."
    )

    print("Buscando imagens em 02_USADOS...")

    usadas = baixar_imagens_usadas(
        limite=LIMITE_IMAGENS_RECENTES,
    )

    print(
        f"{len(usadas)} imagens encontradas em 02_USADOS."
    )

    todas = remover_duplicadas(
        novas + usadas
    )

    return novas, usadas, todas


def analisar_imagens_validas(imagens):
    if not imagens:
        return []

    print(
        f"Analisando ROI de {len(imagens)} imagens..."
    )

    # Envia a quantidade total para que nenhuma imagem válida
    # seja eliminada apenas por não estar entre os maiores ROIs.
    validas = selecionar_top_roi(
        imagens,
        quantidade=len(imagens),
    )

    print(
        f"{len(validas)} imagens passaram no ROI mínimo."
    )

    return validas


def exibir_selecionadas(selecionadas):
    print("=" * 60)
    print("IMAGENS ESCOLHIDAS PARA ESTA POSTAGEM")

    for item in selecionadas:
        origem = item.get("origem", "desconhecida")

        print(
            f"{item.get('nome')} "
            f"| ROI: {item.get('roi')}% "
            f"| origem: {origem}"
        )

    print("=" * 60)


def executar():
    print("=" * 60)
    print(
        "Execução iniciada: "
        f"{agora_brasil().strftime('%d/%m/%Y %H:%M:%S')}"
    )

    try:
        limpar_temp()

        novas, usadas, todas = buscar_todas_as_imagens()

        validas = analisar_imagens_validas(todas)

        # Toda imagem que já passou pela análise deixa 01_NOVOS.
        # Isso inclui imagens abaixo do ROI mínimo.
        if novas:
            print(
                "Movendo todas as imagens analisadas "
                "de 01_NOVOS para 02_USADOS..."
            )

            mover_para_usados(novas)

        if len(validas) < QUANTIDADE_COLAGEM:
            print(
                "Não há imagens válidas suficientes para "
                f"formar uma colagem de {QUANTIDADE_COLAGEM} imagens."
            )
            print("=" * 60)
            return

        historico_atual = carregar_historico_postagens()

        selecionadas, novo_historico = escolher_imagens_do_ciclo(
            imagens=validas,
            quantidade=QUANTIDADE_COLAGEM,
            historico=historico_atual,
        )

        if len(selecionadas) < QUANTIDADE_COLAGEM:
            print(
                "Não foi possível selecionar imagens "
                "suficientes para a postagem."
            )
            print("=" * 60)
            return

        exibir_selecionadas(selecionadas)

        print(
            "Criando colagem. O maior ROI entre as quatro "
            "será o destaque..."
        )

        colagem = criar_colagem(selecionadas)

        if not colagem:
            print("Falha ao criar colagem.")
            print("=" * 60)
            return

        print("Enviando para o Telegram...")

        asyncio.run(
            enviar_post(colagem)
        )

        print("Postagem enviada com sucesso.")

        # O histórico só é salvo depois que o Telegram confirmar
        # o envio. Assim uma falha não marca imagens como publicadas.
        historico_salvo = salvar_historico_postagens(
            novo_historico
        )

        if historico_salvo:
            print(
                "As imagens foram registradas "
                "no histórico do ciclo."
            )
        else:
            print(
                "ATENÇÃO: a postagem foi enviada, mas o "
                "histórico não pôde ser salvo."
            )

        print("Finalizado com sucesso.")

    except Exception as erro:
        print(f"ERRO GERAL: {erro}")

    print("=" * 60)


def iniciar_agendador():
    print("BOT AVISO VIP iniciado no Railway.")
    print(
        "Agendamento: segunda a sexta, "
        "uma postagem por dia às 12:00."
    )
    print("Fuso horário: America/Bahia.")

    scheduler = BlockingScheduler(
        timezone=FUSO_BRASIL,
    )

    scheduler.add_job(
        executar,
        trigger="cron",
        day_of_week="mon-fri",
        hour=12,
        minute=0,
        second=0,
        id="postagem_diaria",
        replace_existing=True,
        max_instances=1,
        coalesce=True,
    )

    scheduler.start()


if __name__ == "__main__":
    iniciar_agendador()