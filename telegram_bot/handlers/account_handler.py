from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from account_manager.manager.user_manager import UserManager
from modules.account_manager.account_manager.models.user_model import User
from modules.account_manager.account_manager.models.mt5_acc_model import Mt5Account
from modules.account_manager.account_manager.database import SessionLocal # Assume you defined a session factory

# Conversation States
LINK_STEP_LOGIN, LINK_STEP_PASS, LINK_STEP_SERVER = range(3)

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tid = update.effective_user.id
    
    with SessionLocal() as session:
        u_mgr = UserManager(session)
        user = u_mgr.get_by_telegram_id(tid)
        
        if not user:
            # Auto-registration
            user = User(telegram_id=tid)
            u_mgr.add(user)
            text = "👋 **Welcome to the Trading Bot!**\nYou've been registered. Now, let's link your broker."
        else:
            text = "Welcome back! Use the menu below to manage your accounts."

    # Main Menu
    keyboard = [
        [InlineKeyboardButton("➕ Link MT5 Account", callback_data="link_mt5")],
        [InlineKeyboardButton("📂 My Accounts", callback_data="list_accounts")],
        [InlineKeyboardButton("❓ Help", callback_data="help")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(text, reply_markup=reply_markup, parse_mode="Markdown")

# --- Linking Flow ---

async def start_link_mt5(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("🔢 Enter your **MT5 Login ID**(this will be encrypted):")
    return LINK_STEP_LOGIN

async def process_login(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["link_login"] = update.message.text
    await update.message.reply_text("🔑 Enter your **MT5 Password** (this will be encrypted):")
    return LINK_STEP_PASS

async def process_pass(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["link_pass"] = update.message.text
    await update.message.reply_text("🌐 Enter your **MT5 Server** (e.g., Exness-Real10)(this will be encrypted):")
    return LINK_STEP_SERVER

async def process_server(update: Update, context: ContextTypes.DEFAULT_TYPE):
    server = update.message.text
    tid = update.effective_user.id
    
    with SessionLocal() as session:
        u_mgr = UserManager(session)
        user = u_mgr.get_by_telegram_id(tid)
        
        # Add the account to this user
        new_acc = Mt5Account(
            user_id=user.id,
            login=context.user_data["link_login"],
            password=context.user_data["link_pass"],
            server=server
        )
        # Assuming you have an MT5Repository or similar
        session.add(new_acc) 
        session.commit()

    await update.message.reply_text("✅ **MT5 Account Linked Successfully!**")
    return ConversationHandler.END


# Account view and Delete handlers

async def list_accounts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    tid = update.effective_user.id
    
    with SessionLocal() as session:
        u_mgr = UserManager(session)
        user = u_mgr.get_by_telegram_id(tid)
        
        accounts = user.mt5_accounts
        if not accounts:
            await query.edit_message_text("You have no linked accounts.", 
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Back", callback_data="back_main")]]))
            return

        text = "📂 **Your Linked Accounts:**\n\n"
        keyboard = []
        for acc in accounts:
            # We don't show the real login/pass here for safety
            text += f"🔹 Server: `{acc.server}` | ID: `{acc.login[:3]}***` \n"
            keyboard.append([InlineKeyboardButton(f"❌ Delete {acc.login[:4]}", callback_data=f"del_{acc.id}")])
        
        keyboard.append([InlineKeyboardButton("⬅️ Back", callback_data="back_main")])
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

async def delete_account(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    acc_id = int(query.data.split("_")[1])
    
    with SessionLocal() as session:
        acc = session.query(Mt5Account).get(acc_id)
        if acc:
            session.delete(acc)
            session.commit()
    
    await query.answer("Account Deleted.")
    await list_accounts(update, context) # Refresh list