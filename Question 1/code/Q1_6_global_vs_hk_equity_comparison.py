"""
Q1.6: Global vs HK/Greater China equity — cumulative growth of $1 and annualised return
(2010–2024). How much better would HK investors have done in global equity?

Data: mpf_category_annual_returns.csv in ../data/ or project root
Output: ../results/q16_cumulative_global_vs_hk.csv
"""

import pandas as pd
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
RESULTS_DIR = ROOT / "results"
DATA_PATH = DATA_DIR / "mpf_category_annual_returns.csv"
if not DATA_PATH.exists():
    DATA_PATH = ROOT.parent / "mpf_category_annual_returns.csv"


def main():
    if not DATA_PATH.exists():
        raise FileNotFoundError(f"MPF data not found: {DATA_PATH}")
    df = pd.read_csv(DATA_PATH)
    df = df[df["hk_year"] >= 2010].copy()
    years = df["hk_year"].astype(int).tolist()

    r_global = df["hk_GlobalEquityLargeCap"].values
    r_hk = df["hk_GreaterChinaEquity"].values
    cum_global = (1 + r_global).cumprod()
    cum_hk = (1 + r_hk).cumprod()
    terminal_global = cum_global[-1]
    terminal_hk = cum_hk[-1]
    n = len(years)
    ann_global = (terminal_global ** (1 / n)) - 1
    ann_hk = (terminal_hk ** (1 / n)) - 1

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    out = pd.DataFrame({
        "year": years,
        "cum_global": cum_global,
        "cum_hk_greater_china": cum_hk,
    })
    out.to_csv(RESULTS_DIR / "q16_cumulative_global_vs_hk.csv", index=False)


if __name__ == "__main__":
    main()
