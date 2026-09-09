#!/usr/bin/env python3
"""
aggregate.py
Agrège geo_enriched.csv par pays et produit agg_by_country.csv + top_countries.csv.
Tolérant : si la source est absente ou vide, écrit des fichiers vides valides.
"""

import os
import pandas as pd

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
INPUT_CSV = os.path.join(DATA_DIR, "geo_enriched.csv")
OUTPUT_CSV = os.path.join(DATA_DIR, "agg_by_country.csv")
TOP_COUNTRIES_CSV = os.path.join(DATA_DIR, "top_countries.csv")

OUT_COLUMNS = ["country", "country_code", "count"]


def _load():
    if not os.path.exists(INPUT_CSV) or os.path.getsize(INPUT_CSV) == 0:
        return pd.DataFrame(columns=["country"])
    try:
        return pd.read_csv(INPUT_CSV)
    except Exception as exc:
        print(f"[!] Lecture impossible de {INPUT_CSV}: {exc}")
        return pd.DataFrame(columns=["country"])


def main():
    os.makedirs(DATA_DIR, exist_ok=True)
    df = _load()

    if df.empty or "country" not in df.columns or df["country"].dropna().empty:
        print("[!] Aucune donnée à agréger — écriture de fichiers vides.")
        empty = pd.DataFrame(columns=OUT_COLUMNS)
        empty.to_csv(OUTPUT_CSV, index=False)
        empty.to_csv(TOP_COUNTRIES_CSV, index=False)
        return

    df = df.copy()
    df["country"] = df["country"].fillna("?")
    if "country_code" not in df.columns:
        df["country_code"] = df["country"]
    df["country_code"] = df["country_code"].fillna(df["country"])

    agg = (
        df.groupby(["country", "country_code"])
        .size()
        .reset_index(name="count")
        .sort_values(by="count", ascending=False)
        .reset_index(drop=True)
    )

    agg.to_csv(OUTPUT_CSV, index=False)
    agg.to_csv(TOP_COUNTRIES_CSV, index=False)

    print(f"[+] Agrégation terminée : {len(agg)} pays.")
    print("\n[+] Top 10 :")
    print(agg.head(10).to_string(index=False))


if __name__ == "__main__":
    main()
