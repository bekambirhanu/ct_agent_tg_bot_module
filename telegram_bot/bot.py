import logging
import asyncio
from telegram.ext import ApplicationBuilder, MessageHandler, filters, CommandHandler
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, filters, MessageHandler
from shared.shared.config.Settings import Settings
from .handlers.request_handlers import get_balance, handle_message
from .handlers.account_handler import start_command, list_mt5_accounts,list_binance_accounts, delete_account, back_to_main, help, toggle_active_account, set_active_account
from .handlers.conversation_handler import mt5_link_conversation, binance_link_conversation

def main():
    """ ### CT-Agent telegram bot starter function """
    
    app = ApplicationBuilder().token(Settings.TELEGRAM_BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(mt5_link_conversation)
    app.add_handler(binance_link_conversation)
    app.add_handler(CallbackQueryHandler(list_mt5_accounts, pattern="^list_mt5_accounts$"))
    app.add_handler(CallbackQueryHandler(list_binance_accounts, pattern="^list_binance_accounts$"))
    app.add_handler(CallbackQueryHandler(toggle_active_account, pattern="^toggle_active_account$"))
    app.add_handler(CallbackQueryHandler(set_active_account, pattern="^setactive_.*"))
    app.add_handler(CallbackQueryHandler(delete_account, pattern="^del_.*"))
    app.add_handler(CallbackQueryHandler(back_to_main, pattern="^back_main$"))
    app.add_handler(CallbackQueryHandler(help, pattern="^help$"))
    
    # And then handle the request
    app.add_handler(CommandHandler("balance", get_balance))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))

    print("Bot is running ")

    app.run_polling()

 # Run as main
if __name__ == "__main__":
    main()