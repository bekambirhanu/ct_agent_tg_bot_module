from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler
from modules.account_manager.account_manager.manager.user_manager import UserManager
from modules.account_manager.account_manager.models.binance_acc_model import BinanceAccount
from modules.account_manager.account_manager.database import SessionLocal # Assume you defined a session factory
from shared.shared.security import encrypt_val


# Conversation State
BINANCE_STEP_NAME, BINANCE_STEP_API_KEY, BINANCE_STEP_API_SECRET = range(3)

async def start_link_binance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("📛 Enter your prefered **account name** (a name to remember):", parse_mode="Markdown")
    return BINANCE_STEP_NAME

async def process_binance_acc_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    account_name = update.message.text
    import random
    # auto generate if empty
    if account_name is None:
        acc_name = await random.randint(1000,9999)
        context.user_data["binance_account_name"] = acc_name
    else:
        context.user_data["binance_account_name"] = account_name.strip() + f"{random.randint(100, 999)}"
    del random
    
    await update.message.reply_text("🔢 Enter your **Binance api key** (this will be encrypted):", parse_mode="Markdown")
    return BINANCE_STEP_API_KEY

async def process_binance_api_key(update: Update, context: ContextTypes.DEFAULT_TYPE):
    api_key = update.message.text
    
    if api_key is None:
        await update.message.reply_text("🔁 Please Enter your **Binance api key** (this will be encrypted for your account's security):", parse_mode="Markdown")
        return BINANCE_STEP_API_KEY

    context.user_data["binance_api_key"] = api_key
    await update.message.reply_text("🔑 Enter your **Binance api secret** (this will be encrypted):", parse_mode="Markdown")
    return BINANCE_STEP_API_SECRET
    
async def process_binance_secret_api(update: Update, context: ContextTypes.DEFAULT_TYPE):
    api_secret = update.message.text
    tid = update.effective_user.id

    if api_secret is None:
        await update.message.reply_text("🔁 Please Enter your **Binance secret api** (this will be encrypted for your account's security):", parse_mode="Markdown")
        return BINANCE_STEP_API_SECRET
    
    with SessionLocal() as session:
        u_mgr = UserManager(session)
        user = u_mgr._get_by_telegram_id(tid)
        
        # Add the account to this user
        new_acc = BinanceAccount(
            user_id=user.id,
            account_name=context.user_data["binance_account_name"],
            api_key= encrypt_val(context.user_data["binance_api_key"]),
            api_secret= encrypt_val(api_secret),
        )
        # Assuming you have a BinanceRepository or similar
        session.add(new_acc)
        session.commit()

    await update.message.reply_text("✅ **Binance Account Linked Successfully!**", parse_mode="Markdown")
    return ConversationHandler.END
