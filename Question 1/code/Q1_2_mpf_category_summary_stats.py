"""
Q1.2 (supplementary): MPF category summary statistics — mean return, volatility, Sharpe ratio.
Uses MPF category returns (HK scheme) for full sample and allocation funds.

Data: mpf_category_annual_returns.csv in ../data/ or project root
Output: ../results/ (summary_stats_*.csv, correlation_allocation_funds.csv)
"""

import pandas as pd
import numpy as np
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
RESULTS_DIR = ROOT / "results"
DATA_PATH = DATA_DIR / "mpf_category_annual_returns.csv"
if not DATA_PATH.exists():
    DATA_PATH = ROOT.parent / "mpf_category_annual_returns.csv"


def load_mpf_returns():
    """Load MPF category returns. Use HK (hk_) columns for Hong Kong scheme."""
    df = pd.read_csv(DATA_PATH)
    hk_cols = [c for c in df.columns if c.startswith("hk_") and c != "hk_year"]
    df = df[["hk_year"] + hk_cols].copy()
    df = df.rename(columns={"hk_year": "year"})
    df = df.set_index("year")
    df.columns = [c.replace("hk_", "") for c in df.columns]
    return df


def summary_stats(df, risk_free_rate_annual=0.02):
    """Compute mean return, volatility, excess return, Sharpe ratio."""
    mean_ret = df.mean()
    vol = df.std()
    excess = mean_ret - risk_free_rate_annual
    sharpe = excess / vol.replace(0, np.nan)
    return pd.DataFrame({
        "Mean_Return": mean_ret,
        "Volatility": vol,
        "Excess_Return": excess,
        "Sharpe_Ratio": sharpe,
    }).round(4)


def main():
    if not DATA_PATH.exists():
        raise FileNotFoundError(f"MPF data not found: {DATA_PATH}")
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    df = load_mpf_returns()

    df_full = df
    df_recent = df.loc[2010:].copy() if 2010 in df.index else df
    Rf = 0.02

    stats_full = summary_stats(df_full, Rf)
    stats_recent = summary_stats(df_recent, Rf)
    stats_full.to_csv(RESULTS_DIR / "summary_stats_full_sample.csv")
    stats_recent.to_csv(RESULTS_DIR / "summary_stats_2010_2024.csv")

    allocation = [c for c in df.columns if "Allocation" in c]
    alloc_full = df[allocation]
    alloc_recent = df_recent[allocation]
    stats_alloc_full = summary_stats(alloc_full, Rf)
    stats_alloc_recent = summary_stats(alloc_recent, Rf)
    stats_alloc_full.to_csv(RESULTS_DIR / "summary_stats_allocation_funds_full.csv")
    stats_alloc_recent.to_csv(RESULTS_DIR / "summary_stats_allocation_funds_2010_2024.csv")

    corr_alloc = alloc_recent.corr().round(3)
    corr_alloc.to_csv(RESULTS_DIR / "correlation_allocation_funds.csv")


if __name__ == "__main__":
    main()
