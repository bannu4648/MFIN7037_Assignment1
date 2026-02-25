# BHATI, Abhimanyu, 3036393745
# KABANI, Sameer, 3036384012
# VOBBILISETTY, Sai Navyanth, 3036384139

"""
Q1.7 (Extra credit): ETF vs MPF funds — low-cost global ETF (VT) vs HK equities and vs MPF global equity.

- Fetches VT (Vanguard Total World Stock ETF) actual annual returns from Yahoo Finance (yfinance).
- Compares: (1) VT vs HK/Greater China equities; (2) VT vs MPF global equity category (hk_GlobalEquityLargeCap);
  (3) how much better is the ETF than MPF funds. Includes a brief note on taxes.

Data: mpf_category_annual_returns.csv. We use hk_ columns only (Hong Kong scheme returns);
cal_ columns are the same categories under an alternative scheme — for HK investors we use hk_.
VT from Yahoo Finance (yfinance).
Output: ../results/q17_etf_vs_mpf.csv
"""

import pandas as pd
import numpy as np
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
RESULTS_DIR = ROOT / "results"
# MPF file may be in Question 1/data/ or project root
DATA_PATH = DATA_DIR / "mpf_category_annual_returns.csv"
if not DATA_PATH.exists():
    DATA_PATH = ROOT.parent / "mpf_category_annual_returns.csv"

# VT (Vanguard Total World Stock ETF) — TER 0.07%, replicates global benchmark
VT_TER = 0.0007
START_YEAR = 2010
END_YEAR = 2024


def fetch_vt_annual_returns():
    """Fetch VT price history and compute annual (calendar-year) returns."""
    try:
        import yfinance as yf
    except ImportError:
        raise ImportError("Install yfinance: pip install yfinance")

    vt = yf.Ticker("VT")
    hist = vt.history(start=f"{START_YEAR}-01-01", end=f"{END_YEAR + 1}-01-01", auto_adjust=True)
    if hist.empty or len(hist) < 2:
        raise RuntimeError("VT history from yfinance is empty or too short. Check dates and connection.")

    hist = hist.reset_index()
    if "Datetime" in hist.columns:
        hist = hist.rename(columns={"Datetime": "Date"})
    hist["Year"] = pd.to_datetime(hist["Date"]).dt.year
    close_col = "Adj Close" if "Adj Close" in hist.columns else "Close"
    last_per_year = hist.sort_values("Date").groupby("Year").last().reset_index()
    last_per_year = last_per_year[last_per_year["Year"].between(START_YEAR, END_YEAR)][["Year", close_col]].sort_values("Year")

    p = last_per_year[close_col].values
    if len(p) < 2:
        raise RuntimeError("Not enough VT year-end prices to compute returns.")
    rets = (p[1:] / p[:-1]) - 1
    years = last_per_year["Year"].values[1:].astype(int).tolist()
    n = len(rets)
    terminal = (1 + rets).prod()
    ann_return = terminal ** (1 / n) - 1
    return {
        "annual_returns": rets,
        "years": years,
        "n_years": n,
        "terminal_per_dollar": terminal,
        "annualised_return": ann_return,
    }


def load_mpf_hk(data_path):
    """Load MPF category returns — HK scheme only (hk_ columns)."""
    df = pd.read_csv(data_path)
    df = df[df["hk_year"] >= START_YEAR].copy()
    df = df[df["hk_year"] <= END_YEAR].copy()
    return df


def main():
    if not DATA_PATH.exists():
        raise FileNotFoundError(f"MPF data not found: {DATA_PATH}")

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    # 1) VT actual returns from online (yfinance)
    vt_data = fetch_vt_annual_returns()
    vt_ann = vt_data["annualised_return"]
    vt_terminal = vt_data["terminal_per_dollar"]
    vt_years = vt_data["years"]
    vt_n = vt_data["n_years"]

    # 2) MPF data (hk_ only — Hong Kong scheme, relevant for HK investors)
    df = load_mpf_hk(DATA_PATH)
    years_mpf = df["hk_year"].astype(int).tolist()
    r_global_mpf = df["hk_GlobalEquityLargeCap"].values
    r_hk_equity = df["hk_GreaterChinaEquity"].values

    cum_global_mpf = (1 + r_global_mpf).cumprod()
    cum_hk = (1 + r_hk_equity).cumprod()
    n_mpf = len(years_mpf)
    terminal_mpf_global = cum_global_mpf[-1]
    terminal_hk = cum_hk[-1]
    ann_mpf_global = (terminal_mpf_global ** (1 / n_mpf)) - 1
    ann_hk = (terminal_hk ** (1 / n_mpf)) - 1

    # Align years: use MPF years as reference (2010–2024)
    diff_etf_mpf_pct = (vt_ann - ann_mpf_global) * 100
    diff_etf_hk_pct = (vt_ann - ann_hk) * 100

    # Build comparison table and save
    comparison = pd.DataFrame({
        "Metric": [
            "Annualised return (2010–2024)",
            "Terminal wealth ($1 invested)",
            "Source",
        ],
        "VT (Vanguard Total World ETF)": [
            f"{vt_ann:.2%}",
            f"${vt_terminal:.4f}",
            "Yahoo Finance (yfinance)",
        ],
        "MPF global equity (hk_GlobalEquityLargeCap)": [
            f"{ann_mpf_global:.2%}",
            f"${terminal_mpf_global:.4f}",
            "mpf_category_annual_returns.csv (HK scheme)",
        ],
        "MPF HK/Greater China equity": [
            f"{ann_hk:.2%}",
            f"${terminal_hk:.4f}",
            "mpf_category_annual_returns.csv (HK scheme)",
        ],
    })
    comparison.to_csv(RESULTS_DIR / "q17_etf_vs_mpf.csv", index=False)


if __name__ == "__main__":
    main()
