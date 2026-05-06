from telegram import Update
from uuid import uuid4
from telegram.ext import ContextTypes, ConversationHandler
from modules.account_manager.account_manager.manager.user_manager import UserManager
from modules.account_manager.account_manager.models.mt5_acc_model import Mt5Account
from modules.account_manager.account_manager.database import SessionLocal # Assume you defined a session factory
from shared.shared.security import encrypt_val
# Conversation States
MT5_STEP_NAME, MT5_STEP_DEVICE_LINK_ID = range(2)


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
    
    await update.message.reply_text("🔢 Generating a unique device link id...", parse_mode="Markdown")

    # Generate a unique device link ID
    device_link_id = uuid4().hex
    tid = update.effective_user.id

    with SessionLocal() as session:
        u_mgr = UserManager(session)
        user = u_mgr._get_by_telegram_id(tid)
        
        # Add the account to this user
        new_acc = Mt5Account(
            user_id=user.id,
            account_name=context.user_data["account_name"],
            encrypted_device_id= encrypt_val(device_link_id.strip())
        )
        # Assuming you have an MT5Repository or similar
        session.add(new_acc) 
        session.commit()

    await update.message.reply_text(f"✅ **MT5 Account Setup successful.**\n device link: ```{device_link_id}```\n\n Note: Remember to copy this link to your MT5 client app and to keep it secure.", parse_mode="Markdown")
    return ConversationHandler.END