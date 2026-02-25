# Question 1 — Asset Allocation

## Overview

This folder contains code and data for **MFIN7037 Assignment 1, Question 1 (Asset Allocation)**. It produces:

- **Q1.1 / Q1.2:** Empirical properties (Sharpe ratio, annualized return, correlation) of US asset classes from Damodaran’s historical returns; comparison of last 30 years vs prior period.
- **Q1.2 (supplementary):** MPF category summary statistics (mean return, volatility, Sharpe) and allocation-fund correlations.
- **Q1.6:** Global vs HK/Greater China equity performance since 2009–2010 (cumulative growth and annualised return).
- **Q1.7 (extra credit):** ETF vs MPF — VT (Vanguard Total World) actual returns from Yahoo Finance vs HK equities and vs MPF global equity; how much better is the ETF than MPF funds.

**Q1.3, Q1.4, and Q1.5** are answered in the **slides and video** (no code in this repo).

Scripts write outputs to the `results/` folder (create it by running the scripts).

---

## Directory structure

```
Question 1/
├── README.md
├── requirements.txt
├── code/
│   ├── Q1_1_damodaran_empirical_properties.py   # Q1.1 & Q1.2 — Damodaran stats + correlation
│   ├── Q1_2_mpf_category_summary_stats.py       # Q1.2 — MPF category summary stats
│   ├── Q1_6_global_vs_hk_equity_comparison.py   # Q1.6 — Global vs HK equity
│   └── Q1_7_etf_vs_mpf_comparison.py            # Q1.7 — ETF (VT) vs MPF & HK equities
├── data/
│   ├── mpf_category_annual_returns.csv          # MPF category returns (course Dropbox)
│   ├── histretSP.xls                            # Damodaran (required for Q1.1/Q1.2); download if missing
│   └── README.txt                               # What to place in data/
└── results/                                     # Created by scripts; output CSVs
```

---

## Data

| File | Description |
|------|-------------|
| `mpf_category_annual_returns.csv` | MPF category average returns (HK scheme), from course Dropbox. |
| `histretSP.xls` | Damodaran US historical returns (1928–2025). Download from [Damodaran — Historical Returns](https://www.stern.nyu.edu/~adamodar/pc/datasets/histretSP.xls) and place in `data/`. Required for Q1.1/Q1.2. |

---

## How to run

From the **Question 1** directory:

```bash
# 1. Create and activate a virtual environment (optional but recommended)
python -m venv .venv
.venv\Scripts\activate   # Windows
# source .venv/bin/activate   # macOS/Linux

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run each script (outputs go to results/)
python code/Q1_1_damodaran_empirical_properties.py
python code/Q1_2_mpf_category_summary_stats.py
python code/Q1_6_global_vs_hk_equity_comparison.py
python code/Q1_7_etf_vs_mpf_comparison.py
```

Scripts read from `data/` (or project root if a file is missing in `data/`) and write to `results/`. Ensure `data/mpf_category_annual_returns.csv` and `data/histretSP.xls` are present (or in project root) before running.

---

## Outputs

Each script writes CSV(s) into `results/` when run from the **Question 1** directory.

| Script | Main outputs |
|--------|--------------|
| `Q1_1_damodaran_empirical_properties.py` | `damodaran_stats_full.csv`, `damodaran_stats_last30.csv`, `damodaran_stats_prior.csv`, `damodaran_corr_full.csv`, `damodaran_corr_last30.csv`, `damodaran_histret_loaded.csv` |
| `Q1_2_mpf_category_summary_stats.py` | `summary_stats_full_sample.csv`, `summary_stats_2010_2024.csv`, `summary_stats_allocation_funds_*.csv`, `correlation_allocation_funds.csv` |
| `Q1_6_global_vs_hk_equity_comparison.py` | `q16_cumulative_global_vs_hk.csv` |
| `Q1_7_etf_vs_mpf_comparison.py` | `q17_etf_vs_mpf.csv` (uses yfinance for VT) |

---

## References

- Damodaran: [Data for current year](https://pages.stern.nyu.edu/~adamodar/New_Home_Page/datacurrent.html) — Historical Returns (US), histretSP.xls.
- MPFA: [Annual Report 2009-10](https://www.mpfa.org.hk/en/info-centre/publications-articles/annual-reports/annual-report-2009-10) (for Q1.4 narrative; no script).
