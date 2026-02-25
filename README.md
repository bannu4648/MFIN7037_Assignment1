# MFIN 7037 — Assignment 1

Three questions spanning asset allocation, smart-beta ETFs, and global macro factor attribution.

---

## Repository Structure

```
MFIN7037_Assignment1/
├── README.md                  ← this file
├── requirements.txt           ← combined dependencies for all three questions
│
├── Question 1/                ← Asset Allocation
│   ├── README.md
│   ├── requirements.txt
│   ├── code/
│   │   ├── Q1_1_damodaran_empirical_properties.py
│   │   ├── Q1_2_mpf_category_summary_stats.py
│   │   ├── Q1_6_global_vs_hk_equity_comparison.py
│   │   └── Q1_7_etf_vs_mpf_comparison.py
│   └── data/
│       ├── histretSP.xls
│       └── mpf_category_annual_returns.csv
│
├── Question 2/                ← Smart Beta ETFs (SPMO)
│   ├── README_Q2.md
│   ├── requirements.txt
│   ├── q2_config.py           ← dates, tickers, URLs — edit here to customise
│   ├── q2_common.py           ← shared download helpers
│   ├── q2_1_spmo_umd_beta.py
│   ├── q2_2_methodology.py
│   ├── q2_3_long_leg.py
│   ├── q2_4_ff6_controls.py
│   ├── q2_5_other_etfs.py
│   ├── q2_report.py
│   └── q2_run_all.py
│
└── Question 3/                ← Global Macro Factor Attribution
    ├── README.md
    ├── requirements.txt
    ├── code/
    │   ├── data_prep.py       ← data loading + FRED / AQR / JKP fetching
    │   ├── model_utils.py     ← OLS helpers, diagnostics, comparison tables
    │   └── run_analysis.py    ← single entry-point: full pipeline
    └── data/
        ├── CS Global Macro Index at 2x Vol Net of 95bps 2025.09.xlsx
        ├── ff.five_factor.parquet
        └── output_data/       ← all generated outputs (created on first run)
```

---

## Setup & Run Instructions

### 1. Install dependencies

From the root `MFIN7037_Assignment1/` folder:

```bash
python3 -m venv .venv
source .venv/bin/activate        # macOS / Linux
# .venv\Scripts\activate         # Windows

pip install -r requirements.txt
```

### 2. Question 1 — Asset Allocation

> **Q1.3, Q1.4, Q1.5** are answered in slides and video — no code.

Ensure the following files are in `Question 1/data/` before running:
- `histretSP.xls` — Damodaran US historical returns. Download from [here](https://www.stern.nyu.edu/~adamodar/pc/datasets/histretSP.xls) if missing.
- `mpf_category_annual_returns.csv` — MPF category annual returns, from course Dropbox.

```bash
cd "Question 1"
python code/Q1_1_damodaran_empirical_properties.py
python code/Q1_2_mpf_category_summary_stats.py
python code/Q1_6_global_vs_hk_equity_comparison.py
python code/Q1_7_etf_vs_mpf_comparison.py
```

Outputs are written to `Question 1/results/` (auto-created on first run).

### 3. Question 2 — Smart Beta ETFs (SPMO)

All data is downloaded automatically at runtime. To customise the sample period or tickers, edit `q2_config.py`.

```bash
cd "Question 2"
python q2_run_all.py             # recommended: runs Q2.1 → Q2.5 → report

# or run individually:
python q2_1_spmo_umd_beta.py
python q2_2_methodology.py
python q2_3_long_leg.py
python q2_4_ff6_controls.py
python q2_5_other_etfs.py
python q2_report.py
```

Outputs are written to the `Question 2/` folder.

### 4. Question 3 — Global Macro Factor Attribution

All input data is already in `Question 3/data/`. External factors (FRED, AQR) are fetched at runtime and cached locally after the first run.

```bash
cd "Question 3"
python code/run_analysis.py
```

Outputs are written to `Question 3/data/output_data/` (auto-created on first run).

---

## What It Contains

### Question 1 — Asset Allocation

| Sub-question | Script | Description | Outputs (`results/`) |
|---|---|---|---|
| **Q1.1 / Q1.2** | `Q1_1_damodaran_empirical_properties.py` | Sharpe ratio, annualised return, std dev, correlation matrix of US asset classes (Damodaran data); last 30 years vs prior period | `damodaran_stats_full.csv`, `damodaran_stats_last30.csv`, `damodaran_stats_prior.csv`, `damodaran_corr_full.csv`, `damodaran_corr_last30.csv`, `damodaran_histret_loaded.csv` |
| **Q1.2 (suppl.)** | `Q1_2_mpf_category_summary_stats.py` | MPF category summary stats (mean return, volatility, Sharpe) and allocation-fund correlations | `summary_stats_full_sample.csv`, `summary_stats_2010_2024.csv`, `summary_stats_allocation_funds_*.csv`, `correlation_allocation_funds.csv` |
| **Q1.6** | `Q1_6_global_vs_hk_equity_comparison.py` | Global market portfolio vs HK / Greater China equities since 2009–2010; cumulative growth and annualised return | `q16_cumulative_global_vs_hk.csv` |
| **Q1.7** *(extra credit)* | `Q1_7_etf_vs_mpf_comparison.py` | VT ETF (Vanguard Total World, via Yahoo Finance) vs HK equities and MPF global equity; fee and tax impact | `q17_etf_vs_mpf.csv` |

### Question 2 — Smart Beta ETFs (SPMO)

| Sub-question | Script | Description | Outputs (`Question 2/`) |
|---|---|---|---|
| **Q2.1** | `q2_1_spmo_umd_beta.py` | Beta of SPMO to the UMD momentum factor; is the ETF "broken"? | `q2_1_regression_summary.csv`, `q2_1_spmo_umd_data.csv`, `q2_1_..._diagnostics.png` |
| **Q2.2** | `q2_2_methodology.py` | SPMO's official methodology vs academic UMD construction | `q2_2_methodology_comparison.csv` |
| **Q2.3** *(extra credit)* | `q2_3_long_leg.py` | Beta to the long leg (winners only); VW vs EW momentum | `q2_3_all_models_summary.csv`, `q2_3_momentum_portfolios.csv`, `q2_3_..._decomposition.png` |
| **Q2.4** | `q2_4_ff6_controls.py` | Fama-French 6-factor controls; market beta, size bias | `q2_4_ff6_regression_results.csv` |
| **Q2.5** *(optional)* | `q2_5_other_etfs.py` | Two other momentum ETFs with FF6 loadings | `q2_5_other_etfs_ff6.csv` |
| **Report** | `q2_report.py` | Compiles all CSV results into a written report | `REPORT_Q2.md`, `REPORT_Q2.pdf` |

### Question 3 — Global Macro Factor Attribution

Analysis of the **CS Global Macro Index at 2x Vol Net of 95bps** monthly return series. A single script (`run_analysis.py`) runs the full pipeline.

| Analysis step | Description | Outputs (`data/output_data/`) |
|---|---|---|
| **FF5 regression** | OLS benchmark — is the fund just repackaged equity style risk? | `ff5_coefficients.csv` |
| **Economist's macro model** | Hand-picked 5 factors: `mkt_rf`, `tsmom`, `val_everywhere`, `hy_oas_chg`, `usd_ret` | `econ_model_coefficients.csv` |
| **Greedy best-fit model** | Forward stepwise selection maximising adj-R² from 14 candidates (capped at 5 factors) | `greedy_model_coefficients.csv` |
| **Model comparison** | FF5 vs Economist vs Greedy on the same date window | `model_comparison.csv` |
| **Factor data** | All merged FRED + AQR factors; offline caches | `external_factors_monthly.csv`, `fred_factors_monthly.csv`, `aqr_factors_monthly.csv` |
| **Extra credit** | HFGM ETF vs backtest: correlation, beta, tracking error, return spread | `hfgm_monthly_returns.csv`, `live_vs_backtest_stats.csv` |
| **Full write-up** | Markdown report of all results | `analysis_global_macro.md` |

**External factors fetched at runtime:**

| Source | Factors |
|---|---|
| **FRED** | `usd_ret` (Broad USD index), `dgs10_chg` (10Y Treasury yield), `hy_oas_chg` (HY OAS spread), `cmdty_ret` (S&P GSCI via Yahoo Finance) |
| **AQR Data Library** | `tsmom`, `tsmom_eq/fi/fx/cm`, `val_everywhere`, `mom_everywhere`, `qmj_global`, `bab_global` |
| **JKP (optional)** | Place `data/jkp_theme_factors_monthly.csv` (from WRDS / jkpfactors.com) — pipeline picks it up automatically |

**Key results:**

| Model | Adj-R² | vs FF5 |
|---|---|---|
| FF5 | ~9.5% | baseline |
| Economist's Macro | ~30.9% | +21.4 pp |
| Greedy Best-Fit | ~40.1% | +30.6 pp |

The single largest driver is **TSMOM** (t-stat ≈ 7.6), confirming heavy trend-following exposure. Credit stress (`hy_oas_chg`), FX (`usd_ret`), and commodities (`cmdty_ret`) are also significant.

---

## Dependencies Summary

| Package | Q1 | Q2 | Q3 | Purpose |
|---|:---:|:---:|:---:|---|
| `numpy` | ✓ | ✓ | ✓ | Numerical computation |
| `pandas` | ✓ | ✓ | ✓ | Data manipulation |
| `yfinance` | ✓ | ✓ | ✓ | Download equity / ETF price history |
| `xlrd==1.2.0` | ✓ | ✓ | — | Read legacy `.xls` files (Damodaran `histretSP.xls`) |
| `openpyxl` | ✓ | — | ✓ | Read `.xlsx` files |
| `pyarrow` | — | — | ✓ | Read `.parquet` files (FF5 factor data) |
| `requests` | — | ✓ | ✓ | Download Ken French zip files, FRED, AQR data |
| `statsmodels` | — | ✓ | ✓ | OLS regressions and diagnostic tests |
| `scipy` | — | ✓ | — | Statistical tests (Jarque-Bera, Q-Q plots) |
| `matplotlib` | — | ✓ | — | Regression diagnostic and decomposition plots |
| `reportlab` | — | ✓ | — | Generate `REPORT_Q2.pdf` |

---

## References

- Damodaran, A. [Historical Returns (US)](https://pages.stern.nyu.edu/~adamodar/New_Home_Page/datacurrent.html) — `histretSP.xls`
- MPFA. [Annual Report 2009-10](https://www.mpfa.org.hk/en/info-centre/publications-articles/annual-reports/annual-report-2009-10)
- Fama, E. F. & French, K. R. (2015). *A five-factor asset pricing model.* JFE.
- Moskowitz, T., Ooi, Y. H., & Pedersen, L. H. (2012). *Time series momentum.* JFE.
- Asness, C., Moskowitz, T., & Pedersen, L. H. (2013). *Value and momentum everywhere.* JF.
- Asness, C., Frazzini, A., & Pedersen, L. H. (2019). *Quality minus junk.* RAP.
- Frazzini, A. & Pedersen, L. H. (2014). *Betting against beta.* JFE.
- Jensen, T. I., Kelly, B., & Pedersen, L. H. (2023). *Is there a replication crisis in finance?* JF.
