from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ContextTypes
)
import aiohttp

BOT_TOKEN = "7721304293:AAESzxmIppuurX-_9XEd4fcxkeRHsmtkYMo"
CHANNEL_ID = -1002185480944
ADMIN_ID = 813287836
TRC20_ADDRESS = "TSViFWncAuWxL1ADua7VwCk96gxAbL8TzS"
BEP20_ADDRESS = "0x4a3E77d046A89121D0911E132C938b2077ad3E00"
USDT_AMOUNT = 279

# В этом коде проверка транзакции не реализована, только шаблон

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [
            InlineKeyboardButton(f"TRC20: `{TRC20_ADDRESS}`", callback_data="trc20"),
            InlineKeyboardButton(f"BEP20: `{BEP20_ADDRESS}`", callback_data="bep20"),
        ],
        [InlineKeyboardButton("✅ Я оплатил", callback_data="paid")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        f"Оплата подписки — {USDT_AMOUNT} USDT (пожизненно)\n\n"
        "Оплатите на любой из адресов ниже (клик по адресу скопирует его):",
        reply_markup=reply_markup,
        parse_mode="MarkdownV2"
    )

async def paid_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "paid":
        await query.message.reply_text(
            "Отправьте TX ID (хеш транзакции) для проверки оплаты."
        )
        return
    # Просто подтверждаем выбор адреса, если нужно
    await query.message.reply_text(f"Вы выбрали: {query.data}")

async def handle_tx(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tx_id = update.message.text.strip()
    # Здесь должна быть проверка транзакции через API (Tronscan или BscScan)
    # Пока заглушка
    await update.message.reply_text(
        f"Спасибо! Проверка транзакции {tx_id} пока не реализована.\n"
        "Как только оплата подтвердится, вы будете добавлены в канал."
    )
    # Тут можно добавить логику добавления пользователя в канал через API Telegram

if name == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(paid_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_tx))

    print("🤖 Бот запущен...")
    app.run_polling()
