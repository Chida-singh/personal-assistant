"""Finance core — thin orchestration layer.

Delegates to focused modules:
  parser      — PDF / text → DataFrame
  categorizer — keyword + LLM categorization
  repository  — DB read / write
  analytics   — stats and reports
  charts      — matplotlib chart generation

Public API is intentionally identical to the old monolithic core.py so
that main.py requires zero changes.
"""

import json
import os
import re
import uuid
from pathlib import Path

import pandas as pd
import requests

from . import analytics
from . import categorizer
from . import charts
from . import parser as _parser
from . import repository as _repo

_OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/api/chat")
_DATA_DIR = Path(__file__).resolve().parent.parent / "data"
_DATA_DIR.mkdir(parents=True, exist_ok=True)



# ── Ingestion ──────────────────────────────────────────────────────────────────

def ingest_file(path: str, account: str = "Main") -> tuple[int, str]:
    """Parse a file and append new transactions to the ledger.

    Returns (rows_added, error_message).
    """
    p = Path(path)
    ext = p.suffix.lower()

    try:
        if ext == ".csv":
            df = pd.read_csv(path, on_bad_lines="skip", engine="python")
            df = _parser.normalise_columns(df)
        elif ext == ".pdf":
            df = _parser.parse_transactions_from_text(_parser.extract_pdf_text(path))
        else:
            df = _parser.parse_transactions_from_text(p.read_text(encoding="utf-8", errors="ignore"))
    except Exception as exc:
        return 0, str(exc)

    if "Date" not in df.columns:
        return 0, f"No Date column found. Got: {list(df.columns)}"

    # Ensure all required columns exist with correct types
    for col in ("Debit", "Credit", "Balance"):
        if col not in df.columns:
            df[col] = 0.0
        df[col] = df[col].apply(_parser.clean_amount)

    df.setdefault("Description", "")
    df.setdefault("PaymentType", "")

    df["Date"] = pd.to_datetime(df["Date"], dayfirst=True, errors="coerce")
    df = df.dropna(subset=["Date"]).sort_values("Date").reset_index(drop=True)

    if df.empty:
        return 0, "No valid transactions found after parsing."

    _fix_debit_credit_from_balance(df)

    df["Category"] = df.apply(
        lambda r: categorizer.infer_category(r["Description"], r["Debit"], r["Credit"]),
        axis=1,
    )
    _llm_fill_uncategorized(df)

    return _append_to_ledger(df, account)


def _fix_debit_credit_from_balance(df: pd.DataFrame) -> None:
    """Use balance change between consecutive rows to correct Debit/Credit."""
    if "Balance" not in df.columns or len(df) < 2:
        return
    for i in range(1, len(df)):
        prev, curr = df.at[i - 1, "Balance"], df.at[i, "Balance"]
        if prev == 0 or curr == 0:
            continue
        delta = curr - prev
        amt = max(df.at[i, "Debit"], df.at[i, "Credit"])
        if amt == 0 or abs(amt - abs(delta)) >= 1.0:
            continue
        if delta > 0:
            df.at[i, "Credit"], df.at[i, "Debit"] = amt, 0.0
        else:
            df.at[i, "Debit"], df.at[i, "Credit"] = amt, 0.0


def _llm_fill_uncategorized(df: pd.DataFrame) -> None:
    """Batch-send 'Other' transactions to LLM for improved categorization."""
    mask = df["Category"] == "Other"
    if not mask.any():
        return
    batch = [
        {"id": str(idx), "desc": row["Description"],
         "amt": row["Debit"] if row["Debit"] > 0 else row["Credit"]}
        for idx, row in df[mask].iterrows()
    ]
    results = {}
    for i in range(0, len(batch), 20):
        results.update(categorizer.llm_categorize_batch(batch[i:i + 20]))
    for id_str, cat in results.items():
        try:
            idx = int(id_str) if str(id_str).isdigit() else id_str
            if cat in categorizer.CATEGORIES or cat in ("Transfer", "Income"):
                df.at[idx, "Category"] = cat
        except Exception:
            pass


def _append_to_ledger(df: pd.DataFrame, account: str) -> tuple[int, int]:
    ledger = _repo.load_all()
    existing_sigs = {
        _repo.make_sig(str(r.get("Date", ""))[:10], r.get("Description", ""),
                       float(r.get("Debit", 0)), float(r.get("Credit", 0)))
        for r in ledger
    }

    new_rows = df[["Date", "Description", "Debit", "Credit", "Balance",
                   "Category", "PaymentType"]].to_dict(orient="records")
    added = []
    for r in new_rows:
        r_date = r["Date"].isoformat() if hasattr(r["Date"], "isoformat") else str(r["Date"])
        r["Date"] = r_date
        sig = _repo.make_sig(r_date[:10], r.get("Description", ""),
                             float(r.get("Debit", 0)), float(r.get("Credit", 0)))
        if sig not in existing_sigs:
            r["id"] = str(uuid.uuid4())[:8]
            r["Account"] = account
            added.append(r)
            existing_sigs.add(sig)

    ledger.extend(added)
    _repo.save_all(ledger)
    return len(added), ""


# ── Manual transactions ────────────────────────────────────────────────────────

def add_manual_transaction(
    date: str, description: str, debit: float, credit: float,
    category: str = "", account: str = "Main",
) -> dict:
    row = {
        "id": str(uuid.uuid4())[:8],
        "Date": date, "Description": description,
        "Debit": debit, "Credit": credit, "Balance": 0.0,
        "Category": category or categorizer.infer_category(description, debit, credit),
        "PaymentType": "Manual", "Account": account,
    }
    ledger = _repo.load_all()
    ledger.append(row)
    _repo.save_all(ledger)
    return row


# ── Ledger read helpers ────────────────────────────────────────────────────────

def get_ledger_df() -> pd.DataFrame:
    return _repo.to_dataframe()


def get_accounts() -> list[str]:
    rows = _repo.load_all()
    accs = {r.get("Account", "Main") for r in rows}
    return sorted(accs) or ["Main"]


def clear_ledger() -> None:
    _repo.save_all([])


def get_transactions(
    category: str = "", search: str = "", sort_by: str = "date_desc",
    page: int = 1, limit: int = 50, account: str = "All",
) -> dict:
    rows = _repo.load_all()
    if not rows:
        return {"total": 0, "page": 1, "pages": 1, "transactions": []}

    rows = _filter(rows, account, category, search)
    rows = _sort(rows, sort_by)

    total = len(rows)
    pages = max(1, (total + limit - 1) // limit)
    page = max(1, min(page, pages))
    start = (page - 1) * limit
    return {"total": total, "page": page, "pages": pages, "transactions": rows[start:start + limit]}


def _filter(rows, account, category, search):
    out = []
    for r in rows:
        if account != "All" and r.get("Account", "Main") != account:
            continue
        if category and r.get("Category", "") != category:
            continue
        if search:
            s = search.lower()
            if s not in r.get("Description", "").lower() and s not in r.get("Category", "").lower():
                continue
        out.append(r)
    return out


def _sort(rows, sort_by):
    parts = sort_by.split("_", 1)
    if len(parts) != 2:
        return rows
    field, direction = parts
    key = "Debit" if field.lower() == "amount" else field.capitalize()
    reverse = direction == "desc"

    def val(r):
        v = r.get(key)
        if v is None:
            return 0 if key in ("Debit", "Credit", "Balance") else ""
        return v.lower() if isinstance(v, str) else v

    try:
        return sorted(rows, key=val, reverse=reverse)
    except Exception:
        return rows


# ── Category management ────────────────────────────────────────────────────────

def update_transaction_category(txn_id: str, new_category: str, note: str = None) -> bool:
    rows = _repo.load_all()
    for r in rows:
        if r.get("id") == txn_id:
            if new_category:
                r["Category"] = new_category
                r["user_confirmed"] = True
            if note is not None:
                r["note"] = note
            _repo.save_all(rows)
            return True
    return False


def confirm_transaction(txn_id: str, category: str, note: str = "") -> bool:
    rows = _repo.load_all()
    target = next((r for r in rows if r.get("id") == txn_id), None)
    if not target:
        return False

    target_payee, _ = categorizer.parse_upi_parts(target.get("Description", ""))
    target_key = target_payee or target.get("Description", "")

    changed = False
    for r in rows:
        is_target = r.get("id") == txn_id
        payee, _ = categorizer.parse_upi_parts(r.get("Description", ""))
        same_payee = (payee or r.get("Description", "")) == target_key

        if is_target or (categorizer.is_ambiguous(r) and same_payee):
            r["Category"] = category
            r["user_confirmed"] = True
            if note:
                r["note"] = note
            changed = True

    if changed:
        _repo.save_all(rows)
    return changed


def get_ambiguous_transactions(limit: int = 30) -> list[dict]:
    rows = _repo.load_all()
    seen, result = set(), []
    for r in rows:
        if not categorizer.is_ambiguous(r):
            continue
        payee, _ = categorizer.parse_upi_parts(r.get("Description", ""))
        key = payee or r.get("Description", "")
        if key in seen:
            continue
        seen.add(key)
        result.append({
            "id": r.get("id", ""),
            "Date": str(r.get("Date", ""))[:10],
            "Description": r.get("Description", ""),
            "payee_display": payee.title() if payee else "Unknown Transfer",
            "Debit": r.get("Debit", 0),
            "Credit": r.get("Credit", 0),
            "Category": r.get("Category", "Other"),
        })
        if len(result) >= limit:
            break
    return result


def recategorize_ledger() -> int:
    """Re-run categorization over the whole ledger and fix parse errors."""
    rows = _repo.load_all()
    changed = 0
    for r in rows:
        # Fix rows where both Debit and Credit are non-zero (parse error)
        d, c = float(r.get("Debit", 0)), float(r.get("Credit", 0))
        if d > 0 and c > 0:
            if d >= c:
                r["Credit"] = 0.0
            else:
                r["Debit"] = 0.0
            changed += 1

        if not r.get("user_confirmed"):
            old = r.get("Category", "")
            new = categorizer.infer_category(r.get("Description", ""), r.get("Debit", 0), r.get("Credit", 0))
            if new != old:
                r["Category"] = new
                changed += 1

        r.setdefault("id", str(uuid.uuid4())[:8])
        r.setdefault("Account", "Main")

    if changed:
        _repo.save_all(rows)
    return changed


def analyze(path: str) -> str:
    count, err = ingest_file(path)
    return f"Failed: {err}" if err else f"Added {count} new transactions."


# ── AI Insights ────────────────────────────────────────────────────────────────

def generate_ai_insights() -> dict:
    rows = _repo.load_all()
    if not rows:
        return {"insights": [], "tip": "", "error": "No data yet"}

    df = _repo.to_dataframe()
    report = analytics.generate_report(df)

    cat_lines = "\n".join(
        f"  - {c['category']}: ₹{c['amount']:.0f} ({c['percentage']}%, {c['count']} txns)"
        for c in report.get("category_breakdown", [])[:8]
    )
    merchant_lines = "\n".join(
        f"  - {m['payee']}: ₹{m['amount']:.0f}"
        for m in report.get("top_merchants_by_spend", [])[:5]
    )
    weekday_lines = "\n".join(
        f"  - {d['day']}: ₹{d['amount']:.0f}"
        for d in report.get("weekday_spending", []) if d["amount"] > 0
    )

    prompt = (
        "You are a smart personal finance advisor. Give 3-4 SHORT, SPECIFIC, "
        "personalized insights using ₹ signs and real numbers. Then one actionable tip.\n\n"
        f"Total spent: ₹{report['total_spent']:.0f}\n"
        f"Total received: ₹{report['total_credited']:.0f}\n"
        f"Net flow: ₹{report['net_flow']:.0f}\n"
        f"Total transactions: {report['txn_count']}\n\n"
        f"By category:\n{cat_lines}\n\nTop merchants:\n{merchant_lines}\n\n"
        f"By weekday:\n{weekday_lines}\n\n"
        "Return ONLY valid JSON: {\"insights\": [...], \"tip\": \"\", \"alert\": \"\"}"
    )
    try:
        resp = requests.post(
            _OLLAMA_URL,
            json={"model": os.getenv("LLM_MODEL", "gemma4"),
                  "messages": [{"role": "user", "content": prompt}],
                  "stream": False, "format": "json"},
            timeout=90,
        )
        resp.raise_for_status()
        content = resp.json().get("message", {}).get("content", "{}")
        content = re.sub(r"```(json)?\n?", "", content).replace("```", "").strip()
        result = json.loads(content)
        return {"insights": result.get("insights", []),
                "tip": result.get("tip", ""), "alert": result.get("alert", "")}
    except json.JSONDecodeError:
        return {"insights": [content[:500]], "tip": "", "alert": ""}
    except Exception as exc:
        return {"insights": [], "tip": "", "alert": "", "error": f"Gemma unavailable: {exc}"}


# ── Re-export analytics / charts so main.py imports from one place ─────────────

summary_stats = analytics.summary_stats
generate_report = analytics.generate_report
group_by_period = analytics.group_by_period
category_breakdown = analytics.category_breakdown
payment_type_breakdown = analytics.payment_type_breakdown
weekday_avg_spending = analytics.weekday_avg_spending
top_merchants = analytics.top_merchants

chart_period = charts.chart_period
chart_category_bar = charts.chart_category_bar
chart_category_pie = charts.chart_category_pie
chart_weekday = charts.chart_weekday
chart_payment_type = charts.chart_payment_type
chart_balance_trend = charts.chart_balance_trend
