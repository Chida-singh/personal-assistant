"""Finance utilities for summarizing bank statement CSV files."""

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


def _infer_category(description: str) -> str:
	# Infer a spending category from description text when labels are missing.
	text = str(description).lower()
	if any(keyword in text for keyword in ["food", "restaurant", "swiggy", "zomato"]):
		return "Food"
	if any(keyword in text for keyword in ["uber", "ola", "fuel"]):
		return "Transport"
	if any(keyword in text for keyword in ["amazon", "flipkart", "shop"]):
		return "Shopping"
	return "Other"


def analyze(file_path: str) -> str:
	# Load CSV input and report a clear message when the file cannot be opened.
	try:
		df = pd.read_csv(file_path)
	except FileNotFoundError:
		return f"Could not open file: {file_path}"
	except OSError:
		return f"Could not open file: {file_path}"

	# Validate required columns; Category is optional and can be inferred.
	required_columns = {"Date", "Description", "Amount"}
	if not required_columns.issubset(df.columns):
		return "CSV format not recognized. Expected: Date, Description, Amount"

	# Normalize Amount values and fail fast if they cannot be treated as numbers.
	amount_series = pd.to_numeric(df["Amount"], errors="coerce")
	if amount_series.isna().all():
		return "CSV format not recognized. Expected: Date, Description, Amount"
	df["Amount"] = amount_series.fillna(0)

	# Use existing Category labels when provided; otherwise infer from Description.
	inferred_categories = False
	if "Category" not in df.columns:
		inferred_categories = True
		df["Category"] = df["Description"].apply(_infer_category)
	else:
		df["Category"] = df["Category"].fillna("").astype(str).str.strip()
		missing_mask = df["Category"] == ""
		if missing_mask.any():
			inferred_categories = True
			df.loc[missing_mask, "Category"] = df.loc[missing_mask, "Description"].apply(_infer_category)

	# Group spending totals by category and sort from highest to lowest spend.
	grouped = df.groupby("Category", dropna=False)["Amount"].sum().sort_values(ascending=False)

	# Save a simple category bar chart in the assistant project root.
	chart_path = Path(__file__).resolve().parent.parent / "chart.png"
	plt.figure(figsize=(8, 4.5))
	grouped.plot(kind="bar")
	plt.title("Spending by Category")
	plt.xlabel("Category")
	plt.ylabel("Amount")
	plt.tight_layout()
	plt.savefig(chart_path)
	plt.close()

	# Build a readable summary string with totals and optional inference note.
	lines = ["Spending summary by category:"]
	lines.extend(f"- {category}: {total:.2f}" for category, total in grouped.items())

	if inferred_categories:
		lines.append("Some categories were inferred from descriptions. Add labels in the CSV for more accurate grouping.")

	lines.append("Chart saved as chart.png")
	return "\n".join(lines)
