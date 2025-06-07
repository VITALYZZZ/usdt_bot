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
    keyboard = [[
        InlineKeyboardButton(f"TRC20: `{TRC20_ADDRESS}`", callback_data="none"),
        InlineKeyboardButton(f"BEP20: `{BEP20_ADDRESS}`", callback_data="none")
    ], [InlineKeyboardButton("✅ Я оплатил", callback_data="paid")]]
    text = (
        f"💳 Оплата подписки — *{USDT_AMOUNT} USDT* (пожизненно)\n\n"
        f"Отправьте *точно* {USDT_AMOUNT} USDT на любой из адресов ниже (нажмите, чтобы скопировать):\n\n"
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

    msg = await update.message.reply_text("🔍 Проверяю транзакцию, подождите...")

    if len(tx_id) == 64:
        # Скорее всего TRC20
        result = await check_trc20(tx_id)
    elif tx_id.startswith("0x") and len(tx_id) == 66:
        # Скорее всего BEP20
        result = await check_bep20(tx_id)
    else:
        await msg.edit_text("❌ Неверный формат TX ID. Убедитесь, что вы отправили корректный хеш.")
        return

    if result["status"]:
        await msg.edit_text("✅ Платёж подтверждён! Вас скоро добавят в канал.")
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=f"💰 Оплата подтверждена:\n\nTX: `{tx_id}`\nUser: @{update.effective_user.username or update.effective_user.id}",
            parse_mode="Markdown"
        )
    else:
        await msg.edit_text(f"❌ Платёж не найден или сумма не совпадает.\n\nДетали: {result['message']}")


async def check_trc20(tx_id):
    url = f"https://apilist.tronscanapi.com/api/transaction-info?hash={tx_id}"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                data = await resp.json()
                if data.get("contractRet") != "SUCCESS":
                    return {"status": False, "message": "Транзакция не успешна или не найдена"}

                token_info = data.get("tokenTransferInfo", {})
                to_addr = token_info.get("to_address", "").lower()
                amount_str = token_info.get("amount_str", "0")
                amount = float(amount_str) / 1_000_000  # USDT TRC20 - 6 знаков

                if to_addr == TRC20_ADDRESS.lower() and amount >= USDT_AMOUNT:
                    return {"status": True}
                else:
                    return {"status": False, "message": f"Адрес или сумма не совпадают (адрес: {to_addr}, сумма: {amount})"}
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
                    to_addr = tx["to"].lower()

value = int(tx["value"])
                    decimals = int(tx["tokenDecimal"])
                    amount = value / (10 ** decimals)
                    if (
                        to_addr == BEP20_ADDRESS.lower() and
                        amount >= USDT_AMOUNT and
                        tx["tokenSymbol"] == "USDT"
                    ):
                        return {"status": True}

                return {"status": False, "message": "Адрес или сумма не совпадают"}
    except Exception as e:
        return {"status": False, "message": str(e)}


if name == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(paid_callback, pattern="paid"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_tx))

    print("🤖 Бот запущен...")
    app.run_polling()
