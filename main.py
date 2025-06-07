import os
import aiohttp
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler,
    MessageHandler, ContextTypes, filters
)

BOT_TOKEN = os.getenv("BOT_TOKEN")
BSCSCAN_API_KEY = os.getenv("BSCSCAN_API_KEY")
ADMIN_ID = 813287836
CHANNEL_ID = -1002185480944

TRC20_ADDRESS = "TSViFWncAuWxL1ADua7VwCk96gxAbL8TzS"
BEP20_ADDRESS = "0x4a3E77d046A89121D0911E132C938b2077ad3E00"
USDT_AMOUNT = 279


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton("✅ Я оплатил", callback_data="paid")]]
    text = (
        f"💳 Оплата подписки — *{USDT_AMOUNT} USDT* (пожизненно)\n\n"
        f"Отправьте *точно* {USDT_AMOUNT} USDT на *любой* из адресов ниже:\n\n"
        f"`TRC20:` `{TRC20_ADDRESS}`\n"
        f"`BEP20:` `{BEP20_ADDRESS}`\n\n"
        "После оплаты нажмите кнопку ниже 👇"
    )
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")


async def paid_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    await update.callback_query.message.reply_text("Пожалуйста, отправьте хеш (TX ID) вашей транзакции.")


async def handle_tx(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tx_id = update.message.text.strip()

    if not tx_id:
        await update.message.reply_text("❌ Пожалуйста, отправьте корректный хеш транзакции.")
        return

    msg = await update.message.reply_text("🔍 Проверяю транзакцию, подождите...")

    # Проверка TRC20
    if len(tx_id) == 64:
        result = await check_trc20(tx_id)
    # Проверка BEP20
    elif tx_id.startswith("0x") and len(tx_id) == 66:
        result = await check_bep20(tx_id)
    else:
        await msg.edit_text("❌ Неверный формат TX ID. Убедитесь, что вы отправили корректный хеш.")
        return

    if result["status"]:
        await msg.edit_text("✅ Платёж подтверждён! Вас скоро добавят в канал.")
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=f"💰 Оплата подтверждена:\n\nTX: `{tx_id}`\nUser: @{update.effective_user.username}",
            parse_mode="Markdown"
        )
    else:
        await msg.edit_text(f"❌ Платёж не найден или недостаточная сумма.\n\nДетали: {result['message']}")


async def check_trc20(tx_id):
    url = f"https://apilist.tronscanapi.com/api/transaction-info?hash={tx_id}"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                data = await resp.json()
                if not data.get("contractRet") == "SUCCESS":
                    return {"status": False, "message": "Транзакция не найдена или не успешна"}

                token_info = data.get("tokenTransferInfo", {})
                if (
                    token_info.get("to_address", "").lower() == TRC20_ADDRESS.lower() and
                    float(token_info.get("amount_str", "0")) / (10 ** 6) >= USDT_AMOUNT
                ):
                    return {"status": True}
                return {"status": False, "message": "Адрес получателя или сумма не совпадают"}
    except Exception as e:
        return {"status": False, "message": str(e)}


async def check_bep20(tx_id):
    url = (
        f"https://api.bscscan.com/api"
        f"?module=account&action=tokentx&txhash={tx_id}&apikey={BSCSCAN_API_KEY}"
    )
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                data = await resp.json()
                txs = data.get("result", [])
                if not txs:
                    return {"status": False, "message": "Транзакция не найдена"}

                for tx in txs:
                    if (
                        tx["to"].lower() == BEP20_ADDRESS.lower() and
                        tx["value"] and
                        int(tx["value"]) / (10 ** int(tx["tokenDecimal"])) >= USDT_AMOUNT and
                        tx["tokenSymbol"] == "USDT"

):
                        return {"status": True}

                return {"status": False, "message": "Адрес получателя или сумма не совпадают"}
    except Exception as e:
        return {"status": False, "message": str(e)}


if name == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(paid_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_tx))

    print("🤖 Бот запущен...")
    app.run_polling()
