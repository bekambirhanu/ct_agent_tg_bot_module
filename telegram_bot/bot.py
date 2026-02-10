import logging
import asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters
from shared.config.Settings import Settings
from nlp_parser.parser import TradeParser
from broker_exness.adapter import ExnessBroker

# Initialize NLP Parser
parser = TradeParser(
    api_key=Settings.MODEL_API_KEY,
    model=Settings.MODEL_NAME,
    base_url=Settings.MODEL_BASE_URL
)
broker = ExnessBroker()
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
        await update.message.reply_text(f"🚀 Order Executed! ID: {execution.get('order_id')}")
    else:
        await update.message.reply_text(f"⚠️ Broker Error: \n{execution.get('error')}")
    

def run_bot():
    app = ApplicationBuilder().token(Settings.TELEGRAM_BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    
    print("Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    run_bot()