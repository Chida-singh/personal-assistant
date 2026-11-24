from pathlib import Path
from typing import Optional

import pandas as pd
from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel

from ..finance import core

router = APIRouter(prefix="/api/finance", tags=["finance"])

UPLOAD_DIR = Path(__file__).resolve().parent.parent / "data" / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


class ManualTransaction(BaseModel):
    date: str
    description: str
    debit: float = 0.0
    credit: float = 0.0
    category: str = ""
    account: str = "Main"


class CategoryUpdate(BaseModel):
    category: str = ""
    note: Optional[str] = None


class ConfirmUpdate(BaseModel):
    category: str
    note: str = ""


@router.post("/upload")
async def finance_upload(file: UploadFile = File(...), account: str = Form("Main")):
    dest = UPLOAD_DIR / file.filename
    with open(dest, "wb") as f:
        content = await file.read()
        f.write(content)
    count, err = core.ingest_file(str(dest), account)
    if err:
        raise HTTPException(status_code=400, detail=err)
    return {"count": count, "message": f"{count} transactions imported", "filename": file.filename}


@router.get("/accounts")
def finance_accounts():
    return {"accounts": core.get_accounts()}


@router.get("/dashboard")
def finance_dashboard(period: str = "month", account: str = "All"):
    df = core.get_ledger_df()
    if account != "All" and not df.empty:
        df = df[df["Account"] == account]
    if df.empty:
        return {"empty": True, "stats": {}, "chart_data": {}}

    stats = core.summary_stats(df)
    chart_data = {}

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


@router.get("/report")
def finance_report(account: str = "All"):
    df = core.get_ledger_df()
    if account != "All" and not df.empty:
        df = df[df["Account"] == account]
    if df.empty:
        return {"empty": True}
    report = core.generate_report(df)
    return {"empty": False, **report}


@router.get("/transactions")
def finance_transactions(
    category: str = "",
    search: str = "",
    sort_by: str = "date_desc",
    page: int = 1,
    limit: int = 50,
    account: str = "All"
):
    return core.get_transactions(category, search, sort_by, page, limit, account)


@router.post("/transactions/manual")
def finance_add_manual(txn: ManualTransaction):
    row = core.add_manual_transaction(
        txn.date, txn.description, txn.debit, txn.credit, txn.category, txn.account
    )
    return {"message": "Transaction added", "transaction": row}


@router.patch("/transactions/{txn_id}")
def finance_update_category(txn_id: str, body: CategoryUpdate):
    ok = core.update_transaction_category(txn_id, body.category, body.note)
    if not ok:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return {"message": "Transaction updated"}


@router.get("/ambiguous")
def finance_ambiguous():
    return {"transactions": core.get_ambiguous_transactions()}


@router.post("/transactions/{txn_id}/confirm")
def finance_confirm_txn(txn_id: str, body: ConfirmUpdate):
    ok = core.confirm_transaction(txn_id, body.category, body.note)
    if not ok:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return {"message": "Transaction confirmed"}


@router.get("/insights")
def finance_insights():
    return core.generate_ai_insights()


@router.get("/charts/{name}")
def finance_chart(name: str, period: str = "month"):
    data_dir = Path(__file__).resolve().parent.parent / "data"
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


@router.delete("/clear")
def finance_clear():
    core._save_ledger([])
    return {"message": "All finance data cleared"}
