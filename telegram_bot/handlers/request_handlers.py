import asyncio
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ContextTypes
from broker_exness.adapter import ExnessBroker
from shared.shared.config.Settings import Settings
from nlp_parser.parser import TradeParser

# Initialize Broker
broker = ExnessBroker()

# Initialize NLP Parser
parser = TradeParser(
    api_key=Settings.MODEL_API_KEY,
    model=Settings.MODEL_NAME,
    base_url=Settings.MODEL_BASE_URL
)
# BALANCE handler

async def get_balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Checking Exness account...")
    data = await broker.get_account_info()
    if data:
        msg = (
            f"💰 **Account Summary**\n"
            f"💵 Balance: ${data['balance']}\n"
            f"📈 Equity: ${data['equity']}\n"
            f"🛡️ Free Margin: ${data['margin_free']}"
        )
        await update.message.reply_text(msg, parse_mode="Markdown")
    else:
        await update.message.reply_text("❌ Could not fetch balance.")

# REQUEST handler

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    
    # 1. Process Text via NLP
    result = parser.parse_text(user_text)
    print({"parser": result})
    if not result.success:
        await update.message.reply_text(f"❌ Failed to parse trade: {result.error_message}")
        return
    
    order = result.order
    
    response_msg = (
        f"✅ **Trade Parsed:**\n"
        f"🔹 Action: {order.action}\n"
        f"🔹 Symbol: {order.symbol}\n"
        f"🔹 Volume: {order.volume}\n"
        f"🔹 SL: {order.sl} | TP: {order.tp}\n\n"
        f"Confirming with broker..."
    )
    await update.message.reply_text(response_msg)
    
    # 2. Execute trade
    tempo_message= await update.message.reply_text("⏳ Sending order to Exness...")
    execution = await broker.execute_order(order)
    await tempo_message.delete()
    await asyncio.sleep(1)

    # 3. Respond
    if execution.get("success"):
        msg = (
            f"✅ **Trade Executed!**\n"
            f"━━━━━━━━━━━━━━━\n"
            f"🆔 **Ticket:** `{execution['ticket']}`\n"
            f"💰 **Price:** `{execution['price']}`\n"
            f"📊 **Symbol:** {order.symbol}\n"
            f"📝 *Manage this trade in your MT5 terminal.*"
        )
        await update.message.reply_text(msg, parse_mode="Markdown")
    else:
        print(f"⚠️ Broker Error: \n{execution}")
        await update.message.reply_text(f"⚠️ Broker Error: \n{execution.get('error')}\n {execution.get('comment')}")
