import logging
import asyncio
from telegram.ext import ApplicationBuilder, MessageHandler, filters, CommandHandler
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, filters, MessageHandler
from shared.shared.config.Settings import Settings
from .handlers.request_handlers import get_balance, handle_message
from .handlers.account_handler import start_command, list_accounts, delete_account, back_to_main
from .handlers.conversation_handler import link_conversation

def main():
    app = ApplicationBuilder().token(Settings.TELEGRAM_BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(link_conversation)
    app.add_handler(CallbackQueryHandler(list_accounts, pattern="^list_accounts$"))
    app.add_handler(CallbackQueryHandler(delete_account, pattern="^del_"))
    app.add_handler(CallbackQueryHandler(back_to_main, pattern="^back_main$"))
    
    # And then handle the request
    app.add_handler(CommandHandler("balance", get_balance))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))

    print("Bot is running...🤖")

    app.run_polling()

 # Run as main
if __name__ == "__main__":
    main()