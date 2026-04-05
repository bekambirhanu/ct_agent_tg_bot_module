from telegram.ext import ConversationHandler, MessageHandler, filters, CallbackQueryHandler, CommandHandler
from telegram_bot.handlers.link_process.mt5_link_process import (
    start_link_mt5, process_acc_name, process_login,
    process_pass, process_server,
    MT5_STEP_LOGIN, MT5_STEP_NAME, MT5_STEP_PASS, MT5_STEP_SERVER
)
link_conversation = ConversationHandler(
    entry_points=[CallbackQueryHandler(start_link_mt5, pattern="^link_mt5$")],
    states={
        MT5_STEP_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_acc_name)],
        MT5_STEP_LOGIN: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_login)],
        MT5_STEP_PASS: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_pass)],
        MT5_STEP_SERVER: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_server)],
    },
    fallbacks=[CommandHandler("cancel", lambda u, c: ConversationHandler.END)],
    allow_reentry=True
)
