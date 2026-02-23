# Question 3 — Global Macro Factor Attribution

## Overview

This project analyses the **CS Global Macro Index at 2x Vol Net of 95bps**
monthly return series and answers:

1. Is Fama-French 5-Factor (FF5) a reasonable benchmark for this fund?
2. What are the FF5 alpha and factor exposures?
3. Can we propose a better 3-5 factor macro benchmark?
4. Does the proposed benchmark improve explainability vs FF5?
5. (Extra credit) How does the backtest compare to the live HFGM ETF?

A single script (`run_analysis.py`) fetches all data, runs every model, and
writes all outputs to `data/output_data/`.

---

## Directory Structure

```
Question 3/
├── README.md
├── requirements.txt
├── code/
│   ├── data_prep.py          # Data loading + FRED / AQR / JKP fetching
│   ├── model_utils.py        # OLS helpers, diagnostics, comparison tables
│   └── run_analysis.py       # Single entry-point: full pipeline
└── data/
    ├── CS Global Macro Index at 2x Vol Net of 95bps 2025.09.xlsx
    ├── ff.five_factor.parquet
    └── output_data/           # All generated outputs (created on first run)
```

---

## Input Data

Already present in `data/`:

| File | Description |
| --- | --- |
| `CS Global Macro Index at 2x Vol Net of 95bps 2025.09.xlsx` | Monthly fund returns (Jan 2002 – Aug 2025) |
| `ff.five_factor.parquet` | Fama-French 5-factor daily returns |

---

## External Factor Sources

### FRED macro proxies

| Factor | FRED Series | Transformation |
| --- | --- | --- |
| `usd_ret` | DTWEXBGS (Broad USD Index) | Month-end level -> % change |
| `dgs10_chg` | DGS10 (10Y Treasury Yield) | Month-end level -> first difference / 100 |
| `hy_oas_chg` | BAMLH0A0HYM2 (HY OAS) | Month-end level -> first difference / 100 |
| `cmdty_ret` | ^SPGSCI via Yahoo Finance | Month-end close -> % change |

### AQR multi-asset factor returns

Downloaded from the [AQR Data Library](https://www.aqr.com/Insights/Datasets):

| Factor | Dataset | What It Captures |
| --- | --- | --- |
| `tsmom` | Time Series Momentum (Moskowitz, Ooi & Pedersen 2012) | Trend-following across equities, FX, rates, commodities |
| `tsmom_eq/fi/fx/cm` | Same (sub-asset breakdowns) | Asset-class-specific trend exposure |
| `val_everywhere` | Value and Momentum Everywhere (Asness, Moskowitz & Pedersen 2013) | Cross-asset value premium |
| `mom_everywhere` | Same | Cross-asset momentum premium |
| `qmj_global` | Quality Minus Junk (Asness, Frazzini & Pedersen 2019) | Quality / defensive premium |
| `bab_global` | Betting Against Beta (Frazzini & Pedersen 2014) | Low-risk / leverage-related premium |

### JKP factors (optional)

[JKP Global Factor Data](https://jkpfactors.com) (Jensen, Kelly & Pedersen 2023)
requires WRDS credentials. To include these factors:

1. Download a theme-level monthly CSV from WRDS or jkpfactors.com.
2. Save as `data/jkp_theme_factors_monthly.csv` with a `date` column.
3. The pipeline picks it up automatically.

### Offline fallback

Every online source (FRED and AQR) is cached as a CSV inside
`data/output_data/` on the first successful run. If the network is
unavailable on a later run, the code automatically loads from the cache
and prints a warning.

---

## Analysis Pipeline

### 1. Data loading

- Fund returns from Excel, standardised to month-end dates.
- FF5 daily parquet compounded to monthly: `(1 + r_daily).prod() - 1`.
- Fund excess return: `fund_ret - rf`.

### 2. FF5 regression (diagnostic benchmark)

OLS of fund excess return on `mkt_rf`, `smb`, `hml`, `rmw`, `cma`.  Tests
whether the fund is just repackaged equity style risk.

### 3. External factors

FRED + AQR data fetched and merged into 14 candidate factors.

### 4. Two proposed macro models

- **Economist's model** — hand-picked 5 factors in priority order reflecting
  macro strategy logic: `mkt_rf`, `tsmom`, `val_everywhere`, `hy_oas_chg`,
  `usd_ret`.
- **Greedy best-fit** — forward stepwise selection maximising adj-R^2 from
  all 14 candidates, capped at 5 factors.

### 5. Model comparison

All three models (FF5, Economist, Greedy) compared on the same date window.

### 6. Extra credit

HFGM ETF (live global macro tracker) returns compared to the fund backtest
over their overlap period: correlation, beta, tracking error, return spread.

---

## Output Files

All written to `data/output_data/`:

| File | Description |
| --- | --- |
| `analysis_global_macro.md` | Full markdown write-up |
| `ff5_coefficients.csv` | FF5 regression coefficients |
| `econ_model_coefficients.csv` | Economist's macro model coefficients |
| `greedy_model_coefficients.csv` | Greedy best-fit model coefficients |
| `model_comparison.csv` | Three-way model comparison |
| `external_factors_monthly.csv` | All merged factor data |
| `fred_factors_monthly.csv` | FRED cache (for offline fallback) |
| `aqr_factors_monthly.csv` | AQR cache (for offline fallback) |
| `hfgm_monthly_returns.csv` | HFGM ETF returns |
| `live_vs_backtest_stats.csv` | Backtest vs live tracking stats |

---

## How To Run

```bash
cd "Question 3"

# 1. Create and activate a virtual environment
python3 -m venv .venv
source .venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run analysis
python code/run_analysis.py
```

---

## Key Results

| Model | Adj-R^2 | vs FF5 |
| --- | --- | --- |
| FF5 | ~9.5% | baseline |
| Economist's Macro | ~30.9% | +21.4 pp |
| Greedy Best-Fit | ~40.1% | +30.6 pp |

The single largest contributor is **TSMOM** (t-stat ~ 7.6), confirming heavy
trend-following exposure. Credit stress (`hy_oas_chg`), FX (`usd_ret`), and
commodities (`cmdty_ret`) are also significant.

---

## References

- Fama, E. F. & French, K. R. (2015). *A five-factor asset pricing model.* JFE.
- Moskowitz, T., Ooi, Y. H., & Pedersen, L. H. (2012). *Time series momentum.* JFE.
- Asness, C., Moskowitz, T., & Pedersen, L. H. (2013). *Value and momentum everywhere.* JF.
- Asness, C., Frazzini, A., & Pedersen, L. H. (2019). *Quality minus junk.* RAP.
- Frazzini, A. & Pedersen, L. H. (2014). *Betting against beta.* JFE.
- Jensen, T. I., Kelly, B., & Pedersen, L. H. (2023). *Is there a replication crisis in finance?* JF.
- Koijen, R. S. J. et al. (2018). *Carry.* JFE.
