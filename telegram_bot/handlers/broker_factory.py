"""
Broker factory — resolves the correct BaseBroker instance for a Telegram user
based on their active_account setting in the database.
"""

import json
import logging
from shared.shared.interfaces.broker import BaseBroker
from shared.shared.security import decrypt_val
from modules.account_manager.account_manager.database import SessionLocal
from modules.account_manager.account_manager.manager.user_manager import UserManager
from modules.account_manager.account_manager.models.mt5_acc_model import Mt5Account
from modules.account_manager.account_manager.models.binance_acc_model import BinanceAccount

logger = logging.getLogger(__name__)


def get_broker_for_user(telegram_id: int) -> BaseBroker:
    """
    Look up the user's active account and return an initialised broker.

    Returns:
        BaseBroker — either a BinanceBroker or ExnessBroker instance with
        the user's decrypted credentials.

    Raises:
        ValueError: if no active account is set, or the referenced account
                    does not exist in the database.
    """
    with SessionLocal() as session:
        u_mgr = UserManager(session)
        user = u_mgr._get_by_telegram_id(telegram_id)

        if not user:
            raise ValueError("User not found. Please /start first.")

        # ── Parse active_account JSON ────────────────────────────
        active = user.active_account
        if active is None:
            raise ValueError("No active account set. Use the menu to select one.")

        if isinstance(active, str):
            try:
                active = json.loads(active)
            except (json.JSONDecodeError, TypeError):
                raise ValueError("Corrupted active_account data.")

        broker_type = active.get("broker")    # "MT5" or "Binance"
        account_id = active.get("account_id")

        if not broker_type or account_id is None:
            raise ValueError("Active account is incomplete. Please re-select from the menu.")

        # ── Binance path ─────────────────────────────────────────
        if broker_type == "Binance":
            acc = session.query(BinanceAccount).filter_by(
                id=account_id, user_id=user.id
            ).first()

            if not acc:
                raise ValueError(
                    f"Binance account (id={account_id}) not found. "
                    "It may have been deleted."
                )

            api_key = decrypt_val(acc.api_key)
            api_secret = decrypt_val(acc.api_secret)

            # Deferred import to avoid circular / heavy imports at module level
            from binance_broker.adapter import BinanceBroker
            return BinanceBroker(api_key=api_key, api_secret=api_secret)

        # ── MT5 path ─────────────────────────────────────────────
        if broker_type == "MT5":
            acc = session.query(Mt5Account).filter_by(
                id=account_id, user_id=user.id
            ).first()

            if not acc:
                raise ValueError(
                    f"MT5 account (id={account_id}) not found. "
                    "It may have been deleted."
                )

            device_id = decrypt_val(acc.encrypted_device_id)

            from broker_exness.adapter import ExnessBroker
            return ExnessBroker(device_id=device_id)

        raise ValueError(f"Unknown broker type: {broker_type}")
