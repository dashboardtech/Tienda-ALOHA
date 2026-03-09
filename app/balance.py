"""
Atomic balance operations for SQLite-safe concurrency.

Uses raw UPDATE statements with WHERE-clause guards to prevent race conditions
(read-modify-write hazards) when multiple requests modify a user's balance
concurrently.  Also provides idempotency-key checking to block accidental
double-submissions.
"""

import hashlib
import time
from decimal import Decimal

from flask import session
from sqlalchemy import text

from app.extensions import db
from app.models import User

# ---------------------------------------------------------------------------
# Idempotency helpers  (server-side double-submit prevention)
# ---------------------------------------------------------------------------
# We store a small ring-buffer of recent operation hashes in the Flask session.
# Each balance-mutating endpoint computes a fingerprint from (user_id, amount,
# action, timestamp-bucket) and rejects the request when the same fingerprint
# appears twice within the dedup window.

_DEDUP_WINDOW_SECONDS = 10
_MAX_RECENT_OPS = 20


def _op_fingerprint(user_id: int, amount: Decimal, action: str) -> str:
    bucket = int(time.time()) // _DEDUP_WINDOW_SECONDS
    raw = f"{user_id}:{amount}:{action}:{bucket}"
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


def is_duplicate_operation(user_id: int, amount: Decimal, action: str) -> bool:
    fp = _op_fingerprint(user_id, amount, action)
    recent: list = session.get("_balance_ops", [])
    if fp in recent:
        return True
    recent.append(fp)
    session["_balance_ops"] = recent[-_MAX_RECENT_OPS:]
    return False


# ---------------------------------------------------------------------------
# Atomic balance mutations
# ---------------------------------------------------------------------------

def atomic_add_balance(user_id: int, amount: Decimal) -> User:
    """Atomically add *amount* (must be > 0) to the user's balance.

    Returns the refreshed User instance.
    Raises ValueError on invalid inputs.
    """
    if amount <= 0:
        raise ValueError("Amount must be positive")

    result = db.session.execute(
        text("UPDATE user SET balance = balance + :amt WHERE id = :uid"),
        {"amt": float(amount), "uid": user_id},
    )
    if result.rowcount == 0:
        raise ValueError("User not found")

    db.session.flush()
    user = db.session.get(User, user_id)
    db.session.refresh(user)
    return user


def atomic_adjust_balance(user_id: int, delta: Decimal) -> User:
    """Atomically adjust balance by *delta* (positive or negative).

    For negative adjustments the UPDATE includes a guard that prevents the
    balance from going below zero.

    Returns the refreshed User instance.
    Raises ValueError when the user is not found or when the balance would
    go negative.
    """
    if delta >= 0:
        result = db.session.execute(
            text("UPDATE user SET balance = balance + :delta WHERE id = :uid"),
            {"delta": float(delta), "uid": user_id},
        )
    else:
        result = db.session.execute(
            text(
                "UPDATE user SET balance = balance + :delta "
                "WHERE id = :uid AND balance >= :required"
            ),
            {"delta": float(delta), "uid": user_id, "required": float(abs(delta))},
        )

    if result.rowcount == 0:
        user = db.session.get(User, user_id)
        if user is None:
            raise ValueError("User not found")
        raise ValueError("Insufficient balance")

    db.session.flush()
    user = db.session.get(User, user_id)
    db.session.refresh(user)
    return user


def atomic_set_balance(user_id: int, new_balance: Decimal) -> User:
    """Atomically overwrite the balance to an exact value (admin only).

    Raises ValueError when *new_balance* < 0 or user not found.
    """
    if new_balance < 0:
        raise ValueError("Balance cannot be negative")

    result = db.session.execute(
        text("UPDATE user SET balance = :bal WHERE id = :uid"),
        {"bal": float(new_balance), "uid": user_id},
    )
    if result.rowcount == 0:
        raise ValueError("User not found")

    db.session.flush()
    user = db.session.get(User, user_id)
    db.session.refresh(user)
    return user


def atomic_refund_balance(user_id: int, refund_amount: Decimal) -> User:
    """Atomically add a refund to the user's balance.

    Thin wrapper around atomic_add_balance with clearer intent.
    """
    return atomic_add_balance(user_id, refund_amount)
