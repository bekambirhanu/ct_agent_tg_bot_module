import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters
from shared.config.Settings import Settings
from nlp_parser.parser import TradeParser

# Initialize NLP Parser
parser = TradeParser(
    api_key=Settings.MODEL_API_KEY,
    model=Settings.MODEL_NAME,
    base_url=Settings.MODEL_BASE_URL
)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    
    # 1. Process Text via NLP
    result = parser.parse_text(user_text)
    print({"parser": result})
    if not result.success:
        await update.message.reply_text(f"❌ Failed to parse trade: {result.error_message}")
        return

    order = result.order
    # 2. Format a confirmation message
    response_msg = (
        f"✅ **Trade Parsed:**\n"
        f"🔹 Action: {order.action}\n"
        f"🔹 Symbol: {order.symbol}\n"
        f"🔹 Volume: {order.volume}\n"
        f"🔹 SL: {order.sl} | TP: {order.tp}\n\n"
        f"Confirming with broker..."
    )
    await update.message.reply_text(response_msg, parse_mode="Markdown")
    
    # TODO: Step 3 will be: Send 'order' to broker-exness module

def main():
    app = ApplicationBuilder().token(Settings.TELEGRAM_BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    
    print("Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()