from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional
from pathlib import Path
from contextlib import asynccontextmanager

from database import create_db_and_tables
import core

@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    # Auto-fix miscategorized rows on startup
    try:
        changed = core.recategorize_ledger()
        print(f"[Finance] Auto-recategorized {changed} transactions.")
    except Exception as e:
        print(f"[Finance] Recategorization error: {e}")
    yield

app = FastAPI(title="Finance Service", lifespan=lifespan)

UPLOAD_DIR = Path(__file__).parent / "data" / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# --- Pydantic Models ---

class ManualTransaction(BaseModel):
    date: str
    description: str
    debit: float = 0.0
    credit: float = 0.0
    category: str = ""
    account: str = "Main"

class CategoryUpdate(BaseModel):
    category: str = ""
    note: str = None

class ConfirmUpdate(BaseModel):
    category: str
    note: str = ""

# --- Routes ---

@app.post("/api/finance/upload")
async def finance_upload(file: UploadFile = File(...), account: str = Form("Main")):
    dest = UPLOAD_DIR / file.filename
    with open(dest, "wb") as f:
        content = await file.read()
        f.write(content)
    count, err = core.ingest_file(str(dest), account)
    if err:
        raise HTTPException(status_code=400, detail=err)
    return {"count": count, "message": f"{count} transactions imported", "filename": file.filename}

@app.get("/api/finance/accounts")
def finance_accounts():
    return {"accounts": core.get_accounts()}

@app.get("/api/finance/dashboard")
def finance_dashboard(period: str = "month", account: str = "All"):
    df = core.get_ledger_df()
    if account != "All" and not df.empty:
        df = df[df["Account"] == account]
    if df.empty:
        return {"empty": True, "stats": {}, "chart_data": {}}

    stats = core.summary_stats(df)
    chart_data = {}

    import pandas as pd
    gp = core.group_by_period(df, period)
    if not gp.empty:
        chart_data["period"] = [
            {
                "label": (
                    f"{pd.Timestamp(row.Period):%b %y}" if period == "month"
                    else f"{pd.Timestamp(row.Period):%d %b}" if period == "week"
                    else f"Q{pd.Timestamp(row.Period).quarter} {pd.Timestamp(row.Period):%y}"
                ),
                "debit": round(float(row.Debit), 2),
                "credit": round(float(row.Credit), 2),
                "net": round(float(row.Net), 2),
            }
            for row in gp.itertuples()
        ]

    cat = core.category_breakdown(df)
    if not cat.empty:
        chart_data["category"] = [
            {"category": row.Category, "amount": round(float(row.Amount), 2)}
            for row in cat.itertuples()
        ]

    wd = core.weekday_avg_spending(df)
    if not wd.empty:
        chart_data["weekday"] = [
            {"day": row.Weekday[:3], "avg": round(float(row.AvgSpend), 2)}
            for row in wd.itertuples()
        ]

    bal_df = df[df["Balance"] > 0].sort_values("Date")
    if not bal_df.empty:
        sample = bal_df.tail(60)
        chart_data["balance"] = [
            {"date": str(row.Date)[:10], "balance": round(float(row.Balance), 2)}
            for row in sample.itertuples()
        ]

    return {"empty": False, "stats": stats, "chart_data": chart_data}

@app.get("/api/finance/report")
def finance_report(account: str = "All"):
    df = core.get_ledger_df()
    if account != "All" and not df.empty:
        df = df[df["Account"] == account]
    if df.empty:
        return {"empty": True}
    report = core.generate_report(df)
    return {"empty": False, **report}

@app.get("/api/finance/transactions")
def finance_transactions(
    category: str = "",
    search: str = "",
    sort_by: str = "date_desc",
    page: int = 1,
    limit: int = 50,
    account: str = "All"
):
    return core.get_transactions(category, search, sort_by, page, limit, account)

@app.post("/api/finance/transactions/manual")
def finance_add_manual(txn: ManualTransaction):
    row = core.add_manual_transaction(
        txn.date, txn.description, txn.debit, txn.credit, txn.category, txn.account
    )
    return {"message": "Transaction added", "transaction": row}

@app.patch("/api/finance/transactions/{txn_id}")
def finance_update_category(txn_id: str, body: CategoryUpdate):
    ok = core.update_transaction_category(txn_id, body.category, body.note)
    if not ok:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return {"message": "Transaction updated"}

@app.get("/api/finance/ambiguous")
def finance_ambiguous():
    return {"transactions": core.get_ambiguous_transactions()}

@app.post("/api/finance/transactions/{txn_id}/confirm")
def finance_confirm_txn(txn_id: str, body: ConfirmUpdate):
    ok = core.confirm_transaction(txn_id, body.category, body.note)
    if not ok:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return {"message": "Transaction confirmed"}

@app.get("/api/finance/insights")
def finance_insights():
    return core.generate_ai_insights()

@app.get("/api/finance/charts/{name}")
def finance_chart(name: str, period: str = "month"):
    data_dir = Path(__file__).parent / "data"
    if name == "period":
        fp = data_dir / f"chart_period_{period}.png"
    else:
        chart_map = {
            "category": "chart_category.png",
            "weekday": "chart_weekday.png",
            "paytype": "chart_paytype.png",
            "balance": "chart_balance.png",
        }
        filename = chart_map.get(name)
        if not filename:
            raise HTTPException(status_code=404, detail="Chart not found")
        fp = data_dir / filename
    if not fp.exists():
        raise HTTPException(status_code=404, detail="Chart not generated yet")
    return FileResponse(str(fp), media_type="image/png", headers={"Cache-Control": "no-cache"})

@app.delete("/api/finance/clear")
def finance_clear():
    # We use a naive delete by just saving an empty array using the new DB wrapper
    core._save_ledger([])
    return {"message": "All finance data cleared"}

@app.get("/health")
def health_check():
    return {"status": "ok", "service": "finance-service"}
