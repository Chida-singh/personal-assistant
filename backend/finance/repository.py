"""Repository — all database read / write for transactions."""

import pandas as pd
from sqlmodel import Session, select

from ..core.database import engine
from ..core.models import Transaction

# ── column-name mapping between DB (snake_case) and app (Capitalized) ──
_DB_TO_APP = {
    "id": "id",
    "date": "Date",
    "description": "Description",
    "debit": "Debit",
    "credit": "Credit",
    "balance": "Balance",
    "category": "Category",
    "payment_type": "PaymentType",
    "account": "Account",
    "user_confirmed": "user_confirmed",
    "note": "note",
}
_APP_TO_DB = {v: k for k, v in _DB_TO_APP.items()}


def _to_app(row: dict) -> dict:
    return {_DB_TO_APP.get(k, k): v for k, v in row.items() if k != "created_at"}


def _to_db(row: dict) -> dict:
    return {_APP_TO_DB.get(k, k): v for k, v in row.items()}


def load_all() -> list[dict]:
    """Return every transaction as a list of app-key dicts."""
    with Session(engine) as session:
        txns = session.exec(select(Transaction)).all()
        return [_to_app(t.model_dump() if hasattr(t, "model_dump") else t.dict()) for t in txns]


def save_all(rows: list[dict]) -> None:
    """Replace the entire ledger atomically (delete → insert in one transaction)."""
    with Session(engine) as session:
        try:
            for existing in session.exec(select(Transaction)).all():
                session.delete(existing)
            session.flush()
            for row in rows:
                session.add(Transaction(**_to_db(row)))
            session.commit()
        except Exception:
            session.rollback()
            raise


def to_dataframe() -> pd.DataFrame:
    """Return the ledger as a typed DataFrame."""
    rows = load_all()
    if not rows:
        return pd.DataFrame(columns=[
            "id", "Date", "Description", "Debit", "Credit", "Balance",
            "Category", "PaymentType", "Account", "user_confirmed", "note"
        ])
    df = pd.DataFrame(rows)
    df["Debit"] = pd.to_numeric(df.get("Debit", 0.0), errors="coerce").fillna(0.0)
    df["Credit"] = pd.to_numeric(df.get("Credit", 0.0), errors="coerce").fillna(0.0)
    df["Balance"] = pd.to_numeric(df.get("Balance", 0.0), errors="coerce").fillna(0.0)
    return df
