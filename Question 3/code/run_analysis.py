"""Global macro factor attribution analysis.

Runs the full pipeline:
  1. Load fund returns and FF5 factors.
  2. Regress on FF5 as a diagnostic benchmark.
  3. Fetch external factors (FRED macro + AQR multi-asset), with local
     cache fallback when the network is unavailable.
  4. Build two proposed macro models:
       a) Economist's model — hand-picked factors reflecting macro logic.
       b) Greedy best-fit — forward stepwise adj-R² maximisation.
  5. Compare all models on the same date window.
  6. (Extra credit) Backtest vs live HFGM ETF.
  7. Write all outputs to ``data/output_data/``.

Usage (from the Question 3 folder):
    python code/run_analysis.py
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from data_prep import (
    fetch_all_external_factors,
    fetch_hfgm_monthly_returns,
    load_ff5_monthly,
    load_fund_monthly_returns,
)
from model_utils import (
    build_report,
    coef_table,
    fit_ols,
    regression_diagnostics,
)

CODE_DIR = Path(__file__).resolve().parent
PROJECT_DIR = CODE_DIR.parent
DATA_DIR = PROJECT_DIR / "data"
OUTPUT_DIR = DATA_DIR / "output_data"
OUTPUT_MD = OUTPUT_DIR / "analysis_global_macro.md"

ALL_CANDIDATES = [
    "mkt_rf", "usd_ret", "dgs10_chg", "hy_oas_chg", "cmdty_ret",
    "tsmom", "val_everywhere", "mom_everywhere",
    "tsmom_eq", "tsmom_fi", "tsmom_fx", "tsmom_cm",
    "qmj_global", "bab_global",
]

ECON_PRIORITY = [
    "mkt_rf", "tsmom", "val_everywhere", "hy_oas_chg", "usd_ret",
    "dgs10_chg", "mom_everywhere", "cmdty_ret",
]


def _resolve_input_file(filename: str) -> Path:
    data_path = DATA_DIR / filename
    return data_path if data_path.exists() else CODE_DIR / filename


def _pick_best_model(fund_excess: pd.Series, candidate_df: pd.DataFrame,
                     all_candidates: list[str], min_obs: int = 60,
                     min_factors: int = 3, max_factors: int = 5) -> list[str]:
    """Greedy forward selection maximising adj-R²."""
    available = [c for c in all_candidates if c in candidate_df.columns
                 and candidate_df[c].notna().sum() > min_obs]
    chosen: list[str] = []
    for _ in range(max_factors):
        best_r2, best_col = -np.inf, None
        for c in available:
            if c in chosen:
                continue
            trial = chosen + [c]
            tmp = candidate_df[["fund_excess"] + trial].dropna()
            if len(tmp) < min_obs:
                continue
            ar2 = float(fit_ols(tmp["fund_excess"], tmp[trial]).rsquared_adj)
            if ar2 > best_r2:
                best_r2, best_col = ar2, c
        if best_col is None:
            break
        chosen.append(best_col)
    if len(chosen) < min_factors:
        chosen = available[:min_factors] if len(available) >= min_factors else available
    return chosen


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    fund_xlsx = _resolve_input_file(
        "CS Global Macro Index at 2x Vol Net of 95bps 2025.09.xlsx"
    )
    ff5_parquet = _resolve_input_file("ff.five_factor.parquet")

    # ── 1) Load local data ──────────────────────────────────────────────
    fund = load_fund_monthly_returns(fund_xlsx)
    ff5 = load_ff5_monthly(ff5_parquet)
    core = fund.merge(ff5, on="date", how="inner").sort_values("date").reset_index(drop=True)
    core["fund_excess"] = core["fund_ret"] - core["rf"]

    # ── 2) FF5 regression ───────────────────────────────────────────────
    ff5_factors = ["mkt_rf", "smb", "hml", "rmw", "cma"]
    ff5_model = fit_ols(core["fund_excess"], core[ff5_factors])
    ff5_diag = regression_diagnostics(ff5_model, core["fund_excess"], core[ff5_factors])
    ff5_coef = coef_table(ff5_model).reset_index().rename(columns={"index": "factor"})

    # ── 3) Fetch external factors (FRED + AQR, cached fallback) ─────────
    ext = fetch_all_external_factors(
        start=str(core["date"].min().date()),
        cache_dir=OUTPUT_DIR,
        data_dir=DATA_DIR,
    )
    ext.to_csv(OUTPUT_DIR / "external_factors_monthly.csv", index=False)
    print(f"External factors: {len(ext)} rows, {len(ext.columns)} columns.")

    # ── 4) Merge into analysis frame ────────────────────────────────────
    macro = core.merge(ext, on="date", how="left")
    macro["fund_excess"] = macro["fund_ret"] - macro["rf"]

    # ── 5a) Economist's model (hand-picked, ≤ 5) ───────────────────────
    econ_avail = [c for c in ECON_PRIORITY
                  if c in macro.columns and macro[c].notna().sum() > 60]
    econ_factors = econ_avail[:5] if len(econ_avail) >= 5 else econ_avail[:max(3, len(econ_avail))]

    econ_df = macro[["date", "fund_excess"] + econ_factors].dropna().reset_index(drop=True)
    econ_model = fit_ols(econ_df["fund_excess"], econ_df[econ_factors])
    econ_diag = regression_diagnostics(econ_model, econ_df["fund_excess"], econ_df[econ_factors])
    econ_coef = coef_table(econ_model).reset_index().rename(columns={"index": "factor"})

    # ── 5b) Greedy best-fit model ───────────────────────────────────────
    greedy_factors = _pick_best_model(
        macro["fund_excess"], macro, ALL_CANDIDATES, min_factors=3, max_factors=5,
    )
    greedy_df = macro[["date", "fund_excess"] + greedy_factors].dropna().reset_index(drop=True)
    greedy_model = fit_ols(greedy_df["fund_excess"], greedy_df[greedy_factors])
    greedy_diag = regression_diagnostics(greedy_model, greedy_df["fund_excess"], greedy_df[greedy_factors])
    greedy_coef = coef_table(greedy_model).reset_index().rename(columns={"index": "factor"})

    # ── 6) Fair-window FF5 comparison ───────────────────────────────────
    all_dates = set(econ_df["date"]) | set(greedy_df["date"])
    ff5_same = core[core["date"].isin(all_dates)].dropna(subset=["fund_excess"] + ff5_factors)
    ff5_same_model = fit_ols(ff5_same["fund_excess"], ff5_same[ff5_factors])
    ff5_same_diag = regression_diagnostics(ff5_same_model, ff5_same["fund_excess"], ff5_same[ff5_factors])

    diag_keys = ["n_obs", "adj_r2", "alpha_monthly", "alpha_annualized",
                 "resid_vol_annualized", "corr_fitted_actual"]
    compare_tbl = pd.DataFrame([
        {"model": "FF5 (same window)", **{k: ff5_same_diag[k] for k in diag_keys}},
        {"model": "Economist's Macro", **{k: econ_diag[k] for k in diag_keys}},
        {"model": "Greedy Best-Fit", **{k: greedy_diag[k] for k in diag_keys}},
    ])

    # ── 7) Extra credit: backtest vs live HFGM ─────────────────────────
    live_note = ""
    live_stats = pd.DataFrame()
    live_overlap = pd.DataFrame()
    try:
        hfgm = fetch_hfgm_monthly_returns(start="2022-01-01")
        hfgm.to_csv(OUTPUT_DIR / "hfgm_monthly_returns.csv", index=False)
        live = core[["date", "fund_ret"]].merge(hfgm, on="date", how="inner").dropna()
        if len(live) >= 4:
            corr = float(live["fund_ret"].corr(live["hfgm_ret"]))
            beta = float(
                np.cov(live["hfgm_ret"], live["fund_ret"], ddof=1)[0, 1]
                / np.var(live["fund_ret"], ddof=1)
            )
            spread = live["hfgm_ret"] - live["fund_ret"]
            live_stats = pd.DataFrame([{
                "overlap_months": len(live),
                "corr_hfgm_vs_backtest": corr,
                "beta_hfgm_on_backtest": beta,
                "tracking_error_ann": float(spread.std(ddof=1) * np.sqrt(12.0)),
                "avg_return_diff_ann": float(((1.0 + spread.mean()) ** 12) - 1.0),
            }])
            live_overlap = live.copy()
            live_overlap["spread"] = spread.values
            live_overlap["date"] = live_overlap["date"].dt.strftime("%Y-%m")
        else:
            live_note = "Not enough overlap between HFGM and backtest for robust metrics."
    except Exception as e:
        live_note = f"Could not fetch HFGM data ({type(e).__name__}: {e})."

    # ── 8) Save CSVs ────────────────────────────────────────────────────
    ff5_coef.to_csv(OUTPUT_DIR / "ff5_coefficients.csv", index=False)
    econ_coef.to_csv(OUTPUT_DIR / "econ_model_coefficients.csv", index=False)
    greedy_coef.to_csv(OUTPUT_DIR / "greedy_model_coefficients.csv", index=False)
    compare_tbl.to_csv(OUTPUT_DIR / "model_comparison.csv", index=False)
    if not live_stats.empty:
        live_stats.to_csv(OUTPUT_DIR / "live_vs_backtest_stats.csv", index=False)

    # ── 9) Markdown report ──────────────────────────────────────────────
    report = build_report(
        date_min=str(core["date"].min().date()),
        date_max=str(core["date"].max().date()),
        n_months=len(core),
        n_ext_factors=len(ext.columns) - 1,
        ff5_diag=ff5_diag,
        ff5_coef=ff5_coef,
        ff5_alpha_p=float(ff5_model.pvalues.get("const", np.nan)),
        econ_factors=econ_factors,
        econ_coef=econ_coef,
        econ_diag=econ_diag,
        greedy_factors=greedy_factors,
        greedy_coef=greedy_coef,
        greedy_diag=greedy_diag,
        ff5_same_diag=ff5_same_diag,
        compare_tbl=compare_tbl,
        n_candidates=len(ALL_CANDIDATES),
        live_stats=live_stats,
        live_overlap=live_overlap,
        live_note=live_note,
    )
    OUTPUT_MD.write_text(report, encoding="utf-8")
    print(f"Analysis complete. Report → {OUTPUT_MD}")


if __name__ == "__main__":
    main()
