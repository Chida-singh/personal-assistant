"""Categorization — keyword rules and LLM fallback."""

import json
import os
import re

import requests

_OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/api/chat")

# ── category keywords ──
CATEGORIES: dict[str, list[str]] = {
    "Food & Dining": [
        "food", "restaurant", "swiggy", "zomato", "cafe", "coffee",
        "mcdonalds", "mcdonald", "mcdelivery", "kfc", "domino", "pizza",
        "biryani", "eat", "kitchen", "bakery", "chai", "juice",
        "coconut water", "tender coconut", "coke", "burger", "burrito",
        "hotel", "dhaba", "canteen", "idly", "dosa", "mess", "fruits",
        "vegeta", "subzi", "sweet", "mithai", "lassi", "snack", "brownie",
        "ice cream", "icecream", "momos", "noodle", "chaat", "pani puri",
        "lunch", "dinner", "breakfast",
    ],
    "Transportation": [
        "uber", "ola", "fuel", "petrol", "transit", "lyft", "rapido",
        "ticket", "flight", "metro", "cab", "auto", "travel",
        "train", "taxi", "toll", "parking", "driver", "bike", "yulu", "bounce",
    ],
    "Shopping": [
        "amazon", "flipkart", "shop", "mart", "store", "supermarket",
        "grocery", "myntra", "ajio", "meesho", "shampoo", "dunzo",
        "zepto", "blinkit", "bigbasket", "dmart", "lifestyle", "reliance",
        "nykaa", "beauty", "cosmetics", "croma", "vijay sales",
    ],
    "Entertainment": [
        "netflix", "spotify", "prime video", "movie", "cinema", "hotstar",
        "gaming", "youtube", "apple music", "stream", "disney",
        "bookmyshow", "pvr", "inox", "playstation", "badminton", "cricket",
        "sports", "swim", "aquat", "bowling", "arcade", "club",
    ],
    "Bills & Utilities": [
        "electric", "water bill", "recharge", "broadband", "mobile",
        "jio", "airtel", "wifi", "bsnl", "bescom", "bbmp", "gas cylinder",
        "lpg", "insurance", "policy", "premium", "annual fee", "debit card",
    ],
    "Personal Care": [
        "haircut", "salon", "barber", "spa", "parlour", "trim", "grooming",
        "lifecare", "pharmacy", "chemist", "medical", "medicine", "health",
        "hospital", "clinic", "doctor", "dental", "apollo", "netmeds",
    ],
    "Education & Work": [
        "print", "printout", "stationery", "book", "course", "udemy",
        "coursera", "colour", "banner", "poster", "design", "copies",
        "xerox", "ai tokens", "openai", "chatgpt", "google asia", "api",
        "subscription", "cloud", "hosting",
    ],
    "Transfer": ["neft", "imps", "rtgs", "kotak", "monthly spend", "thank", "transfer"],
    "Income": ["salary", "refund", "deposit", "interest", "cashback", "reward", "dividend"],
    "Cash": ["cash", "atm", "withdrawal"],
}

GENERIC_MEMOS = {
    "upi", "upiintent", "pay", "payment", "transfer", "", "you are paying",
    "pay to", "nan", "imps", "neft", "rtgs", "n/a", "na", "none",
}

# Pre-compile patterns; use word-boundary matching for short/single-word keywords
_PATTERNS: dict[str, list[re.Pattern]] = {}
for _cat, _kws in CATEGORIES.items():
    _PATTERNS[_cat] = []
    for _kw in _kws:
        if len(_kw) <= 4 and ' ' not in _kw:
            _PATTERNS[_cat].append(re.compile(r'\b' + re.escape(_kw) + r'\b', re.IGNORECASE))
        else:
            _PATTERNS[_cat].append(re.compile(re.escape(_kw), re.IGNORECASE))


def parse_upi_parts(desc: str) -> tuple[str, str]:
    """Split a UPI description into (payee, memo), both lowercased."""
    if not desc.upper().startswith("UPI/"):
        return "", desc.lower()
    parts = desc.split("/")
    payee = parts[1].strip() if len(parts) > 1 else ""
    memo = parts[3].strip() if len(parts) > 3 else ""
    return payee.lower(), memo.lower()


def infer_category(desc: str, debit: float = 0, credit: float = 0) -> str:
    """Return the best matching category for a transaction."""
    raw = str(desc).lower()
    search_text = "{} {}".format(*parse_upi_parts(desc)) if raw.startswith("upi/") else raw

    # Credits default to Transfer/Income unless a keyword proves otherwise
    if credit > 0 and debit == 0:
        for pat in _PATTERNS.get("Income", []):
            if pat.search(search_text):
                return "Income"
        return "Transfer"

    for cat, patterns in _PATTERNS.items():
        for pat in patterns:
            if pat.search(search_text):
                return cat

    if raw.startswith("upi/"):
        _, memo = parse_upi_parts(desc)
        if memo.strip().lower() in GENERIC_MEMOS:
            return "Transfer"

    return "Other"


def is_ambiguous(row: dict) -> bool:
    """Return True if a transaction still needs user clarification."""
    if row.get("user_confirmed"):
        return False
    cat = row.get("Category", "Other")
    if cat not in ("Transfer", "Other"):
        return False
    desc = row.get("Description", "")
    if not str(desc).upper().startswith("UPI/"):
        return False
    _, memo = parse_upi_parts(desc)
    return memo.strip().lower() in GENERIC_MEMOS


def llm_categorize_batch(txns: list[dict]) -> dict:
    """Send uncategorized transactions to Ollama for classification.

    Args:
        txns: list of dicts with keys id, desc, amt.
    Returns:
        dict mapping id → category string.
    """
    if not txns:
        return {}

    category_list = ", ".join(list(CATEGORIES.keys()) + ["Other"])
    lines = "\n".join(f"ID: {t['id']} | Desc: {t['desc']} | Amt: {t['amt']}" for t in txns)
    prompt = (
        f"Categorize the following transactions into one of: {category_list}.\n"
        "Return ONLY a JSON object mapping the transaction ID to the category string.\n\n"
        + lines
    )

    try:
        resp = requests.post(
            _OLLAMA_URL,
            json={
                "model": os.getenv("LLM_MODEL", "gemma4"),
                "messages": [{"role": "user", "content": prompt}],
                "stream": False,
                "format": "json",
            },
            timeout=120,
        )
        resp.raise_for_status()
        content = resp.json().get("message", {}).get("content", "{}")
        content = re.sub(r"```(json)?\n?", "", content).replace("```", "").strip()
        return json.loads(content)
    except Exception:
        return {}
