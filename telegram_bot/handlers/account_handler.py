import json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from modules.account_manager.account_manager.manager.user_manager import UserManager
from modules.account_manager.account_manager.models.user_model import User
from modules.account_manager.account_manager.models.mt5_acc_model import Mt5Account
from modules.account_manager.account_manager.models.binance_acc_model import BinanceAccount
from modules.account_manager.account_manager.database import SessionLocal # Assume you defined a session factory
from shared.shared.security import ( encrypt_val, generate_blind_index, decrypt_val )
from psycopg2.errors import InvalidTextRepresentation


def _get_active_account_display(user) -> str:
    """Return a human-readable string describing the user's active account."""
    active = user.active_account
    if active is None:
        return "None"
    if isinstance(active, str):
        try:
            active = json.loads(active)
        except (json.JSONDecodeError, TypeError):
            return "None"
    broker = active.get("broker", "?")
    account = active.get("account", "?")
    return f"{account} ({broker})"


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
    # Build active-account label for display
    try:
        active_label = _get_active_account_display(user)
    except Exception:
        active_label = "None"

    # Main Menu
    keyboard = [
        [InlineKeyboardButton(f"🔄 Active: {active_label}", callback_data="toggle_active_account")],
        [InlineKeyboardButton("🔗 Link MT5 Account", callback_data="link_mt5")],
        [InlineKeyboardButton("🔗 Link to Binance Account", callback_data="link_binance")],
        [InlineKeyboardButton("📂 My Exness Accounts", callback_data="list_mt5_accounts")],
        [InlineKeyboardButton("📂 My Binance Accounts", callback_data="list_binance_accounts")],
        [InlineKeyboardButton("❓ Help", callback_data="help")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(text, reply_markup=reply_markup, parse_mode="Markdown")


# Account view and Delete handlers

async def list_mt5_accounts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    tid = update.effective_user.id
    
    with SessionLocal() as session:
        u_mgr = UserManager(session)
        user = u_mgr._get_by_telegram_id(tid)
        
        accounts = user.mt5_accounts
        if not accounts:
            await query.edit_message_text("You have no linked Exness account.", 
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Back", callback_data="back_main")]]))
            return

        text = "📂 ***Your Linked Accounts:***\n\n"
        keyboard = []
        for acc in accounts:
            # We don't show the real login/pass here for safety
            
            device_id = decrypt_val(acc.encrypted_device_id)
            text += f"🔹***Name: {acc.account_name} | Device Link ID: {device_id}*** \n"
            keyboard.append([InlineKeyboardButton(f"❌ Delete {acc.account_name}", callback_data=f"del_mt5_{acc.id}")])
        
        keyboard.append([InlineKeyboardButton("⬅️ Back", callback_data="back_main")])
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

async def list_binance_accounts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    tid = update.effective_user.id
    
    with SessionLocal() as session:
        u_mgr = UserManager(session)
        user = u_mgr._get_by_telegram_id(tid)
        
        accounts = user.binance_accounts
        if not accounts:
            await query.edit_message_text("You have no linked Binance account.", 
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Back", callback_data="back_main")]]))
            return

        text = "📂 ***Your Linked Binance Accounts:***\n\n"
        keyboard = []
        for account in accounts:
            # We don't show the real login/pass here for safety
            
            text += f"🔹***Name: {account.account_name}*** \n"
            keyboard.append([InlineKeyboardButton(f"❌ Delete {account.account_name}", callback_data=f"del_bin_{account.id}")])
        
        keyboard.append([InlineKeyboardButton("⬅️ Back", callback_data="back_main")])
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

async def back_to_main(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the 'Back' button to return to the start menu."""
    query = update.callback_query
    await query.answer()

    tid = update.effective_user.id
    active_label = "None"
    try:
        with SessionLocal() as session:
            u_mgr = UserManager(session)
            user = u_mgr._get_by_telegram_id(tid)
            if user:
                text = "Welcome back! Use the menu below to manage your accounts."
                active_label = _get_active_account_display(user)
            else:
                text = "👋 ***Welcome to the Trading Bot!***\nUse the menu below to get started."
    except Exception as e:
        print(e)
        text = "Use the menu below to manage your accounts."

    keyboard = [
        [InlineKeyboardButton(f"🔄 Active: {active_label}", callback_data="toggle_active_account")],
        [InlineKeyboardButton("🔗 Link MT5 Account", callback_data="link_mt5")],
        [InlineKeyboardButton("🔗 Link Binance Account", callback_data="link_binance")],
        [InlineKeyboardButton("📂 My Exness Accounts", callback_data="list_mt5_accounts")],
        [InlineKeyboardButton("📂 My Binance Accounts", callback_data="list_binance_accounts")],
        [InlineKeyboardButton("❓ Help", callback_data="help")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text, reply_markup=reply_markup, parse_mode="Markdown")


async def delete_account(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    callback = query.data.split("_")
    is_mt5 = callback[1] == 'mt5'
    acc_id = int(callback[-1])
    
    with SessionLocal() as session:
        acc = session.query(Mt5Account if is_mt5 else BinanceAccount).get(acc_id)
        if acc:
            session.delete(acc)
            session.commit()
    
    await query.answer("Account Deleted.")
    
    # Refresh list
    if is_mt5:
        await list_mt5_accounts(update, context)
    else:
        await list_binance_accounts(update, context)
    
    

async def toggle_active_account(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show all linked accounts (MT5 + Binance) so the user can pick the active one."""
    query = update.callback_query
    await query.answer()
    tid = update.effective_user.id

    with SessionLocal() as session:
        u_mgr = UserManager(session)
        user = u_mgr._get_by_telegram_id(tid)

        if not user:
            await query.edit_message_text("⚠️ User not found. Please /start first.")
            return

        active_label = _get_active_account_display(user)
        mt5_accounts = user.mt5_accounts
        binance_accounts = user.binance_accounts

        if not mt5_accounts and not binance_accounts:
            await query.edit_message_text(
                "You have no linked accounts yet. Link one first!",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔗 Link MT5 Account", callback_data="link_mt5")],
                    [InlineKeyboardButton("🔗 Link Binance Account", callback_data="link_binance")],
                    [InlineKeyboardButton("⬅️ Back", callback_data="back_main")]
                ])
            )
            return

        text = (
            f"🔄 ***Select Active Account***\n\n"
            f"Current active: ***{active_label}***\n\n"
            f"Choose an account below to set as active:\n"
        )
        keyboard = []

        # MT5 accounts
        if mt5_accounts:
            text += "\n__MT5 Accounts:__\n"
            for acc in mt5_accounts:
                device_id = decrypt_val(acc.encrypted_device_id)
                text += f"  🔹 {acc.account_name} Device Link ID: {device_id}\n"
                keyboard.append([
                    InlineKeyboardButton(
                        f"✅ {acc.account_name} (MT5)",
                        callback_data=f"setactive_mt5_{acc.id}"
                    )
                ])

        # Binance accounts
        if binance_accounts:
            text += "\n__Binance Accounts:__\n"
            for acc in binance_accounts:
                text += f"  🔹 {acc.account_name}\n"
                keyboard.append([
                    InlineKeyboardButton(
                        f"✅ {acc.account_name} (Binance)",
                        callback_data=f"setactive_bin_{acc.id}"
                    )
                ])

        keyboard.append([InlineKeyboardButton("⬅️ Back", callback_data="back_main")])
        await query.edit_message_text(
            text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown"
        )


async def set_active_account(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Persist the user's choice of active account."""
    query = update.callback_query
    callback = query.data  # e.g. "setactive_mt5_3" or "setactive_bin_5"
    parts = callback.split("_")
    # parts: ['setactive', 'mt5'/'bin', '<id>']
    broker_tag = parts[1]  # 'mt5' or 'bin'
    acc_id = int(parts[2])

    with SessionLocal() as session:
        u_mgr = UserManager(session)
        tid = update.effective_user.id
        user = u_mgr._get_by_telegram_id(tid)

        if not user:
            await query.answer("⚠️ User not found.", show_alert=True)
            return

        if broker_tag == "mt5":
            acc = session.query(Mt5Account).filter_by(id=acc_id, user_id=user.id).first()
            if not acc:
                await query.answer("Account not found.", show_alert=True)
                return
            new_active = {"broker": "MT5", "account": acc.account_name, "account_id": acc.id}
        else:
            acc = session.query(BinanceAccount).filter_by(id=acc_id, user_id=user.id).first()
            if not acc:
                await query.answer("Account not found.", show_alert=True)
                return
            new_active = {"broker": "Binance", "account": acc.account_name, "account_id": acc.id}

        u_mgr._toggle_active_account(user.id, new_active)

    await query.answer(f"✅ Active account set to {new_active['account']}")
    # Refresh the selection screen to reflect the change
    await toggle_active_account(update, context)


async def help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pass