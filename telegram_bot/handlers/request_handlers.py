import asyncio
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ContextTypes
from shared.shared.config.Settings import Settings
from nlp_parser.parser import TradeParser
from .broker_factory import get_broker_for_user

# Initialize NLP Parser
parser = TradeParser(
    api_key=Settings.MODEL_API_KEY,
    model=Settings.MODEL_NAME,
    base_url=Settings.MODEL_BASE_URL
)

# BALANCE handler

async def get_balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tid = update.effective_user.id

    try:
        broker = get_broker_for_user(tid)
    except ValueError as e:
        await update.message.reply_text(f"⚠️ {e}")
        return

    # Determine broker type from class name
    broker_name = type(broker).__name__  # "BinanceBroker" or "ExnessBroker"
    is_binance = broker_name == "BinanceBroker"

    await update.message.reply_text(
        f"⏳ Checking {'Binance' if is_binance else 'MT5'} account..."
    )

    data = await broker.get_account_info()

    if not data or not data.get("success", False):
        error = data.get("error", "Unknown error") if data else "No response"
        await update.message.reply_text(f"❌ Could not fetch balance.\n{error}")
        return

    if is_binance:
        balances = data.get("balances", [])
        if not balances:
            await update.message.reply_text("💰 No non-zero balances found.")
            return
        lines = [f"💰 **Binance Account Summary**\n"]
        for b in balances[:10]:  # Show top 10
            lines.append(f"🔹 {b['asset']}: {b['free']} (locked: {b['locked']})")
        msg = "\n".join(lines)
    else:
        msg = (
            f"💰 **MT5 Account Summary**\n"
            f"💵 Balance: ${data['balance']}\n"
            f"📈 Equity: ${data['equity']}\n"
            f"🛡️ Free Margin: ${data['margin_free']}"
        )

    await update.message.reply_text(msg, parse_mode="Markdown")


# REQUEST handler

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    tid = update.effective_user.id

    # 1. Process Text via NLP
    result = parser.parse_text(user_text)
    print({"parser": result})
    if not result.success:
        await update.message.reply_text(f"❌ Failed to parse trade: {result.error_message}")
        return

    order = result.order

    # 2. Resolve broker from the user's active account
    try:
        broker = get_broker_for_user(tid)
    except ValueError as e:
        await update.message.reply_text(f"⚠️ {e}")
        return

    broker_name = type(broker).__name__
    is_binance = broker_name == "BinanceBroker"
    broker_label = "Binance" if is_binance else "MT5"

    response_msg = (
        f"✅ **Trade Parsed:**\n"
        f"🔹 Action: {order.action}\n"
        f"🔹 Symbol: {order.symbol}\n"
        f"🔹 Volume: {order.volume}\n"
        f"🔹 SL: {order.sl} | TP: {order.tp}\n\n"
        f"Confirming with {broker_label}..."
    )
    await update.message.reply_text(response_msg)

    # 3. Execute trade
    tempo_message = await update.message.reply_text(
        f"⏳ Sending order to {broker_label}..."
    )
    execution = await broker.execute_order(order)
    await tempo_message.delete()
    await asyncio.sleep(1)

    # 4. Respond
    if execution.get("success"):
        if is_binance:
            msg = (
                f"✅ **Trade Executed on Binance!**\n"
                f"━━━━━━━━━━━━━━━\n"
                f"🆔 **Order ID:** `{execution['ticket']}`\n"
                f"💰 **Price:** `{execution['price']}`\n"
                f"📊 **Symbol:** {order.symbol}\n"
                f"📝 *Manage this trade on your Binance account.*"
            )
        else:
            msg = (
                f"✅ **Trade Executed on MT5!**\n"
                f"━━━━━━━━━━━━━━━\n"
                f"🆔 **Ticket:** `{execution['ticket']}`\n"
                f"💰 **Price:** `{execution['price']}`\n"
                f"📊 **Symbol:** {order.symbol}\n"
                f"📝 *Manage this trade in your MT5 terminal.*"
            )
        await update.message.reply_text(msg, parse_mode="Markdown")
    else:
        print(f"⚠️ Broker Error: \n{execution}")
        await update.message.reply_text(
            f"⚠️ {broker_label} Error: \n{execution.get('error')}\n {execution.get('comment', '')}"
        )
