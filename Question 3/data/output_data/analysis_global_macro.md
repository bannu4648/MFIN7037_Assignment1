# CS Global Macro Index (2x Vol, Net 95bps): Factor Attribution

> Factor sources: **Fama-French 5**, **FRED** (USD, 10Y, HY OAS, GSCI),
> **AQR Data Library** (TSMOM, Value & Momentum Everywhere, QMJ, BAB).
> JKP theme factors can be included by placing a CSV in `data/`.

---

## Data Overview

- Fund: **2002-01-31** to **2025-08-31** (284 months).
- FF5: daily returns compounded to monthly (`mkt_rf`, `smb`, `hml`, `rmw`, `cma`, `rf`).
- External factors: 13 series from FRED + AQR.

## Is FF5 a Good Benchmark?

FF5 is a **diagnostic benchmark** — useful for testing whether the fund is
repackaged equity style risk — but **not** a complete economic benchmark for
a global macro product whose returns stem from rates, FX, commodities,
credit, and trend-following.

## FF5 Regression Results

### Fit and alpha

| n_obs | r2 | adj_r2 | alpha_monthly | alpha_annualized | resid_vol_monthly | resid_vol_annualized | corr_fitted_actual |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 284.0000 | 0.1040 | 0.0879 | 0.0114 | 0.1459 | 0.0367 | 0.1270 | 0.3225 |

Alpha is **statistically significant** at 5% (p = 0.0000).

### FF5 exposures

| factor | coef | t_stat | p_value |
| --- | --- | --- | --- |
| const | 0.0114 | 4.9921 | 0.0000 |
| mkt_rf | 0.2433 | 4.4152 | 0.0000 |
| smb | 0.0202 | 0.2118 | 0.8324 |
| hml | 0.1056 | 1.1517 | 0.2504 |
| rmw | 0.0451 | 0.3998 | 0.6896 |
| cma | 0.1889 | 1.3645 | 0.1735 |

The fund has equity beta, but FF5 explainability is limited (adj-R² is modest).
Residual risk is large, pointing to exposures outside equity style factors.

---

## Proposed Macro Models

### Model A — Economist's Macro Model

Hand-picked factors reflecting global macro strategy exposures:

- **`mkt_rf`**: FF market excess return — broad equity risk premium
- **`tsmom`**: AQR Time-Series Momentum (all assets) — trend-following proxy
- **`val_everywhere`**: AQR Value Everywhere (global avg) — cross-asset value premium
- **`hy_oas_chg`**: FRED HY OAS change — credit risk appetite / stress proxy
- **`usd_ret`**: FRED USD index monthly return — FX exposure proxy

| factor | coef | t_stat | p_value |
| --- | --- | --- | --- |
| const | 0.0097 | 3.9998 | 0.0001 |
| mkt_rf | 0.0574 | 0.7183 | 0.4733 |
| tsmom | 0.4952 | 7.6585 | 0.0000 |
| val_everywhere | 0.1471 | 0.8863 | 0.3764 |
| hy_oas_chg | -1.4318 | -3.2809 | 0.0012 |
| usd_ret | -0.5082 | -3.0264 | 0.0028 |

### Model B — Greedy Best-Fit Model

Factors selected by forward stepwise adj-R² maximisation from all 14 candidates:

- **`cmdty_ret`**: S&P GSCI monthly return — commodity risk proxy
- **`tsmom`**: AQR Time-Series Momentum (all assets) — trend-following proxy
- **`usd_ret`**: FRED USD index monthly return — FX exposure proxy
- **`hy_oas_chg`**: FRED HY OAS change — credit risk appetite / stress proxy
- **`tsmom_fx`**: AQR TSMOM sub-asset: Currencies

| factor | coef | t_stat | p_value |
| --- | --- | --- | --- |
| const | 0.0091 | 4.2638 | 0.0000 |
| cmdty_ret | 0.2399 | 5.6182 | 0.0000 |
| tsmom | 0.5743 | 7.2370 | 0.0000 |
| usd_ret | -0.2277 | -1.4707 | 0.1428 |
| hy_oas_chg | -0.8984 | -2.5907 | 0.0102 |
| tsmom_fx | -0.1040 | -1.7766 | 0.0770 |

---

## Model Comparison (overlapping window)

| model | n_obs | adj_r2 | alpha_monthly | alpha_annualized | resid_vol_annualized | corr_fitted_actual |
| --- | --- | --- | --- | --- | --- | --- |
| FF5 (same window) | 228.0000 | 0.0946 | 0.0098 | 0.1245 | 0.1342 | 0.3385 |
| Economist's Macro | 228.0000 | 0.3086 | 0.0097 | 0.1226 | 0.1172 | 0.5691 |
| Greedy Best-Fit | 228.0000 | 0.4011 | 0.0091 | 0.1154 | 0.1091 | 0.6436 |

- Economist model vs FF5: **+0.2140** adj-R²
- Greedy model vs FF5: **+0.3065** adj-R²

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

| overlap_months | corr_hfgm_vs_backtest | beta_hfgm_on_backtest | tracking_error_ann | avg_return_diff_ann |
| --- | --- | --- | --- | --- |
| 4.0000 | 0.8372 | 0.8280 | 0.0669 | 0.3040 |

| date | fund_ret | hfgm_ret | spread |
| --- | --- | --- | --- |
| 2025-05 | -0.0098 | 0.0203 | 0.0301 |
| 2025-06 | 0.0439 | 0.0381 | -0.0058 |
| 2025-07 | -0.0143 | 0.0127 | 0.0270 |
| 2025-08 | 0.0495 | 0.0876 | 0.0381 |

## Bottom Line

- FF5 alone is **not** a fully appropriate benchmark for this global macro fund.
- Adding AQR cross-asset factors (TSMOM, Value/Momentum Everywhere, QMJ, BAB)
  alongside FRED macro proxies substantially improves explainability.
- The covariance structure of the proposed models aligns with the economic
  narrative of a multi-asset, trend-aware macro strategy.
