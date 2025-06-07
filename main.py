import aiohttp
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, ContextTypes, filters

BOT_TOKEN = "7721304293:AAESzxmIppuurX-_9XEd4fcxkeRHsmtkYMo"
USDT_AMOUNT = 279

TRC20_ADDRESS = "TSViFWncAuWxL1ADua7VwCk96gxAbL8TzS"
BEP20_ADDRESS = "0x4a3E77d046A89121D0911E132C938b2077ad3E00"
BSC_API_KEY = "RSCQ9ID2UBCIMXZZPPN67J23RCHW891G8N"

CHANNEL_ID = -1002185480944
ADMIN_ID = 813287836

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton("✅ Я оплатил", callback_data="paid")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    msg = (
        f"💳 *Оплата подписки — 279 USDT (пожизненно)*\n\n"
        f"Вы можете отправить USDT в любой сети:\n\n"
        f"*TRC20:*\n`{TRC20_ADDRESS}`\n\n"
        f"*BEP20:*\n`{BEP20_ADDRESS}`\n\n"
        f"После оплаты нажмите кнопку ниже и отправьте хеш (TX ID)."
    )
    await update.message.reply_text(msg, reply_markup=reply_markup, parse_mode="Markdown")

async def paid_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    await update.callback_query.message.reply_text("🔁 Пожалуйста, введите хеш (TX ID) вашей транзакции.")

async def handle_tx(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tx_hash = update.message.text.strip()
    user_id = update.effective_user.id
    username = update.effective_user.username or "NoUsername"

    await update.message.reply_text("⏳ Проверяю транзакцию...")

    valid = await check_trx(tx_hash) or await check_bsc(tx_hash)

    if valid:
        try:
            await context.bot.invite_chat_member(CHANNEL_ID, user_id)
            await update.message.reply_text("✅ Оплата подтверждена! Вы добавлены в закрытый канал.")
        except Exception as e:
            await update.message.reply_text("⚠️ Ошибка при добавлении в канал. Свяжитесь с админом.")
            print(f"Ошибка добавления: {e}")

        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=f"💰 Оплата от @{username} (ID: {user_id}) подтверждена.\nTX: `{tx_hash}`",
            parse_mode="Markdown"
        )
    else:
        await update.message.reply_text("❌ Транзакция не найдена или не соответствует условиям.\nПроверьте сумму, сеть и адрес получателя.")

async def check_trx(tx_hash):
    url = f"https://apilist.tronscanapi.com/api/transaction-info?hash={tx_hash}"

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as r:
                if r.status != 200:
                    return False
                data = await r.json()

        transfers = data.get("tokenTransferInfo", [])
        for tx in transfers:
            if (
                tx.get("to_address") == TRC20_ADDRESS and
                tx.get("symbol") == "USDT" and
                float(tx.get("amount", 0)) >= USDT_AMOUNT
            ):
                return True
        return False
    except Exception as e:
        print(f"Ошибка TRONSCAN: {e}")
        return False

async def check_bsc(tx_hash):
    url = f"https://api.bscscan.com/api?module=account&action=tokentx&txhash={tx_hash}&apikey={BSC_API_KEY}"

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as r:
                if r.status != 200:
                    return False
                result = (await r.json()).get("result", [])

        for tx in result:
            if (
                tx.get("to", "").lower() == BEP20_ADDRESS.lower() and
                tx.get("tokenSymbol") == "USDT" and
                float(tx.get("value", 0)) / (10 ** int(tx.get("tokenDecimal", 6))) >= USDT_AMOUNT
            ):
                return True
        return False
    except Exception as e:
        print(f"Ошибка BSC API: {e}")
        return False

if name == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.

add_handler(CallbackQueryHandler(paid_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_tx))

    print("🤖 Бот запущен...")
    app.run_polling()
