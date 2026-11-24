"""Parser — PDF extraction and raw-text → DataFrame conversion."""

import re
from pathlib import Path

import pandas as pd

try:
    import fitz  # PyMuPDF
except ImportError:
    fitz = None


# Regex: matches DD/MM/YYYY, DD-MM-YYYY, DD MMM YYYY, etc. at line start
_DATE_RE = re.compile(r"(\d{1,2}[\s/\-]+(?:[A-Za-z]{3,9}|\d{1,2})[\s/\-]+\d{2,4})")

# Regex: Indian-style amount tokens, e.g. 1,00,000.00 or 500.00Cr
_AMOUNT_RE = re.compile(r"[\d,]+\.\d{1,2}(?:\s*(?:Cr|Dr|CR|DR))?")


def clean_amount(val) -> float:
    """Convert a raw amount string to float.

    Handles: commas, currency symbols, parenthesized negatives (500.00),
    and multi-dot garbage (1.234.56).
    """
    if pd.isna(val) or str(val).strip() in ("", " ", "-"):
        return 0.0

    s = str(val).strip()
    is_negative = s.startswith("(") and s.endswith(")")
    if is_negative:
        s = s[1:-1]

    s = re.sub(r"[^\d.\-]", "", s)

    # Handle multiple dots — keep only the last separator
    if s.count(".") > 1:
        left, right = s.rsplit(".", 1)
        s = left.replace(".", "") + "." + right

    try:
        result = float(s)
        return -result if is_negative else result
    except ValueError:
        return 0.0


def extract_pdf_text(path: str) -> str:
    """Return raw text from all pages of a PDF."""
    if not fitz:
        raise ImportError("PyMuPDF required: pip install pymupdf")
    text = ""
    with fitz.open(path) as doc:
        for page in doc:
            text += page.get_text() + "\n"
    return text


def parse_transactions_from_text(raw: str) -> pd.DataFrame:
    """Convert raw bank-statement text into a DataFrame.

    Supports:
    - DD/MM/YYYY, DD-MM-YYYY, DD MMM YYYY date formats
    - Multi-line transaction descriptions
    - Amounts with Indian comma grouping (1,00,000.00)
    - Cr / Dr suffixes on amount tokens
    - 1-, 2-, or 3-column amount layouts
    """
    lines = raw.split("\n")
    records = []

    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if not line:
            i += 1
            continue

        match = _DATE_RE.match(line)
        if not match:
            i += 1
            continue

        date_str = match.group(1).strip()
        rest = line[match.end():].strip()

        # Collect continuation lines (no date at start)
        j = i + 1
        while j < len(lines):
            next_line = lines[j].strip()
            if not next_line:
                j += 1
                continue
            if _DATE_RE.match(next_line):
                break
            rest += " " + next_line
            j += 1

        # Extract all amount tokens from combined text
        amount_matches = list(_AMOUNT_RE.finditer(rest))
        if not amount_matches:
            i = j
            continue

        desc = rest[: amount_matches[0].start()].strip()
        desc = re.sub(r"\s+", " ", desc)

        amounts = []
        for am in amount_matches:
            raw_amt = am.group(0).strip()
            is_cr = raw_amt.upper().endswith("CR")
            is_dr = raw_amt.upper().endswith("DR")
            num_str = re.sub(r"[^\d.]", "", raw_amt)
            try:
                amounts.append({"val": float(num_str), "cr": is_cr, "dr": is_dr})
            except ValueError:
                continue

        if not amounts or not desc:
            i = j
            continue

        debit, credit, balance = _assign_amounts(amounts)

        records.append({
            "Date": date_str,
            "Description": desc,
            "Debit": debit,
            "Credit": credit,
            "Balance": balance,
        })
        i = j

    return pd.DataFrame(records)


def _assign_amounts(amounts: list[dict]) -> tuple[float, float, float]:
    """Assign extracted amount tokens to (debit, credit, balance)."""
    if len(amounts) >= 3:
        return amounts[-3]["val"], amounts[-2]["val"], amounts[-1]["val"]

    if len(amounts) == 2:
        amt, bal = amounts[0], amounts[1]
        balance = bal["val"]
        if amt["cr"]:
            return 0.0, amt["val"], balance
        if amt["dr"]:
            return amt["val"], 0.0, balance
        return amt["val"], 0.0, balance  # default debit; balance delta corrects later

    amt = amounts[0]
    if amt["cr"]:
        return 0.0, amt["val"], 0.0
    return amt["val"], 0.0, 0.0


def normalise_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Rename CSV header variants to canonical column names."""
    col_map = {}
    aliases = {
        "Date": ("txndate", "transactiondate", "date", "valuedate"),
        "Description": ("description", "narration", "particulars", "remarks", "desc"),
        "Debit": ("debit", "withdrawal", "withdrawals", "debitamount", "dr", "withdrawal(dr.)"),
        "Credit": ("credit", "deposit", "deposits", "creditamount", "cr", "deposit(cr.)"),
        "Balance": ("balance", "closingbalance", "runningbalance"),
        "PaymentType": ("paymenttype", "type", "mode", "channel", "txntype"),
        "Amount": ("amount",),
        "Category": ("category",),
    }
    for col in df.columns:
        key = str(col).strip().lower().replace(" ", "")
        for canonical, variants in aliases.items():
            if key in variants:
                col_map[col] = canonical
                break
    df = df.rename(columns=col_map)

    # Split a single signed Amount column into Debit / Credit
    if "Amount" in df.columns and "Debit" not in df.columns:
        df["Debit"] = df["Amount"].apply(lambda v: abs(clean_amount(v)) if clean_amount(v) < 0 else 0.0)
        df["Credit"] = df["Amount"].apply(lambda v: clean_amount(v) if clean_amount(v) > 0 else 0.0)

    return df
