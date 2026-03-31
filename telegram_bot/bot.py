import logging
import asyncio
from telegram.ext import ApplicationBuilder, MessageHandler, filters, CommandHandler
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ConversationHandler, filters, MessageHandler
from shared.shared.config.Settings import Settings
from .handlers.request_handlers import get_balance, handle_message
from .handlers.account_handler import (
    start_command, start_link_mt5, process_login, 
    process_pass, process_server, list_accounts, delete_account,
    LINK_STEP_LOGIN, LINK_STEP_PASS, LINK_STEP_SERVER
)

def main():
    app = ApplicationBuilder().token(Settings.TELEGRAM_BOT_TOKEN).build()

    # The Link Account Conversation
    link_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(start_link_mt5, pattern="^link_mt5$")],
        states={
            LINK_STEP_LOGIN: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_login)],
            LINK_STEP_PASS: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_pass)],
            LINK_STEP_SERVER: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_server)],
        },
        fallbacks=[CommandHandler("cancel", lambda u, c: ConversationHandler.END)],
        allow_reentry=True
    )

    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(link_conv)
    app.add_handler(CallbackQueryHandler(list_accounts, pattern="^list_accounts$"))
    app.add_handler(CallbackQueryHandler(delete_account, pattern="^del_"))
    app.add_handler(CallbackQueryHandler(start_command, pattern="^back_main$")) # Reuse start for main menu
    
    # And then handle the request
    app.add_handler(CommandHandler("balance", get_balance))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))

    print("Bot is running...🤖")

    app.run_polling()

 # Run as main
if __name__ == "__main__":
    main()