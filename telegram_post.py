from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup

from config import (
    TELEGRAM_BOT_TOKEN,
    TELEGRAM_CHANNEL_ID,
    TELEGRAM_LINK_VIP,
    TELEGRAM_LINK_SAIBA_MAIS,
)


TEXTO_POST = """
🚨 Quer receber operações todos os dias e ter um acompanhamento de verdade?

🐉🤑 Na nossa sala você acompanha entradas em tempo real, recebe análises do mercado e tem acesso às estratégias que utilizamos em Futuros, Spot e Scalping.

⚠️ Sem precisar ficar o dia inteiro analisando gráficos sozinho 👀
"""


async def enviar_post(caminho_imagem):
    bot = Bot(token=TELEGRAM_BOT_TOKEN)

    teclado = InlineKeyboardMarkup([
        [InlineKeyboardButton("🥇 Vip", url=TELEGRAM_LINK_VIP)],
        [InlineKeyboardButton("🐬 Saiba mais", url=TELEGRAM_LINK_SAIBA_MAIS)],
    ])

    with open(caminho_imagem, "rb") as foto:
        await bot.send_photo(
            chat_id=TELEGRAM_CHANNEL_ID,
            photo=foto,
            caption=TEXTO_POST,
            reply_markup=teclado,
        )