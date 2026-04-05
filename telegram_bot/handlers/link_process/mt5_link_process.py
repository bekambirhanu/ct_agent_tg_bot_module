from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler
from modules.account_manager.account_manager.manager.user_manager import UserManager
from modules.account_manager.account_manager.models.mt5_acc_model import Mt5Account
from modules.account_manager.account_manager.database import SessionLocal # Assume you defined a session factory
from shared.shared.security import encrypt_val
# Conversation States
MT5_STEP_NAME, MT5_STEP_LOGIN, MT5_STEP_PASS, MT5_STEP_SERVER = range(4)


async def start_link_mt5(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("📛 Enter your prefered **account name** (a name to remember):", parse_mode="Markdown")
    return MT5_STEP_NAME

async def process_acc_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    account_name = update.message.text
    # auto generate if empty
    if account_name is None:
        import random
        acc_name = await random.randint(1000,9999)
        context.user_data["account_name"] = acc_name
        del random
    else:
        context.user_data["account_name"] = account_name.strip()
    
    await update.message.reply_text("🔢 Enter your **MT5 Login number** (this will be encrypted):", parse_mode="Markdown")
    return MT5_STEP_LOGIN

async def process_login(update: Update, context: ContextTypes.DEFAULT_TYPE):
    login = update.message.text
    # retype if empty
    if login is None:
        await update.message.reply_text("🔁 please Enter your **MT5 Login number** (this will be encrypted for your security):", parse_mode="Markdown")
        return MT5_STEP_LOGIN
    
    context.user_data["link_login"] = login.strip()
    await update.message.reply_text("🔑 Enter your **MT5 Password** (this will be encrypted):", parse_mode="Markdown")
    return MT5_STEP_PASS

async def process_pass(update: Update, context: ContextTypes.DEFAULT_TYPE):
    password = update.message.text
    if password is None:
        await update.message.reply_text("🔁 please Enter your **MT5 password** (this will be encrypted for your security):", parse_mode="Markdown")
        return MT5_STEP_PASS
    
    context.user_data["link_pass"] = password.strip()
    await update.message.reply_text("🌐 Enter your **MT5 Server** (e.g., Exness-Real10)\n(this will be encrypted):", parse_mode="Markdown")
    return MT5_STEP_SERVER

async def process_server(update: Update, context: ContextTypes.DEFAULT_TYPE):
    server = update.message.text
    tid = update.effective_user.id
    if server is None:
        await update.message.reply_text("🔁 please Enter your **MT5 Server** (this will be encrypted for your security):", parse_mode="Markdown")
        return MT5_STEP_SERVER

    with SessionLocal() as session:
        u_mgr = UserManager(session)
        user = u_mgr._get_by_telegram_id(tid)
        
        # Add the account to this user
        new_acc = Mt5Account(
            user_id=user.id,
            account_name=context.user_data["account_name"],
            broker_login= encrypt_val(context.user_data["link_login"]),
            encrypted_password= encrypt_val(context.user_data["link_pass"]),
            broker_server= encrypt_val(server.strip())
        )
        # Assuming you have an MT5Repository or similar
        session.add(new_acc) 
        session.commit()

    await update.message.reply_text("✅ **MT5 Account Linked Successfully!**", parse_mode="Markdown")
    return ConversationHandler.END

