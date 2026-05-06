from warnings import filterwarnings
from telegram.warnings import PTBUserWarning

# To ignore some unnecessary warnings
filterwarnings(action="ignore", message=r".*CallbackQueryHandler", category=PTBUserWarning)

from telegram.ext import ConversationHandler, MessageHandler, filters, CallbackQueryHandler, CommandHandler
from telegram_bot.handlers.link_process.mt5_link_process import (
    start_link_mt5, process_acc_name,
    MT5_STEP_NAME
)
from telegram_bot.handlers.link_process.binance_link_process import (
    start_link_binance, process_binance_acc_name, process_binance_api_key, process_binance_secret_api,
    BINANCE_STEP_NAME, BINANCE_STEP_API_KEY, BINANCE_STEP_API_SECRET
)

mt5_link_conversation = ConversationHandler(
    entry_points=[CallbackQueryHandler(start_link_mt5, pattern="^link_mt5$")],
    states={
        # Metatrade linking
        MT5_STEP_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_acc_name)],
    },
    fallbacks=[CommandHandler("cancel", lambda u, c: ConversationHandler.END)],
    allow_reentry=True
)


binance_link_conversation = ConversationHandler(
    entry_points=[CallbackQueryHandler(start_link_binance, pattern="^link_binance$")],
    states={
        # Binance linking
        BINANCE_STEP_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_binance_acc_name)],
        BINANCE_STEP_API_KEY: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_binance_api_key)],
        BINANCE_STEP_API_SECRET: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_binance_secret_api)],
    },
    fallbacks=[CommandHandler("cancel", lambda u, c: ConversationHandler.END)],
    allow_reentry=True
)