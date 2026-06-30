from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup

from config import (
    TELEGRAM_BOT_TOKEN,
    TELEGRAM_CHANNEL_ID,
    TELEGRAM_LINK_VIP,
)


TEXTO_POST = """
🚀 No Grupo VIP ThaiTraderOficial, você acompanha análises macro, insights exclusivos, análises espelho, direcional do mercado, alertas e operações em Futuros e Spot, além de participar de lives com leitura do mercado em tempo real.

📚 Também recebe aulas de gestão financeira, mentalidade, carteira de investimentos e Imposto de Renda com o Professor Emerson, aulas bônus com o método da Thai, panorama semanal e acesso ao chat exclusivo da comunidade.

🎯 Mais do que acompanhar análises, você aprende a desenvolver estratégia, interpretar o mercado com confiança e conquistar cada vez mais autonomia para tomar suas próprias decisões.
"""


async def enviar_post(caminho_imagem):
    bot = Bot(token=TELEGRAM_BOT_TOKEN)

    teclado = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                text="🥇 Grupo VIP | Saiba mais",
                url=TELEGRAM_LINK_VIP,
            )
        ]
    ])

    with open(caminho_imagem, "rb") as foto:
        await bot.send_photo(
            chat_id=TELEGRAM_CHANNEL_ID,
            photo=foto,
            caption=TEXTO_POST,
            reply_markup=teclado,
            connect_timeout=60,
            read_timeout=120,
            write_timeout=120,
            pool_timeout=60,
        )