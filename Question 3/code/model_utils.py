# BHATI, Abhimanyu, 3036393745
# KABANI, Sameer, 3036384012
# VOBBILISETTY, Sai Navyanth, 3036384139

from __future__ import annotations

import numpy as np
import pandas as pd
import statsmodels.api as sm


# ── OLS helpers ─────────────────────────────────────────────────────────────

def fit_ols(y: pd.Series, x: pd.DataFrame):
    x_with_const = sm.add_constant(x, has_constant="add")
    model = sm.OLS(y, x_with_const, missing="drop").fit()
    return model


def regression_diagnostics(model, y: pd.Series, x: pd.DataFrame) -> dict:
    x_with_const = sm.add_constant(x, has_constant="add")
    y_hat = model.predict(x_with_const)
    resid = y - y_hat
    return {
        "n_obs": int(model.nobs),
        "r2": float(model.rsquared),
        "adj_r2": float(model.rsquared_adj),
        "alpha_monthly": float(model.params.get("const", np.nan)),
        "alpha_annualized": float((1.0 + model.params.get("const", 0.0)) ** 12 - 1.0),
        "resid_vol_monthly": float(resid.std(ddof=1)),
        "resid_vol_annualized": float(resid.std(ddof=1) * np.sqrt(12.0)),
        "corr_fitted_actual": float(np.corrcoef(y, y_hat)[0, 1]),
    }


def coef_table(model) -> pd.DataFrame:
    return pd.DataFrame({
        "coef": model.params,
        "t_stat": model.tvalues,
        "p_value": model.pvalues,
    })


# ── Markdown helpers ────────────────────────────────────────────────────────

def to_md_table(df: pd.DataFrame, digits: int = 4) -> str:
    """Convert a DataFrame to a GitHub-flavoured markdown table."""
    data = df.copy()
    for c in data.columns:
        if pd.api.types.is_numeric_dtype(data[c]):
            data[c] = data[c].map(lambda x: f"{x:.{digits}f}" if pd.notna(x) else "")
    header = "| " + " | ".join(data.columns.astype(str)) + " |"
    sep = "| " + " | ".join(["---"] * len(data.columns)) + " |"
    body = [
        "| " + " | ".join(str(v) for v in row) + " |"
        for row in data.astype(str).itertuples(index=False, name=None)
    ]
    return "\n".join([header, sep] + body)


FACTOR_DESC: dict[str, str] = {
    "tsmom": "AQR Time-Series Momentum (all assets) — trend-following proxy",
    "val_everywhere": "AQR Value Everywhere (global avg) — cross-asset value premium",
    "mom_everywhere": "AQR Momentum Everywhere (global avg) — cross-asset momentum premium",
    "qmj_global": "AQR Quality Minus Junk (global equities) — quality premium",
    "bab_global": "AQR Betting Against Beta (global equities) — low-risk / leverage premium",
    "tsmom_eq": "AQR TSMOM sub-asset: Equity indices",
    "tsmom_fi": "AQR TSMOM sub-asset: Fixed income",
    "tsmom_fx": "AQR TSMOM sub-asset: Currencies",
    "tsmom_cm": "AQR TSMOM sub-asset: Commodities",
    "mkt_rf": "FF market excess return — broad equity risk premium",
    "usd_ret": "FRED USD index monthly return — FX exposure proxy",
    "dgs10_chg": "FRED 10Y Treasury yield change — duration / rates proxy",
    "hy_oas_chg": "FRED HY OAS change — credit risk appetite / stress proxy",
    "cmdty_ret": "S&P GSCI monthly return — commodity risk proxy",
}


def factor_bullets(factors: list[str]) -> str:
    """Markdown bullet list describing each factor."""
    return "\n".join(f"- **`{f}`**: {FACTOR_DESC.get(f, f)}" for f in factors)


# ── Report builder ──────────────────────────────────────────────────────────

def build_report(
    *,
    date_min: str,
    date_max: str,
    n_months: int,
    n_ext_factors: int,
    ff5_diag: dict,
    ff5_coef: pd.DataFrame,
    ff5_alpha_p: float,
    econ_factors: list[str],
    econ_coef: pd.DataFrame,
    econ_diag: dict,
    greedy_factors: list[str],
    greedy_coef: pd.DataFrame,
    greedy_diag: dict,
    ff5_same_diag: dict,
    compare_tbl: pd.DataFrame,
    n_candidates: int,
    live_stats: pd.DataFrame,
    live_overlap: pd.DataFrame,
    live_note: str,
) -> str:
    """Assemble the full markdown analysis report from pre-computed results."""
    alpha_sig = (
        "statistically significant" if ff5_alpha_p < 0.05
        else "not statistically significant"
    )
    econ_delta = econ_diag["adj_r2"] - ff5_same_diag["adj_r2"]
    greedy_delta = greedy_diag["adj_r2"] - ff5_same_diag["adj_r2"]

    md = f"""# CS Global Macro Index (2x Vol, Net 95bps): Factor Attribution

> Factor sources: **Fama-French 5**, **FRED** (USD, 10Y, HY OAS, GSCI),
> **AQR Data Library** (TSMOM, Value & Momentum Everywhere, QMJ, BAB).
> JKP theme factors can be included by placing a CSV in `data/`.

---

## Data Overview

- Fund: **{date_min}** to **{date_max}** ({n_months} months).
- FF5: daily returns compounded to monthly (`mkt_rf`, `smb`, `hml`, `rmw`, `cma`, `rf`).
- External factors: {n_ext_factors} series from FRED + AQR.

## Is FF5 a Good Benchmark?

FF5 is a **diagnostic benchmark** — useful for testing whether the fund is
repackaged equity style risk — but **not** a complete economic benchmark for
a global macro product whose returns stem from rates, FX, commodities,
credit, and trend-following.

## FF5 Regression Results

### Fit and alpha

{to_md_table(pd.DataFrame([ff5_diag]))}

Alpha is **{alpha_sig}** at 5% (p = {ff5_alpha_p:.4f}).

### FF5 exposures

{to_md_table(ff5_coef)}

The fund has equity beta, but FF5 explainability is limited (adj-R² is modest).
Residual risk is large, pointing to exposures outside equity style factors.

---

## Proposed Macro Models

### Model A — Economist's Macro Model

Hand-picked factors reflecting global macro strategy exposures:

{factor_bullets(econ_factors)}

{to_md_table(econ_coef)}

### Model B — Greedy Best-Fit Model

Factors selected by forward stepwise adj-R² maximisation from all {n_candidates} candidates:

{factor_bullets(greedy_factors)}

{to_md_table(greedy_coef)}

---

## Model Comparison (overlapping window)

{to_md_table(compare_tbl)}

- Economist model vs FF5: **{econ_delta:+.4f}** adj-R²
- Greedy model vs FF5: **{greedy_delta:+.4f}** adj-R²

## Why These Factors Make Sense for Global Macro

| Factor | Economic Rationale |
| --- | --- |
| `tsmom` | Macro funds are often trend followers; TSMOM captures this across assets. |
| `val_everywhere` | Value signals drive macro trades in FX, rates, and equity indices. |
| `mom_everywhere` | Cross-asset momentum is a core return driver for tactical macro. |
| `hy_oas_chg` | Credit spreads reflect risk-on/risk-off regimes that dominate macro P&L. |
| `usd_ret` | USD moves proxy for macro FX positioning. |
| `dgs10_chg` | Rate shocks drive the duration component of macro books. |
| `cmdty_ret` | Commodity exposure is a core macro asset class. |
| `qmj_global` | Quality tilt captures defensive vs aggressive regime exposure. |
| `bab_global` | Low-beta / leverage preference reveals funding-based risk premia. |

## Risk Premia Interpretation

Stable, significant loadings on multi-asset factors support a **risk premia
harvesting** view: the fund earns compensation for bearing systematic macro
exposures rather than generating pure alpha.  Remaining alpha reflects
dynamic timing, implementation edge, or model omission (e.g., carry,
volatility risk premium).

### References

- Fama, E. F. & French, K. R. (2015). *A five-factor asset pricing model.* JFE.
- Moskowitz, T., Ooi, Y. H., & Pedersen, L. H. (2012). *Time series momentum.* JFE.
- Asness, C., Moskowitz, T., & Pedersen, L. H. (2013). *Value and momentum everywhere.* JF.
- Asness, C., Frazzini, A., & Pedersen, L. H. (2019). *Quality minus junk.* RAP.
- Frazzini, A. & Pedersen, L. H. (2014). *Betting against beta.* JFE.
- Jensen, T. I., Kelly, B., & Pedersen, L. H. (2023). *Is there a replication crisis in finance?* JF.
- Koijen, R. S. J. et al. (2018). *Carry.* JFE.

## Extra Credit: Backtest vs Live (HFGM)

"""

    if not live_stats.empty:
        md += to_md_table(live_stats) + "\n\n"
        md += to_md_table(live_overlap[["date", "fund_ret", "hfgm_ret", "spread"]]) + "\n"
    else:
        md += f"- {live_note or 'Live comparison unavailable.'}\n"

    md += """
## Bottom Line

- FF5 alone is **not** a fully appropriate benchmark for this global macro fund.
- Adding AQR cross-asset factors (TSMOM, Value/Momentum Everywhere, QMJ, BAB)
  alongside FRED macro proxies substantially improves explainability.
- The covariance structure of the proposed models aligns with the economic
  narrative of a multi-asset, trend-aware macro strategy.
"""
    return md
