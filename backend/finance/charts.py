"""Charts — all matplotlib chart generation for finance data."""

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd

_DATA_DIR = Path(__file__).resolve().parent / "data"
_COLORS = [
    "#f87171", "#60a5fa", "#34d399", "#fbbf24", "#c084fc",
    "#f472b6", "#9ca3af", "#fb923c", "#22d3ee", "#a3e635",
]


def _dark_fig(figsize: tuple) -> tuple:
    """Return a (fig, ax) pair styled for dark background."""
    plt.style.use("dark_background")
    fig, ax = plt.subplots(figsize=figsize)
    fig.patch.set_facecolor("#111111")
    return fig, ax


def chart_period(grouped: pd.DataFrame, period_label: str) -> str:
    """Grouped bar chart — debit vs credit per period."""
    out = _DATA_DIR / f"chart_period_{period_label}.png"
    fig, ax = _dark_fig((10, 4))

    x = range(len(grouped))
    w = 0.35
    labels = [
        f"{pd.Timestamp(p):%b %y}" if period_label == "month"
        else f"{pd.Timestamp(p):%d %b}" if period_label == "week"
        else f"Q{pd.Timestamp(p).quarter} {pd.Timestamp(p):%y}"
        for p in grouped["Period"]
    ]
    ax.bar([i - w / 2 for i in x], grouped["Debit"], w, label="Debit", color="#f87171")
    ax.bar([i + w / 2 for i in x], grouped["Credit"], w, label="Credit", color="#34d399")
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
    """Horizontal bar chart of spending by category."""
    out = _DATA_DIR / "chart_category.png"
    n = len(cat_df)
    fig, ax = _dark_fig((9, max(4, n * 0.55)))

    colors = [_COLORS[i % len(_COLORS)] for i in range(n)]
    bars = ax.barh(cat_df["Category"], cat_df["Amount"], color=colors)
    ax.invert_yaxis()
    ax.set_xlabel("Amount (₹)", color="#aaa", fontsize=10)
    ax.tick_params(colors="#aaa")
    ax.set_title("Spending by Category", color="#eee", pad=12)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    for bar, val in zip(bars, cat_df["Amount"]):
        ax.text(
            bar.get_width() + 10, bar.get_y() + bar.get_height() / 2,
            f"₹{val:,.0f}", va="center", ha="left", color="#ddd", fontsize=9,
        )
    plt.tight_layout()
    plt.savefig(str(out), facecolor=fig.get_facecolor(), dpi=130, bbox_inches="tight")
    plt.close()
    return str(out)


# Alias for backward compatibility
chart_category_pie = chart_category_bar


def chart_weekday(wd_df: pd.DataFrame) -> str:
    """Bar chart of average daily spend per weekday."""
    out = _DATA_DIR / "chart_weekday.png"
    fig, ax = _dark_fig((7, 4))
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
    """Side-by-side bars for payment type count and volume."""
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
    """Area line chart of balance over time."""
    if df.empty or "Balance" not in df.columns:
        return ""
    bal = df[df["Balance"] > 0].sort_values("Date")
    if bal.empty:
        return ""
    out = _DATA_DIR / "chart_balance.png"
    fig, ax = _dark_fig((10, 3.5))
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
