import pandas as pd
from typing import Dict, Any, Tuple, List

def _try_read(csv_path: str):
    for sep in [",", ";"]:
        for enc in [None, "utf-8", "latin-1"]:
            try:
                df = pd.read_csv(csv_path, sep=sep) if enc is None else pd.read_csv(csv_path, sep=sep, encoding=enc)
                return df
            except Exception:
                continue
    raise FileNotFoundError(f"No pude leer el CSV: {csv_path}")

def load_dataset(csv_path: str) -> Tuple[pd.DataFrame, Dict[str, float], float]:
    df = _try_read(csv_path)
    year_cols: List[str] = [c for c in df.columns if isinstance(c, str) and c.startswith("F") and c[1:].isdigit()]
    if not year_cols:
        raise ValueError("No encontré columnas F1961..F2022 en el CSV.")

    df["mean_change"] = df[year_cols].mean(axis=1, skipna=True)
    per_year_mean = {c[1:]: df[c].mean(skipna=True) for c in year_cols}
    global_mean = df[year_cols].stack().mean()
    df = df.dropna(subset=["mean_change"]).reset_index(drop=True)
    return df, per_year_mean, global_mean

def to_payload(row: pd.Series) -> Dict[str, Any]:
    series = {c[1:]: row[c] for c in row.index if isinstance(c, str) and c.startswith("F") and c[1:].isdigit()}


    iso_raw = row.get("ISO3")
    iso = (str(iso_raw).strip().upper()) if pd.notna(iso_raw) else ""

    country_raw = row.get("Country")
    country = (str(country_raw).strip()) if pd.notna(country_raw) else ""

    return {
        "ObjectId": row.get("ObjectId"),
        "Country": country,
        "ISO3": iso,
        "mean_change": float(row.get("mean_change")),
        "series": series,
    }
