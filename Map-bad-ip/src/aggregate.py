#!/usr/bin/env python3
"""
aggregate.py
Agrège le nombre d’IP malveillantes par pays à partir de data/geo_enriched.csv
et écrit data/agg_by_country.csv.
"""

import os
import pandas as pd

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
INPUT_CSV = os.path.join(DATA_DIR, "geo_enriched.csv")
OUTPUT_CSV = os.path.join(DATA_DIR, "agg_by_country.csv")

def main():
    df = pd.read_csv(INPUT_CSV)
    agg = df.groupby(["country", "country_code"]).size().reset_index(name="count")
    os.makedirs(DATA_DIR, exist_ok=True)
    agg.to_csv(OUTPUT_CSV, index=False)
    print(f"[+] Agrégation terminée : {len(agg)} pays.")

if __name__ == "__main__":
    main()
