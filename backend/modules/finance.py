"""Finance module — parses bank statements, stores txns, generates period analytics."""

import io
import json
import re
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pandas as pd
import requests

try:
	import fitz  # PyMuPDF
except ImportError:
	fitz = None

# ── paths ──
_DATA_DIR = Path(__file__).resolve().parent.parent / "data"
_LEDGER = _DATA_DIR / "finance_ledger.json"

# ── category keywords — checked against UPI payee + memo ──
_CAT_MAP = {
	"Food & Dining": [
		"food", "restaurant", "swiggy", "zomato", "cafe", "coffee",
		"mcdonalds", "mcdonald", "mcdelivery", "kfc", "domino", "pizza",
		"biryani", "eat", "kitchen", "bakery", "chai", "juice", "coconut", "coconut water", "tender coconut",
		"coke", "burger", "burrito", "hotel", "dhaba", "canteen", "idc", "idly", "dosa", "mess",
		"fruits", "vegeta", "subzi", "sweet", "mithai", "lassi",
		"snack", "brownie", "ice cream", "icecream", "tea", "momos",
		"noodle", "chaat", "pani puri", "lunch", "dinner", "breakfast",
	],
	"Transportation": [
		"uber", "ola", "fuel", "petrol", "transit", "lyft", "rapido",
		"ticket", "flight", "metro", "cab", "auto", "travel", "bus",
		"train", "taxi", "toll", "parking", "driver", "bike", "yulu", "bounce",
	],
	"Shopping": [
		"amazon", "flipkart", "shop", "mart", "store", "supermarket",
		"grocery", "myntra", "ajio", "meesho", "shampoo", "dunzo",
		"zepto", "blinkit", "bigbasket", "dmart", "lifestyle", "reliance",
		"nykaa", "beauty", "cosmetics", "croma", "vijay sales",
	],
	"Entertainment": [
		"netflix", "spotify", "prime", "movie", "cinema", "hotstar",
		"game", "gaming", "play", "youtube", "apple music", "stream", "disney",
		"bookmyshow", "pvr", "inox", "ps4", "ps5", "xbox", "playstation",
		"badminton", "cricket", "sports", "swim", "aquat", "pool",
		"bowling", "arcade", "club",
	],
	"Bills & Utilities": [
		"electric", "water", "bill", "recharge", "broadband", "mobile",
		"jio", "airtel", "vi ", "wifi", "bsnl", "act ", "bescom",
		"bbmp", "gas", "cylinder", "lpg", "insurance", "policy",
		"premium", "annual fee", "debit card",
	],
	"Personal Care": [
		"haircut", "salon", "barber", "spa", "parlour",
		"trim", "grooming", "lifecare", "pharmacy", "chemist",
		"medical", "medicine", "mask", "health", "hospital", "clinic",
		"doctor", "dental", "eye", "apollo", "netmeds",
	],
	"Education & Work": [
		"print", "printout", "stationery", "book", "course", "udemy",
		"coursera", "colour", "banner",
		"poster", "design", "copies", "xerox",
		"ai tokens", "openai", "chatgpt", "google asia", "api",
		"subscription", "cloud", "hosting",
	],
	"Transfer": [
		"neft", "imps", "rtgs",
		"kotak", "monthly spend", "thank", "transfer"
	],
	"Income": [
		"salary", "refund", "deposit", "interest", "cashback", "reward", "dividend",
	],
	"Cash": ["cash", "atm", "withdrawal"],
}


def _parse_upi_parts(desc: str):
    """
    UPI descriptions follow: UPI/PAYEE_NAME/TXN_ID/MEMO
    Returns (payee, memo) both lowercased for matching.
    """
    if not desc.upper().startswith("UPI/"):
        return "", desc.lower()
    parts = desc.split("/")
    payee = parts[1].strip() if len(parts) > 1 else ""
    memo = parts[3].strip() if len(parts) > 3 else ""
    return payee.lower(), memo.lower()


def _infer_category(desc: str, debit: float = 0, credit: float = 0) -> str:
	"""Categorize a transaction description, UPI-aware and Income-aware."""
	raw = str(desc).lower()

	if raw.startswith("upi/"):
		payee, memo = _parse_upi_parts(desc)
		search_text = f"{payee} {memo}"
	else:
		search_text = raw

	# If it's incoming money, it should only match Income or Transfer
	if credit > 0 and debit == 0:
		for kw in _CAT_MAP["Income"]:
			if kw in search_text:
				return "Income"
		for kw in _CAT_MAP["Transfer"]:
			if kw in search_text:
				return "Transfer"
		return "Transfer"  # Default incoming to Transfer (e.g., friend sending money)

	# Check multi-word keywords first (longer matches take priority)
	for cat, kws in _CAT_MAP.items():
		for kw in kws:
			if len(kw) > 3 and kw in search_text:
				return cat

	# Then check single/short keywords
	for cat, kws in _CAT_MAP.items():
		for kw in kws:
			if len(kw) <= 3 and kw in search_text:
				return cat

	# For UPI with generic memos (just "UPI", "pay", etc.), 
	# these are person-to-person transfers
	if raw.startswith("upi/"):
		_, memo = _parse_upi_parts(desc)
		if memo.strip().lower() in _GENERIC_MEMOS:
			return "Transfer"

	return "Other"


# Memos that are too generic to infer a category from
_GENERIC_MEMOS = {
	"upi", "upiintent", "pay", "payment", "transfer", "", "you are paying",
	"pay to", "nan", "imps", "neft", "rtgs", "n/a", "na", "none",
}


def _is_ambiguous(row: dict) -> bool:
	"""Return True if this transaction needs user input to be properly categorized."""
	if row.get("user_confirmed"):
		return False
	desc = row.get("Description", "")
	cat = row.get("Category", "Other")
	if cat not in ("Transfer", "Other"):
		return False  # already categorized clearly
	if not str(desc).upper().startswith("UPI/"):
		return False  # non-UPI transfer rows are usually legit
	payee, memo = _parse_upi_parts(desc)
	return memo.strip().lower() in _GENERIC_MEMOS


def get_ambiguous_transactions(limit: int = 30) -> list[dict]:
	"""Return transactions that couldn't be auto-categorized and need user input. Groups duplicates."""
	rows = _load_ledger()
	ambiguous = []
	seen_payees = set()
	for r in rows:
		if _is_ambiguous(r):
			payee, memo = _parse_upi_parts(r.get("Description", ""))
			# Group by payee if available, else by exact description
			group_key = payee if payee else r.get("Description", "")
			if group_key in seen_payees:
				continue
			seen_payees.add(group_key)
			
			ambiguous.append({
				"id": r.get("id", ""),
				"Date": str(r.get("Date", ""))[:10],
				"Description": r.get("Description", ""),
				"payee_display": payee.title() if payee else "Unknown Transfer",
				"Debit": r.get("Debit", 0),
				"Credit": r.get("Credit", 0),
				"Category": r.get("Category", "Other"),
			})
		if len(ambiguous) >= limit:
			break
	return ambiguous


def confirm_transaction(txn_id: str, category: str, note: str = "") -> bool:
	"""Mark a transaction as user-confirmed and apply to all identical ambiguous transactions."""
	rows = _load_ledger()
	
	target_desc = ""
	for r in rows:
		if r.get("id") == txn_id:
			target_desc = r.get("Description", "")
			break
			
	if not target_desc:
		return False
		
	target_payee, _ = _parse_upi_parts(target_desc)
	target_key = target_payee if target_payee else target_desc
	
	changed = False
	for r in rows:
		if r.get("id") == txn_id:
			r["Category"] = category
			r["user_confirmed"] = True
			if note: r["note"] = note
			changed = True
		elif _is_ambiguous(r):
			p, _ = _parse_upi_parts(r.get("Description", ""))
			k = p if p else r.get("Description", "")
			if k == target_key:
				r["Category"] = category
				r["user_confirmed"] = True
				if note: r["note"] = note
				changed = True
				
	if changed:
		_save_ledger(rows)
		return True
	return False


def generate_ai_insights() -> dict:
	"""Call Gemma 4 to produce personalized spending insights."""
	rows = _load_ledger()
	if not rows:
		return {"insights": [], "tip": "", "error": "No data yet"}

	df = _df_from_ledger()
	report = generate_report(df)

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
		for d in report.get("weekday_spending", [])
		if d['amount'] > 0
	)

	prompt = (
		"You are a smart personal finance advisor. Analyze the spending data below and give "
		"3-4 SHORT, SPECIFIC, personalized insights. Use ₹ signs. Reference real numbers. "
		"Be conversational, not robotic. Then give one actionable tip.\n\n"
		f"Total spent: ₹{report['total_spent']:.0f}\n"
		f"Total received: ₹{report['total_credited']:.0f}\n"
		f"Net flow: ₹{report['net_flow']:.0f}\n"
		f"Transactions: {report['txn_count']}\n\n"
		f"Spending by category:\n{cat_lines}\n\n"
		f"Top merchants:\n{merchant_lines}\n\n"
		f"Spending by day:\n{weekday_lines}\n\n"
		"Return ONLY valid JSON with keys: insights (array of strings), tip (string), "
		"alert (string, empty if no anomaly)."
	)

	try:
		resp = requests.post(
			"http://localhost:11434/api/chat",
			json={
				"model": os.getenv("LLM_MODEL", "gemma4"),
				"messages": [{"role": "user", "content": prompt}],
				"stream": False,
				"format": "json",
			},
			timeout=90,
		)
		resp.raise_for_status()
		content = resp.json().get("message", {}).get("content", "{}")
		# strip markdown fences if present
		content = re.sub(r"```(json)?\n?", "", content).replace("```", "").strip()
		result = json.loads(content)
		return {
			"insights": result.get("insights", []),
			"tip": result.get("tip", ""),
			"alert": result.get("alert", ""),
		}
	except json.JSONDecodeError:
		# Fallback: return raw content as a single insight
		return {"insights": [content[:500]], "tip": "", "alert": ""}
	except Exception as e:
		return {"insights": [], "tip": "", "alert": "", "error": f"Gemma unavailable: {e}"}


def _clean_amount(val) -> float:
	"""Parse amount string like '4,000.00' or '' into float."""
	if pd.isna(val) or str(val).strip() in ("", " "):
		return 0.0
	s = re.sub(r"[^\d.\-]", "", str(val))
	try:
		return float(s)
	except ValueError:
		return 0.0


# ── PDF extraction ──

def extract_pdf_text(fp: str) -> str:
	if not fitz:
		raise ImportError("PyMuPDF required. pip install pymupdf")
	txt = ""
	with fitz.open(fp) as doc:
		for pg in doc:
			txt += pg.get_text() + "\n"
	return txt


def _llm_csv(raw: str) -> str:
	"""Ask local Ollama to convert raw text → CSV."""
	llm_model = os.getenv("LLM_MODEL", "gemma4")
	prompt = (
		"Extract all financial transactions from the text below into CSV.\n"
		"Columns: Date,Description,Debit,Credit,Balance\n"
		"Rules:\n"
		"- Date = YYYY-MM-DD\n"
		"- Amounts = plain numbers, no commas, no currency symbols\n"
		"- Leave empty if not applicable\n"
		"- Output ONLY the CSV rows including header, no markdown, no explanation\n\n"
		f"TEXT:\n{raw}"
	)
	try:
		resp = requests.post("http://localhost:11434/api/chat", json={
			"model": llm_model,
			"messages": [{"role": "user", "content": prompt}],
			"stream": False
		}, timeout=300)
		resp.raise_for_status()
		csv = resp.json().get("message", {}).get("content", "")
		csv = re.sub(r"```(csv)?\n?", "", csv).replace("```", "").strip()
		return csv
	except Exception as e:
		raise RuntimeError(f"LLM CSV conversion failed: {e}. Make sure Ollama is running.")


# ── ledger persistence ──

def _load_ledger() -> list[dict]:
	if _LEDGER.exists():
		return json.loads(_LEDGER.read_text(encoding="utf-8"))
	return []


def _save_ledger(rows: list[dict]):
	_DATA_DIR.mkdir(parents=True, exist_ok=True)
	_LEDGER.write_text(json.dumps(rows, indent=2, default=str), encoding="utf-8")


def _df_from_ledger() -> pd.DataFrame:
	rows = _load_ledger()
	if not rows:
		return pd.DataFrame(columns=["id", "Date", "Description", "Debit", "Credit",
									  "Balance", "Category", "PaymentType", "Account"])
	df = pd.DataFrame(rows)
	df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
	for c in ("Debit", "Credit", "Balance"):
		if c in df.columns:
			df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0)
	if "id" not in df.columns:
		df["id"] = [str(uuid.uuid4())[:8] for _ in range(len(df))]
	if "Account" not in df.columns:
		df["Account"] = "Main"
	df["Account"] = df["Account"].fillna("Main")
	return df


# ── Auto-recategorize existing "Transfer" rows that are actually UPI ──

def recategorize_ledger():
	"""Re-run categorization on the whole ledger. Fixes old miscategorized rows."""
	rows = _load_ledger()
	changed = 0
	for r in rows:
		desc = r.get("Description", "")
		old_cat = r.get("Category", "")
		
		# Fix rows that have both Debit and Credit > 0 (parse error)
		debit = r.get("Debit", 0)
		credit = r.get("Credit", 0)
		if isinstance(debit, (int, float)) and isinstance(credit, (int, float)):
			if debit > 0 and credit > 0:
				# Keep whichever is actually the transaction, zero the other
				# If balance went up, it's a credit; otherwise debit
				r["Credit"] = 0
				changed += 1
		
		# Re-categorize non-user-confirmed rows
		if not r.get("user_confirmed"):
			new_cat = _infer_category(desc, debit=r.get("Debit", 0), credit=r.get("Credit", 0))
			if new_cat != old_cat:
				r["Category"] = new_cat
				changed += 1
		
		# Ensure all rows have an id
		if "id" not in r or not r["id"]:
			r["id"] = str(uuid.uuid4())[:8]
		# Ensure Account field
		if "Account" not in r:
			r["Account"] = "Main"
	if changed > 0 or any("id" not in r for r in rows):
		_save_ledger(rows)
	return changed


# ── CSV / file ingestion ──

def _normalise_columns(df: pd.DataFrame) -> pd.DataFrame:
	"""Map common header variations to our canonical names."""
	col_map = {}
	for c in df.columns:
		cl = str(c).strip().lower().replace(" ", "")
		if cl in ("txndate", "transactiondate", "date", "valuedate"):
			col_map[c] = "Date"
		elif cl in ("description", "narration", "particulars", "remarks", "desc"):
			col_map[c] = "Description"
		elif cl in ("debit", "withdrawal", "withdrawals", "debitamount", "dr", "withdrawal(dr.)"):
			col_map[c] = "Debit"
		elif cl in ("credit", "deposit", "deposits", "creditamount", "cr", "deposit(cr.)"):
			col_map[c] = "Credit"
		elif cl in ("balance", "closingbalance", "runningbalance"):
			col_map[c] = "Balance"
		elif cl in ("paymenttype", "type", "mode", "channel", "txntype"):
			col_map[c] = "PaymentType"
		elif cl in ("amount",):
			col_map[c] = "Amount"
		elif cl in ("category",):
			col_map[c] = "Category"
	df = df.rename(columns=col_map)

	# If only a single "Amount" col exists, split into Debit/Credit
	if "Amount" in df.columns and "Debit" not in df.columns:
		df["Debit"] = df["Amount"].apply(lambda v: abs(v) if v < 0 else 0)
		df["Credit"] = df["Amount"].apply(lambda v: v if v > 0 else 0)
	return df


def ingest_file(path: str, account: str = "Main") -> tuple[int, str]:
	"""Parse file → append to ledger. Returns (count_added, error_or_empty)."""
	p = Path(path)
	ext = p.suffix.lower()

	try:
		if ext == ".csv":
			df = pd.read_csv(path, on_bad_lines='skip', engine='python')
		elif ext == ".pdf":
			raw = extract_pdf_text(path)
			csv_str = _llm_csv(raw)
			df = pd.read_csv(io.StringIO(csv_str), on_bad_lines='skip', engine='python')
		else:
			with open(path, "r", encoding="utf-8", errors="ignore") as f:
				csv_str = _llm_csv(f.read())
			df = pd.read_csv(io.StringIO(csv_str), on_bad_lines='skip', engine='python')
	except Exception as e:
		return 0, str(e)

	df = _normalise_columns(df)

	# ensure Date exists
	if "Date" not in df.columns:
		return 0, f"No Date column found. Got: {list(df.columns)}"

	# clean amounts
	for c in ("Debit", "Credit", "Balance"):
		if c not in df.columns:
			df[c] = 0
		df[c] = df[c].apply(_clean_amount)

	# --- Fix LLM Extraction using Balance Delta ---
	# The LLM often extracts deposits into the Debit column. We can use the 
	# mathematical change in the Balance column to definitively prove if a 
	# transaction was incoming (Credit) or outgoing (Debit).
	if "Balance" in df.columns and len(df) > 1:
		diffs = df["Balance"].diff()
		for i, idx in enumerate(df.index):
			if i == 0:
				continue  # Cannot calculate delta for the first row
			delta = diffs[idx]
			if pd.notna(delta) and delta != 0:
				if delta > 0:
					df.at[idx, "Credit"] = round(delta, 2)
					df.at[idx, "Debit"] = 0
				else:
					df.at[idx, "Credit"] = 0
					df.at[idx, "Debit"] = round(abs(delta), 2)

	if "Description" not in df.columns:
		df["Description"] = ""
	if "PaymentType" not in df.columns:
		df["PaymentType"] = ""

	# Always re-infer category using new smart logic (with amounts)
	df["Category"] = df.apply(lambda r: _infer_category(r["Description"], r.get("Debit", 0), r.get("Credit", 0)), axis=1)

	# parse dates
	df["Date"] = pd.to_datetime(df["Date"], dayfirst=True, errors="coerce")
	df = df.dropna(subset=["Date"])

	if df.empty:
		return 0, "No valid transactions found after parsing."

	# append to ledger with deduplication
	ledger = _load_ledger()

	existing_sigs = set()
	for r in ledger:
		sig = f"{r.get('Date')}_{r.get('Description')}_{r.get('Debit')}_{r.get('Credit')}"
		existing_sigs.add(sig)

	new_rows = df[["Date", "Description", "Debit", "Credit", "Balance",
				   "Category", "PaymentType"]].to_dict(orient="records")

	added_rows = []
	for r in new_rows:
		r_date = r["Date"].isoformat() if hasattr(r["Date"], "isoformat") else str(r["Date"])
		r["Date"] = r_date
		r["id"] = str(uuid.uuid4())[:8]
		r["Account"] = account
		sig = f"{r_date}_{r.get('Description')}_{r.get('Debit')}_{r.get('Credit')}"
		if sig not in existing_sigs:
			added_rows.append(r)
			existing_sigs.add(sig)

	ledger.extend(added_rows)
	_save_ledger(ledger)
	return len(added_rows), ""


def add_manual_transaction(date: str, description: str, debit: float, credit: float, category: str = "", account: str = "Main") -> dict:
	"""Add a manual transaction to the ledger."""
	ledger = _load_ledger()
	row = {
		"id": str(uuid.uuid4())[:8],
		"Date": date,
		"Description": description,
		"Debit": debit,
		"Credit": credit,
		"Balance": 0.0,
		"Category": category if category else _infer_category(description),
		"PaymentType": "Manual",
		"Account": account,
	}
	ledger.append(row)
	_save_ledger(ledger)
	return row


def update_transaction_category(txn_id: str, new_category: str, note: str = None) -> bool:
	"""Update the category and/or note of a single transaction by id."""
	rows = _load_ledger()
	for r in rows:
		if r.get("id") == txn_id:
			if new_category:
				r["Category"] = new_category
				r["user_confirmed"] = True
			if note is not None:
				r["note"] = note
			_save_ledger(rows)
			return True
	return False


def get_accounts() -> list[str]:
	"""Return a list of unique account names."""
	rows = _load_ledger()
	accounts = set()
	for r in rows:
		accounts.add(r.get("Account", "Main"))
	if not accounts:
		return ["Main"]
	return sorted(list(accounts))


def get_transactions(
	category: str = "",
	search: str = "",
	sort_by: str = "date_desc",
	page: int = 1,
	limit: int = 50,
	account: str = "All",
) -> dict:
	"""Return paginated, filtered transaction list."""
	rows = _load_ledger()
	if not rows:
		return {"total": 0, "page": 1, "pages": 1, "transactions": []}

	# filter
	filtered = []
	for r in rows:
		if account != "All" and r.get("Account", "Main") != account:
			continue
		if category and r.get("Category", "") != category:
			continue
		if search:
			s = search.lower()
			if s not in r.get("Description", "").lower() and s not in r.get("Category", "").lower():
				continue
		filtered.append(r)

	# sort
	parts = sort_by.split("_")
	if len(parts) == 2:
		field, direction = parts
		key = field.capitalize()
		reverse = (direction == "desc")
		if key == "Amount":
			key = "Debit"
			
		def sort_val(x):
			v = x.get(key)
			if v is None:
				return 0 if key in ("Debit", "Credit", "Balance") else ""
			if isinstance(v, str):
				return v.lower()
			return v

		try:
			filtered.sort(key=sort_val, reverse=reverse)
		except Exception:
			pass

	total = len(filtered)
	pages = max(1, (total + limit - 1) // limit)
	page = max(1, min(page, pages))
	start = (page - 1) * limit
	end = start + limit

	return {
		"total": total,
		"page": page,
		"pages": pages,
		"transactions": filtered[start:end],
	}


def analyze(path: str) -> str:
	count, err = ingest_file(path)
	if err:
		return f"Failed to analyze statement: {err}"
	return f"Successfully analyzed statement. Added {count} new transactions."


def clear_ledger():
	if _LEDGER.exists():
		_LEDGER.unlink()


def get_ledger_df() -> pd.DataFrame:
	return _df_from_ledger()

def top_merchants(df: pd.DataFrame, limit: int = 5) -> pd.DataFrame:
	if df.empty:
		return pd.DataFrame()
	debits = df[df["Debit"] > 0].copy()
	if debits.empty:
		return pd.DataFrame()
	
	def extract_payee(desc):
		if str(desc).upper().startswith("UPI/"):
			parts = desc.split("/")
			return parts[1].strip().title() if len(parts) > 1 else desc
		return desc[:25]
	
	debits["Payee"] = debits["Description"].apply(extract_payee)
	top = debits.groupby("Payee")["Debit"].sum().sort_values(ascending=False).head(limit).reset_index()
	top.columns = ["Payee", "Amount"]
	return top


# ── analytics ──

def summary_stats(df: pd.DataFrame) -> dict:
	"""Return high-level stats dict."""
	if df.empty:
		return {}
	total_debit = df["Debit"].sum()
	total_credit = df["Credit"].sum()
	net = total_credit - total_debit
	txn_count = len(df)
	date_range = f"{df['Date'].min():%d %b %Y} – {df['Date'].max():%d %b %Y}"
	return {
		"total_debit": round(total_debit, 2),
		"total_credit": round(total_credit, 2),
		"net_flow": round(net, 2),
		"txn_count": txn_count,
		"date_range": date_range,
	}


def generate_report(df: pd.DataFrame) -> dict:
	"""Generate a full spending report."""
	if df.empty:
		return {}

	debits = df[df["Debit"] > 0].copy()
	credits = df[df["Credit"] > 0].copy()

	total_spent = debits["Debit"].sum()
	total_credited = credits["Credit"].sum()

	# Category breakdown
	cat_group = debits.groupby("Category")["Debit"].agg(["sum", "count"]).reset_index()
	cat_group.columns = ["category", "amount", "count"]
	cat_group["percentage"] = (cat_group["amount"] / total_spent * 100).round(1) if total_spent > 0 else 0
	cat_group["amount"] = cat_group["amount"].round(2)
	cat_group = cat_group.sort_values("amount", ascending=False).to_dict(orient="records")

	# Top merchants by spend (extract payee from UPI)
	def extract_payee(desc):
		if str(desc).upper().startswith("UPI/"):
			parts = desc.split("/")
			return parts[1].strip().title() if len(parts) > 1 else desc
		return desc[:40]

	debits = debits.copy()
	debits["Payee"] = debits["Description"].apply(extract_payee)
	top_merchants_spend = (
		debits.groupby("Payee")["Debit"]
		.sum()
		.sort_values(ascending=False)
		.head(10)
		.reset_index()
	)
	top_merchants_spend.columns = ["payee", "amount"]
	top_merchants_spend["amount"] = top_merchants_spend["amount"].round(2)

	# Top merchants by frequency
	top_merchants_freq = (
		debits.groupby("Payee")["Debit"]
		.count()
		.sort_values(ascending=False)
		.head(10)
		.reset_index()
	)
	top_merchants_freq.columns = ["payee", "count"]

	# Day of week pattern
	debits["Weekday"] = debits["Date"].dt.day_name()
	weekday_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
	wd = debits.groupby("Weekday")["Debit"].sum().reindex(weekday_order, fill_value=0).reset_index()
	wd.columns = ["day", "amount"]
	wd["amount"] = wd["amount"].round(2)

	# Most recent day spent
	if not debits.empty:
		latest = debits.sort_values("Date").iloc[-1]
		last_txn = {
			"date": str(latest["Date"])[:10],
			"description": latest["Description"],
			"amount": float(latest["Debit"]),
			"category": latest["Category"],
		}
	else:
		last_txn = {}

	return {
		"total_spent": round(total_spent, 2),
		"total_credited": round(total_credited, 2),
		"net_flow": round(total_credited - total_spent, 2),
		"txn_count": len(debits),
		"category_breakdown": cat_group,
		"top_merchants_by_spend": top_merchants_spend.to_dict(orient="records"),
		"top_merchants_by_frequency": top_merchants_freq.to_dict(orient="records"),
		"weekday_spending": wd.to_dict(orient="records"),
		"last_transaction": last_txn,
	}


def group_by_period(df: pd.DataFrame, period: str = "month") -> pd.DataFrame:
	"""Group txns by month / week / quarter."""
	if df.empty:
		return df
	df = df.copy()
	if period == "week":
		df["Period"] = df["Date"].dt.to_period("W").apply(lambda p: p.start_time)
	elif period == "quarter":
		df["Period"] = df["Date"].dt.to_period("Q").apply(lambda p: p.start_time)
	else:
		df["Period"] = df["Date"].dt.to_period("M").apply(lambda p: p.start_time)
	g = df.groupby("Period", as_index=False).agg(
		Debit=("Debit", "sum"),
		Credit=("Credit", "sum"),
		Txns=("Date", "count"),
	)
	g["Net"] = g["Credit"] - g["Debit"]
	return g.sort_values("Period")


def category_breakdown(df: pd.DataFrame) -> pd.DataFrame:
	"""Spending by category (debits only)."""
	if df.empty:
		return df
	exp = df[df["Debit"] > 0].copy()
	g = exp.groupby("Category", as_index=False)["Debit"].sum()
	g = g.rename(columns={"Debit": "Amount"}).sort_values("Amount", ascending=False)
	return g


def payment_type_breakdown(df: pd.DataFrame) -> pd.DataFrame:
	"""Txn count & volume by payment type."""
	if df.empty:
		return df
	exp = df[df["Debit"] > 0].copy()
	if "PaymentType" not in exp.columns or exp["PaymentType"].str.strip().eq("").all():
		return pd.DataFrame()
	exp["PaymentType"] = exp["PaymentType"].replace("", "Unknown")
	g = exp.groupby("PaymentType", as_index=False).agg(
		Count=("Debit", "count"), Volume=("Debit", "sum")
	).sort_values("Volume", ascending=False)
	return g


def weekday_avg_spending(df: pd.DataFrame) -> pd.DataFrame:
	"""Avg daily spending per weekday."""
	if df.empty:
		return df
	df = df.copy()
	df["Weekday"] = df["Date"].dt.day_name()
	day_totals = df.groupby([df["Date"].dt.date, "Weekday"])["Debit"].sum().reset_index()
	day_totals.columns = ["DateVal", "Weekday", "Debit"]
	avg = day_totals.groupby("Weekday", as_index=False)["Debit"].mean()
	avg = avg.rename(columns={"Debit": "AvgSpend"})
	order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
	avg["Weekday"] = pd.Categorical(avg["Weekday"], categories=order, ordered=True)
	return avg.sort_values("Weekday")


# ── charting — period-specific filenames to prevent cache collisions ──

_COLORS = ["#f87171", "#60a5fa", "#34d399", "#fbbf24", "#c084fc",
		   "#f472b6", "#9ca3af", "#fb923c", "#22d3ee", "#a3e635"]


def chart_period(grouped: pd.DataFrame, period_label: str) -> str:
	out = _DATA_DIR / f"chart_period_{period_label}.png"
	plt.style.use("dark_background")
	fig, ax = plt.subplots(figsize=(10, 4))
	fig.patch.set_facecolor("#111111")

	x = range(len(grouped))
	w = 0.35
	labels = [f"{pd.Timestamp(p):%b %y}" if period_label == "month"
			   else f"{pd.Timestamp(p):%d %b}" if period_label == "week"
			   else f"Q{pd.Timestamp(p).quarter} {pd.Timestamp(p):%y}"
			   for p in grouped["Period"]]

	ax.bar([i - w/2 for i in x], grouped["Debit"], w, label="Debit", color="#f87171")
	ax.bar([i + w/2 for i in x], grouped["Credit"], w, label="Credit", color="#34d399")
	ax.set_xticks(list(x))
	ax.set_xticklabels(labels, rotation=45, ha="right", fontsize=9, color="#aaa")
	ax.tick_params(axis="y", colors="#aaa")
	ax.set_title(f"Debit vs Credit ({period_label.title()})", color="#eee", pad=12)
	ax.legend(facecolor="#222", edgecolor="#333", fontsize=9)
	ax.spines["top"].set_visible(False)
	ax.spines["right"].set_visible(False)
	plt.tight_layout()
	plt.savefig(str(out), facecolor=fig.get_facecolor(), dpi=130)
	plt.close()
	return str(out)


def chart_category_bar(cat_df: pd.DataFrame) -> str:
	"""Horizontal bar chart — much more readable than pie for many categories."""
	out = _DATA_DIR / "chart_category.png"
	plt.style.use("dark_background")

	n = len(cat_df)
	fig_h = max(4, n * 0.55)
	fig, ax = plt.subplots(figsize=(9, fig_h))
	fig.patch.set_facecolor("#111111")

	colors = [_COLORS[i % len(_COLORS)] for i in range(n)]
	bars = ax.barh(cat_df["Category"], cat_df["Amount"], color=colors)
	ax.invert_yaxis()
	ax.set_xlabel("Amount (₹)", color="#aaa", fontsize=10)
	ax.tick_params(colors="#aaa")
	ax.set_title("Spending by Category", color="#eee", pad=12)
	ax.spines["top"].set_visible(False)
	ax.spines["right"].set_visible(False)

	for bar, val in zip(bars, cat_df["Amount"]):
		ax.text(bar.get_width() + 10, bar.get_y() + bar.get_height()/2,
				f"₹{val:,.0f}", va="center", ha="left", color="#ddd", fontsize=9)

	plt.tight_layout()
	plt.savefig(str(out), facecolor=fig.get_facecolor(), dpi=130, bbox_inches="tight")
	plt.close()
	return str(out)


# Keep old name as alias for backward compat
def chart_category_pie(cat_df: pd.DataFrame) -> str:
	return chart_category_bar(cat_df)


def chart_weekday(wd_df: pd.DataFrame) -> str:
	out = _DATA_DIR / "chart_weekday.png"
	plt.style.use("dark_background")
	fig, ax = plt.subplots(figsize=(7, 4))
	fig.patch.set_facecolor("#111111")

	ax.bar(wd_df["Weekday"].astype(str), wd_df["AvgSpend"], color="#fbbf24")
	ax.set_title("Average Daily Spending by Weekday", color="#eee", pad=12)
	ax.tick_params(axis="x", rotation=30, colors="#aaa")
	ax.tick_params(axis="y", colors="#aaa")
	ax.set_ylabel("Avg Spend (₹)", color="#aaa")
	ax.spines["top"].set_visible(False)
	ax.spines["right"].set_visible(False)
	plt.tight_layout()
	plt.savefig(str(out), facecolor=fig.get_facecolor(), dpi=130)
	plt.close()
	return str(out)


def chart_payment_type(pt_df: pd.DataFrame) -> str:
	if pt_df.empty:
		return ""
	out = _DATA_DIR / "chart_paytype.png"
	plt.style.use("dark_background")
	fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4))
	fig.patch.set_facecolor("#111111")

	ax1.barh(pt_df["PaymentType"], pt_df["Count"], color="#60a5fa")
	ax1.set_title("Txn Count by Payment Type", color="#eee", pad=10)
	ax1.tick_params(colors="#aaa")
	ax1.invert_yaxis()

	ax2.barh(pt_df["PaymentType"], pt_df["Volume"], color="#c084fc")
	ax2.set_title("Txn Volume by Payment Type", color="#eee", pad=10)
	ax2.tick_params(colors="#aaa")
	ax2.invert_yaxis()

	plt.tight_layout()
	plt.savefig(str(out), facecolor=fig.get_facecolor(), dpi=130)
	plt.close()
	return str(out)


def chart_balance_trend(df: pd.DataFrame) -> str:
	"""Line chart of balance over time."""
	if df.empty or "Balance" not in df.columns:
		return ""
	bal = df[df["Balance"] > 0].sort_values("Date")
	if bal.empty:
		return ""
	out = _DATA_DIR / "chart_balance.png"
	plt.style.use("dark_background")
	fig, ax = plt.subplots(figsize=(10, 3.5))
	fig.patch.set_facecolor("#111111")
	ax.fill_between(bal["Date"], bal["Balance"], alpha=0.25, color="#34d399")
	ax.plot(bal["Date"], bal["Balance"], color="#34d399", linewidth=1.5)
	ax.set_title("Balance Trend", color="#eee", pad=12)
	ax.tick_params(colors="#aaa")
	ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %y"))
	ax.xaxis.set_major_locator(mdates.MonthLocator(interval=1))
	plt.xticks(rotation=45, ha="right", fontsize=8)
	ax.spines["top"].set_visible(False)
	ax.spines["right"].set_visible(False)
	plt.tight_layout()
	plt.savefig(str(out), facecolor=fig.get_facecolor(), dpi=130)
	plt.close()
	return str(out)
