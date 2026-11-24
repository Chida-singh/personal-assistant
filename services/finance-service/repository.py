"""Repository — all database read / write for transactions."""

import uuid

import pandas as pd
from sqlmodel import Session, select

from database import engine
from models import Transaction

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
        return [_to_app(t.dict()) for t in txns]


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
        return pd.DataFrame(
            columns=["id", "Date", "Description", "Debit", "Credit",
                     "Balance", "Category", "PaymentType", "Account"]
        )
    df = pd.DataFrame(rows)
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    for col in ("Debit", "Credit", "Balance"):
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
    df.setdefault("id", [str(uuid.uuid4())[:8] for _ in range(len(df))])
    df["Account"] = df.get("Account", pd.Series("Main", index=df.index)).fillna("Main")
    return df


def make_sig(date: str, desc: str, debit: float, credit: float) -> str:
    """Stable deduplication key (floats normalized to 2 d.p.)."""
    return f"{date}_{desc}_{debit:.2f}_{credit:.2f}"
