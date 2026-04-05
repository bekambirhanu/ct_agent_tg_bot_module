from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from modules.account_manager.account_manager.manager.user_manager import UserManager
from modules.account_manager.account_manager.models.user_model import User
from modules.account_manager.account_manager.models.mt5_acc_model import Mt5Account
from modules.account_manager.account_manager.database import SessionLocal # Assume you defined a session factory
from shared.shared.security import ( encrypt_val, generate_blind_index, decrypt_val )
from psycopg2.errors import InvalidTextRepresentation


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tid = update.effective_user.id
    encrypted_tid = encrypt_val(str(tid))
    try:
        with SessionLocal() as session:
            u_mgr = UserManager(session)
            user = u_mgr._get_by_telegram_id(tid)
            
            if not user:
                hashed_tid = generate_blind_index(str(tid))
                # Auto-registration
                user = User(encrypted_telegram_id=encrypted_tid, telegram_id_hash= hashed_tid)
                u_mgr.add(user)
                text = "👋 ***Welcome to the Trading Bot!***\nYou've been registered. Now, let's link broker Accounts You desire."
            else:
                text = "Welcome back! Use the menu below to manage your accounts."
    except InvalidTextRepresentation as e:
        print(e.pgerror)
    except Exception as e:
        print(e)
    # Main Menu
    keyboard = [
        [InlineKeyboardButton("🔗 Link MT5 Account", callback_data="link_mt5")],
        [InlineKeyboardButton("📂 My Accounts", callback_data="list_accounts")],
        [InlineKeyboardButton("❓ Help", callback_data="help")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(text, reply_markup=reply_markup, parse_mode="Markdown")

# --- Linking Flow ---

# Account view and Delete handlers

async def list_accounts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    tid = update.effective_user.id
    
    with SessionLocal() as session:
        u_mgr = UserManager(session)
        user = u_mgr._get_by_telegram_id(tid)
        
        accounts = user.mt5_accounts
        if not accounts:
            await query.edit_message_text("You have no linked accounts.", 
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Back", callback_data="back_main")]]))
            return

        text = "📂 ***Your Linked Accounts:***\n\n"
        keyboard = []
        for acc in accounts:
            # We don't show the real login/pass here for safety
            
            server = decrypt_val(acc.broker_server)
            text += f"🔹***Name: {acc.account_name} | Server: {server}*** \n"
            keyboard.append([InlineKeyboardButton(f"❌ Delete {acc.account_name}", callback_data=f"del_{acc.id}")])
        
        keyboard.append([InlineKeyboardButton("⬅️ Back", callback_data="back_main")])
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

async def back_to_main(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the 'Back' button to return to the start menu."""
    query = update.callback_query
    await query.answer()

    tid = update.effective_user.id
    try:
        with SessionLocal() as session:
            u_mgr = UserManager(session)
            user = u_mgr._get_by_telegram_id(tid)
            if user:
                text = "Welcome back! Use the menu below to manage your accounts."
            else:
                text = "👋 ***Welcome to the Trading Bot!***\nUse the menu below to get started."
    except Exception as e:
        print(e)
        text = "Use the menu below to manage your accounts."

    keyboard = [
        [InlineKeyboardButton("🔗 Link MT5 Account", callback_data="link_mt5")],
        [InlineKeyboardButton("🔗 Link Binance Account", callback_data="link_binance")],
        [InlineKeyboardButton("📂 My Accounts", callback_data="list_accounts")],
        [InlineKeyboardButton("❓ Help", callback_data="help")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text, reply_markup=reply_markup, parse_mode="Markdown")


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