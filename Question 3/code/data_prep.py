"""Data preparation — loads local files, fetches FRED macro proxies, AQR
multi-asset factor returns, and HFGM ETF data.

External data sources
---------------------
FRED  : USD index (DTWEXBGS), 10Y yield (DGS10), HY OAS (BAMLH0A0HYM2)
Yahoo : S&P GSCI (^SPGSCI), HFGM ETF
AQR   : TSMOM, Value & Momentum Everywhere, Quality Minus Junk, Betting
        Against Beta  (https://www.aqr.com/Insights/Datasets)
JKP   : Optional local CSV from jkpfactors.com / WRDS

Every online source has a fallback: if the download fails the code looks for
a previously-cached CSV in *cache_dir* (defaults to ``data/output_data/``).
"""

from __future__ import annotations

from io import BytesIO, StringIO
from pathlib import Path

import pandas as pd
import requests
import yfinance as yf

# ── Local file loaders ──────────────────────────────────────────────────────

def load_fund_monthly_returns(xlsx_path: Path) -> pd.DataFrame:
    df = pd.read_excel(xlsx_path)
    df.columns = [str(c).strip().lower() for c in df.columns]
    df = df.rename(columns={"return": "fund_ret", "date": "date"})
    df["date"] = pd.to_datetime(df["date"])
    df["date"] = df["date"].dt.to_period("M").dt.to_timestamp("M")
    df = df[["date", "fund_ret"]].dropna().sort_values("date").reset_index(drop=True)
    return df


def load_ff5_monthly(parquet_path: Path) -> pd.DataFrame:
    ff = pd.read_parquet(parquet_path)
    ff["dt"] = pd.to_datetime(ff["dt"])
    ff["month"] = ff["dt"].dt.to_period("M").dt.to_timestamp("M")
    factor_cols = ["mkt_rf", "smb", "hml", "rmw", "cma", "rf"]
    for col in factor_cols:
        ff[col] = pd.to_numeric(ff[col], errors="coerce")

    ff_monthly = (
        ff.groupby("month")[factor_cols]
        .apply(lambda x: (1.0 + x).prod() - 1.0)
        .reset_index()
        .rename(columns={"month": "date"})
        .sort_values("date")
        .reset_index(drop=True)
    )
    return ff_monthly


def _load_csv_fallback(csv_path: Path) -> pd.DataFrame:
    """Read a date-indexed CSV that was previously cached."""
    df = pd.read_csv(csv_path)
    if "date" not in df.columns:
        raise ValueError(f"CSV is missing 'date' column: {csv_path}")
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["date"]).sort_values("date").reset_index(drop=True)
    return df


# ── FRED helpers ────────────────────────────────────────────────────────────

def _fetch_fred_csv(series_id: str) -> pd.DataFrame:
    url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={series_id}"
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    out = pd.read_csv(StringIO(r.text))
    out.columns = ["date", series_id]
    out["date"] = pd.to_datetime(out["date"], errors="coerce")
    out[series_id] = pd.to_numeric(out[series_id], errors="coerce")
    out = out.dropna(subset=["date"]).sort_values("date").reset_index(drop=True)
    return out


def _fetch_fred_factors(start: str = "2002-01-01") -> pd.DataFrame:
    usd = _fetch_fred_csv("DTWEXBGS")
    dgs10 = _fetch_fred_csv("DGS10")
    hy_oas = _fetch_fred_csv("BAMLH0A0HYM2")

    for df in (usd, dgs10, hy_oas):
        df["date"] = df["date"].dt.to_period("M").dt.to_timestamp("M")

    usd_m = usd.groupby("date", as_index=False)["DTWEXBGS"].last()
    dgs10_m = dgs10.groupby("date", as_index=False)["DGS10"].last()
    hy_m = hy_oas.groupby("date", as_index=False)["BAMLH0A0HYM2"].last()

    usd_m["usd_ret"] = usd_m["DTWEXBGS"].pct_change()
    dgs10_m["dgs10_chg"] = dgs10_m["DGS10"].diff() / 100.0
    hy_m["hy_oas_chg"] = hy_m["BAMLH0A0HYM2"].diff() / 100.0

    cmdty = pd.DataFrame(columns=["date", "cmdty_ret"])
    try:
        c = yf.download("^SPGSCI", start=start, auto_adjust=True, progress=False)
        if not c.empty:
            close = c["Close"].iloc[:, 0] if isinstance(c.columns, pd.MultiIndex) else c["Close"]
            close = close.rename("close").to_frame()
            close.index = pd.to_datetime(close.index)
            close["date"] = close.index.to_period("M").to_timestamp("M")
            cmdty = (
                close.groupby("date", as_index=False)["close"]
                .last()
                .assign(cmdty_ret=lambda x: x["close"].pct_change())[["date", "cmdty_ret"]]
            )
    except Exception:
        pass

    out = (
        usd_m[["date", "usd_ret"]]
        .merge(dgs10_m[["date", "dgs10_chg"]], on="date", how="outer")
        .merge(hy_m[["date", "hy_oas_chg"]], on="date", how="outer")
        .merge(cmdty, on="date", how="outer")
        .sort_values("date")
        .reset_index(drop=True)
    )
    return out[out["date"] >= pd.Timestamp(start)]


# ── AQR helpers ─────────────────────────────────────────────────────────────

_AQR_BASE = "https://www.aqr.com/-/media/AQR/Documents/Insights/Data-Sets"
_AQR_URLS = {
    "tsmom": f"{_AQR_BASE}/Time-Series-Momentum-Factors-Monthly.xlsx",
    "vme": f"{_AQR_BASE}/Value-and-Momentum-Everywhere-Factors-Monthly.xlsx",
    "qmj": f"{_AQR_BASE}/Quality-Minus-Junk-Factors-Monthly.xlsx",
    "bab": f"{_AQR_BASE}/Betting-Against-Beta-Equity-Factors-Monthly.xlsx",
}


def _parse_aqr_tsmom(raw: bytes) -> pd.DataFrame:
    xls = pd.ExcelFile(BytesIO(raw))
    df = pd.read_excel(xls, sheet_name="TSMOM Factors", header=None)

    hdr_idx = None
    for i in range(min(25, len(df))):
        if "TSMOM" in [str(v).strip().upper() for v in df.iloc[i] if pd.notna(v)]:
            hdr_idx = i
            break
    if hdr_idx is None:
        raise ValueError("Could not locate header row in TSMOM sheet")

    col_names = []
    for j, v in enumerate(df.iloc[hdr_idx]):
        if pd.notna(v):
            col_names.append(str(v).strip())
        elif j == 0:
            col_names.append("date")
        else:
            col_names.append(f"_col{j}")
    df.columns = col_names
    df = df.iloc[hdr_idx + 1:].copy()
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["date"])

    rename = {"TSMOM": "tsmom", "TSMOM^EQ": "tsmom_eq", "TSMOM^FI": "tsmom_fi",
              "TSMOM^FX": "tsmom_fx", "TSMOM^CM": "tsmom_cm"}
    keep = ["date"] + [c for c in rename if c in df.columns]
    df = df[keep].rename(columns=rename)
    for c in df.columns:
        if c != "date":
            df[c] = pd.to_numeric(df[c], errors="coerce")
    df["date"] = df["date"].dt.to_period("M").dt.to_timestamp("M")
    return df.sort_values("date").reset_index(drop=True)


def _parse_aqr_vme(raw: bytes) -> pd.DataFrame:
    xls = pd.ExcelFile(BytesIO(raw))
    df = pd.read_excel(xls, sheet_name="VME Factors", header=None)

    hdr_idx = None
    for i in range(min(30, len(df))):
        vals = [str(v).strip().upper() for v in df.iloc[i] if pd.notna(v)]
        if "DATE" in vals and "VAL" in vals:
            hdr_idx = i
            break
    if hdr_idx is None:
        raise ValueError("Could not locate header row in VME sheet")

    df.columns = [str(v).strip() if pd.notna(v) else f"_col{j}" for j, v in enumerate(df.iloc[hdr_idx])]
    df = df.iloc[hdr_idx + 1:].copy()
    df = df.rename(columns={"DATE": "date"})
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["date"])

    rename = {"VAL": "val_everywhere", "MOM": "mom_everywhere"}
    keep = ["date"] + [c for c in rename if c in df.columns]
    df = df[keep].rename(columns=rename)
    for c in df.columns:
        if c != "date":
            df[c] = pd.to_numeric(df[c], errors="coerce")
    df["date"] = df["date"].dt.to_period("M").dt.to_timestamp("M")
    return df.sort_values("date").reset_index(drop=True)


def _parse_aqr_country_factor(raw: bytes, sheet: str, col_name: str) -> pd.DataFrame:
    xls = pd.ExcelFile(BytesIO(raw))
    df = pd.read_excel(xls, sheet_name=sheet, header=None)

    hdr_idx = None
    for i in range(min(25, len(df))):
        vals = [str(v).strip().upper() for v in df.iloc[i] if pd.notna(v)]
        if "DATE" in vals and "GLOBAL" in vals:
            hdr_idx = i
            break
    if hdr_idx is None:
        raise ValueError(f"Could not locate header row in {sheet}")

    df.columns = [str(v).strip() if pd.notna(v) else f"_col{j}" for j, v in enumerate(df.iloc[hdr_idx])]
    df = df.iloc[hdr_idx + 1:].copy()
    df = df.rename(columns={"DATE": "date"})
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["date"])

    if "Global" not in df.columns:
        raise ValueError(f"'Global' column not found in {sheet}")

    out = df[["date", "Global"]].rename(columns={"Global": col_name})
    out[col_name] = pd.to_numeric(out[col_name], errors="coerce")
    out["date"] = out["date"].dt.to_period("M").dt.to_timestamp("M")
    return out.sort_values("date").reset_index(drop=True)


def _fetch_aqr_factors(start: str = "2002-01-01") -> pd.DataFrame:
    merged = pd.DataFrame()
    errors: list[str] = []

    for key in ("tsmom", "vme", "qmj", "bab"):
        try:
            r = requests.get(_AQR_URLS[key], timeout=60)
            r.raise_for_status()
            if key == "tsmom":
                part = _parse_aqr_tsmom(r.content)
            elif key == "vme":
                part = _parse_aqr_vme(r.content)
            elif key == "qmj":
                part = _parse_aqr_country_factor(r.content, "QMJ Factors", "qmj_global")
            else:
                part = _parse_aqr_country_factor(r.content, "BAB Factors", "bab_global")

            merged = part if merged.empty else merged.merge(part, on="date", how="outer")
        except Exception as exc:
            errors.append(f"{key}: {type(exc).__name__}: {exc}")

    if errors:
        print(f"[data_prep] AQR fetch warnings: {'; '.join(errors)}")
    if merged.empty:
        return pd.DataFrame(columns=["date"])
    return merged[merged["date"] >= pd.Timestamp(start)].sort_values("date").reset_index(drop=True)


# ── JKP (local-only) ───────────────────────────────────────────────────────

def _load_jkp_local(data_dir: Path) -> pd.DataFrame:
    """Load JKP theme factors from a manually placed CSV (requires WRDS)."""
    p = data_dir / "jkp_theme_factors_monthly.csv"
    if not p.exists():
        return pd.DataFrame(columns=["date"])
    df = pd.read_csv(p)
    if "date" not in df.columns:
        raise ValueError("JKP CSV missing 'date' column")
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["date"]).sort_values("date").reset_index(drop=True)
    df["date"] = df["date"].dt.to_period("M").dt.to_timestamp("M")
    return df


# ── Public entry-points ────────────────────────────────────────────────────

def fetch_all_external_factors(start: str = "2002-01-01",
                               cache_dir: Path | None = None,
                               data_dir: Path | None = None) -> pd.DataFrame:
    """Fetch FRED + AQR factors, merge, and return a single monthly DataFrame.

    On success each source is cached as a CSV inside *cache_dir* so the next
    run can fall back to local data if the network is unavailable.

    Parameters
    ----------
    start : str
        Earliest date to include (ISO format).
    cache_dir : Path | None
        Folder where cached CSVs are written / read.  Typically
        ``data/output_data/``.
    data_dir : Path | None
        Folder containing input data and optional JKP CSV.
    """
    warnings: list[str] = []

    # --- FRED ---
    fred_cache = cache_dir / "fred_factors_monthly.csv" if cache_dir else None
    try:
        fred = _fetch_fred_factors(start=start)
        if fred_cache:
            fred.to_csv(fred_cache, index=False)
    except Exception as e:
        if fred_cache and fred_cache.exists():
            fred = _load_csv_fallback(fred_cache)
            warnings.append(f"FRED online failed ({e}); loaded local cache.")
        else:
            warnings.append(f"FRED online failed ({e}); no cache available.")
            fred = pd.DataFrame(columns=["date"])

    # --- AQR ---
    aqr_cache = cache_dir / "aqr_factors_monthly.csv" if cache_dir else None
    try:
        aqr = _fetch_aqr_factors(start=start)
        if aqr.empty:
            raise RuntimeError("AQR returned empty data")
        if aqr_cache:
            aqr.to_csv(aqr_cache, index=False)
    except Exception as e:
        if aqr_cache and aqr_cache.exists():
            aqr = _load_csv_fallback(aqr_cache)
            warnings.append(f"AQR online failed ({e}); loaded local cache.")
        else:
            warnings.append(f"AQR online failed ({e}); no cache available.")
            aqr = pd.DataFrame(columns=["date"])

    # --- JKP (local-only, optional) ---
    jkp = pd.DataFrame(columns=["date"])
    if data_dir:
        try:
            jkp = _load_jkp_local(data_dir)
        except Exception as exc:
            warnings.append(f"JKP local load failed: {exc}")

    # --- Merge ---
    out = fred.copy() if not fred.empty else pd.DataFrame(columns=["date"])
    for part in (aqr, jkp):
        if not part.empty and "date" in part.columns:
            if out.empty or "date" not in out.columns or len(out) == 0:
                out = part
            else:
                out = out.merge(part, on="date", how="outer")

    if not out.empty and "date" in out.columns:
        out = out[out["date"] >= pd.Timestamp(start)].sort_values("date").reset_index(drop=True)

    if warnings:
        for w in warnings:
            print(f"[data_prep] {w}")

    return out


def fetch_hfgm_monthly_returns(start: str = "2022-01-01") -> pd.DataFrame:
    h = yf.download("HFGM", start=start, auto_adjust=True, progress=False)
    if h.empty:
        return pd.DataFrame(columns=["date", "hfgm_ret"])
    close = h["Close"].iloc[:, 0] if isinstance(h.columns, pd.MultiIndex) else h["Close"]
    close = close.rename("close").to_frame()
    close.index = pd.to_datetime(close.index)
    close["date"] = close.index.to_period("M").to_timestamp("M")
    out = (
        close.groupby("date", as_index=False)["close"]
        .last()
        .assign(hfgm_ret=lambda x: x["close"].pct_change())[["date", "hfgm_ret"]]
        .dropna()
        .reset_index(drop=True)
    )
    return out
