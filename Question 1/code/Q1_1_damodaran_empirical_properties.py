# BHATI, Abhimanyu, 3036393745
# KABANI, Sameer, 3036384012
# VOBBILISETTY, Sai Navyanth, 3036384139

"""
Q1.1 & Q1.2: Empirical properties of asset classes from Damodaran's historical returns.
Computes annualized return, volatility, Sharpe ratio (T-Bill as Rf), and correlation
for full sample, last 30 years, and prior period.

Data: histretSP.xls in ../data/
Output: ../results/ (damodaran_stats_*.csv, damodaran_corr_*.csv)
"""

import pandas as pd
import numpy as np
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
RESULTS_DIR = ROOT / "results"
XLS_PATH = DATA_DIR / "histretSP.xls"
if not XLS_PATH.exists():
    XLS_PATH = ROOT.parent / "histretSP.xls"


def load_damodaran():
    """Load Damodaran historical returns from histretSP.xls."""
    if not XLS_PATH.exists():
        raise FileNotFoundError(
            "histretSP.xls not found. Place it in data/ or project root. "
            "Download: https://www.stern.nyu.edu/~adamodar/pc/datasets/histretSP.xls"
        )
    df = pd.read_excel(XLS_PATH, sheet_name="Returns by year", engine="xlrd", header=19)
    df = df.iloc[:, :8].copy()
    df.columns = ["Year", "SP500", "SmallCap", "TBill", "TBond10Y", "Baa", "RealEstate", "Gold"]
    df["Year"] = pd.to_numeric(df["Year"], errors="coerce")
    df = df.dropna(subset=["Year"])
    df = df[df["Year"] >= 1928].copy()
    for c in ["SP500", "SmallCap", "TBill", "TBond10Y", "Baa", "RealEstate", "Gold"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    df = df.dropna(how="all", subset=["SP500"])
    return df


def stats_table(df, rf_col="TBill"):
    """Compute annualized return, vol, Sharpe for each asset."""
    cols = [c for c in ["SP500", "SmallCap", "TBill", "TBond10Y", "Baa", "RealEstate", "Gold"] if c in df.columns]
    df_ = df[cols].dropna()
    n = len(df_)
    geo_ret = df_[cols].apply(lambda s: (1 + s).prod() ** (1 / n) - 1)
    vol = df_[cols].std()
    excess = geo_ret - df_[rf_col].mean()
    sharpe = excess / vol.replace(0, np.nan)
    return pd.DataFrame({
        "Annualized_Return": geo_ret,
        "Volatility": vol,
        "Sharpe_Ratio": sharpe,
    }).round(4)


def main():
    df = load_damodaran()
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    df.to_csv(RESULTS_DIR / "damodaran_histret_loaded.csv", index=False)

    full = df.dropna(subset=["SP500"], how="all")
    last_year = int(full["Year"].max())
    first_year = int(full["Year"].min())
    df_30 = df[df["Year"] >= last_year - 30].copy()
    df_prior = df[(df["Year"] >= first_year) & (df["Year"] < last_year - 30)].copy()
    if len(df_prior) < 5:
        mid = first_year + (last_year - first_year) // 2
        df_30 = df[df["Year"] >= mid].copy()
        df_prior = df[df["Year"] < mid].copy()

    cols = [c for c in ["SP500", "SmallCap", "TBill", "TBond10Y", "Baa", "RealEstate", "Gold"] if c in df.columns]
    s_full = stats_table(full)
    s_30 = stats_table(df_30)
    s_prior = stats_table(df_prior)
    corr_full = full[cols].corr().round(3)
    corr_30 = df_30[cols].corr().round(3)

    s_full.to_csv(RESULTS_DIR / "damodaran_stats_full.csv")
    s_30.to_csv(RESULTS_DIR / "damodaran_stats_last30.csv")
    s_prior.to_csv(RESULTS_DIR / "damodaran_stats_prior.csv")
    corr_full.to_csv(RESULTS_DIR / "damodaran_corr_full.csv")
    corr_30.to_csv(RESULTS_DIR / "damodaran_corr_last30.csv")


if __name__ == "__main__":
    main()
