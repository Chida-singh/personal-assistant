"""Analytics — statistics and report generation from a transaction DataFrame."""

import pandas as pd


def summary_stats(df: pd.DataFrame) -> dict:
    """High-level numeric summary."""
    if df.empty:
        return {}
    return {
        "total_debit": round(df["Debit"].sum(), 2),
        "total_credit": round(df["Credit"].sum(), 2),
        "net_flow": round(df["Credit"].sum() - df["Debit"].sum(), 2),
        "txn_count": len(df),
        "date_range": f"{df['Date'].min():%d %b %Y} – {df['Date'].max():%d %b %Y}",
    }


def generate_report(df: pd.DataFrame) -> dict:
    """Full spending report: categories, merchants, weekday patterns."""
    if df.empty:
        return {}

    debits = df[df["Debit"] > 0].copy()
    credits = df[df["Credit"] > 0].copy()

    total_spent = debits["Debit"].sum()
    total_credited = credits["Credit"].sum()

    cat_group = (
        debits.groupby("Category")["Debit"]
        .agg(["sum", "count"])
        .reset_index()
        .rename(columns={"Category": "category", "sum": "amount", "count": "count"})
    )
    cat_group["percentage"] = (
        (cat_group["amount"] / total_spent * 100).round(1) if total_spent > 0 else 0
    )
    cat_group["amount"] = cat_group["amount"].round(2)
    cat_group = cat_group.sort_values("amount", ascending=False).to_dict(orient="records")

    debits["Payee"] = debits["Description"].apply(_extract_payee)

    top_by_spend = (
        debits.groupby("Payee")["Debit"].sum()
        .sort_values(ascending=False).head(10).reset_index()
        .rename(columns={"Payee": "payee", "Debit": "amount"})
    )
    top_by_spend["amount"] = top_by_spend["amount"].round(2)

    top_by_freq = (
        debits.groupby("Payee")["Debit"].count()
        .sort_values(ascending=False).head(10).reset_index()
        .rename(columns={"Payee": "payee", "Debit": "count"})
    )

    weekday_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    debits["Weekday"] = debits["Date"].dt.day_name()
    weekday = (
        debits.groupby("Weekday")["Debit"].sum()
        .reindex(weekday_order, fill_value=0).reset_index()
        .rename(columns={"Weekday": "day", "Debit": "amount"})
    )
    weekday["amount"] = weekday["amount"].round(2)

    last_txn = {}
    if not debits.empty:
        row = debits.sort_values("Date").iloc[-1]
        last_txn = {
            "date": str(row["Date"])[:10],
            "description": row["Description"],
            "amount": float(row["Debit"]),
            "category": row["Category"],
        }

    return {
        "total_spent": round(total_spent, 2),
        "total_credited": round(total_credited, 2),
        "net_flow": round(total_credited - total_spent, 2),
        "txn_count": len(df),
        "debit_count": len(debits),
        "credit_count": len(credits),
        "category_breakdown": cat_group,
        "top_merchants_by_spend": top_by_spend.to_dict(orient="records"),
        "top_merchants_by_frequency": top_by_freq.to_dict(orient="records"),
        "weekday_spending": weekday.to_dict(orient="records"),
        "last_transaction": last_txn,
    }


def group_by_period(df: pd.DataFrame, period: str = "month") -> pd.DataFrame:
    """Aggregate debits and credits by month / week / quarter."""
    if df.empty:
        return df
    freq = {"week": "W", "quarter": "Q"}.get(period, "M")
    df = df.copy()
    df["Period"] = df["Date"].dt.to_period(freq).apply(lambda p: p.start_time)
    grouped = df.groupby("Period", as_index=False).agg(
        Debit=("Debit", "sum"),
        Credit=("Credit", "sum"),
        Txns=("Date", "count"),
    )
    grouped["Net"] = grouped["Credit"] - grouped["Debit"]
    return grouped.sort_values("Period")


def category_breakdown(df: pd.DataFrame) -> pd.DataFrame:
    """Spending totals per category (debits only)."""
    if df.empty:
        return df
    result = (
        df[df["Debit"] > 0]
        .groupby("Category", as_index=False)["Debit"]
        .sum()
        .rename(columns={"Debit": "Amount"})
        .sort_values("Amount", ascending=False)
    )
    return result


def payment_type_breakdown(df: pd.DataFrame) -> pd.DataFrame:
    """Transaction count and volume by payment type."""
    if df.empty:
        return pd.DataFrame()
    exp = df[df["Debit"] > 0].copy()
    if "PaymentType" not in exp.columns or exp["PaymentType"].str.strip().eq("").all():
        return pd.DataFrame()
    exp["PaymentType"] = exp["PaymentType"].replace("", "Unknown")
    return (
        exp.groupby("PaymentType", as_index=False)
        .agg(Count=("Debit", "count"), Volume=("Debit", "sum"))
        .sort_values("Volume", ascending=False)
    )


def weekday_avg_spending(df: pd.DataFrame) -> pd.DataFrame:
    """Average daily spend per weekday."""
    if df.empty:
        return df
    df = df.copy()
    df["Weekday"] = df["Date"].dt.day_name()
    day_totals = df.groupby([df["Date"].dt.date, "Weekday"])["Debit"].sum().reset_index()
    day_totals.columns = ["DateVal", "Weekday", "Debit"]
    avg = day_totals.groupby("Weekday", as_index=False)["Debit"].mean().rename(
        columns={"Debit": "AvgSpend"}
    )
    order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    avg["Weekday"] = pd.Categorical(avg["Weekday"], categories=order, ordered=True)
    return avg.sort_values("Weekday")


def top_merchants(df: pd.DataFrame, limit: int = 5) -> pd.DataFrame:
    """Top merchants by total spend."""
    if df.empty:
        return pd.DataFrame()
    debits = df[df["Debit"] > 0].copy()
    if debits.empty:
        return pd.DataFrame()
    debits["Payee"] = debits["Description"].apply(_extract_payee)
    result = (
        debits.groupby("Payee")["Debit"].sum()
        .sort_values(ascending=False).head(limit).reset_index()
    )
    result.columns = ["Payee", "Amount"]
    return result


def _extract_payee(desc: str) -> str:
    """Return the human-readable payee name from a description."""
    if str(desc).upper().startswith("UPI/"):
        parts = desc.split("/")
        return parts[1].strip().title() if len(parts) > 1 else desc
    return str(desc)[:40]
