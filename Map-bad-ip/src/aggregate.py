import os
import pandas as pd

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
INPUT_CSV = os.path.join(DATA_DIR, "geo_enriched.csv")
OUTPUT_CSV = os.path.join(DATA_DIR, "agg_by_country.csv")

def main():
    df = pd.read_csv(INPUT_CSV)
    
    # Vérifie si 'country_code' existe, sinon on utilise 'country' comme fallback
    if 'country_code' not in df.columns:
        print("[!] 'country_code' non trouvé, utilisation de 'country' comme alternative.")
        df['country_code'] = df['country']  # Assigner la colonne 'country' à 'country_code'

    agg = df.groupby(["country", "country_code"]).size().reset_index(name="count")
    os.makedirs(DATA_DIR, exist_ok=True)
    agg.to_csv(OUTPUT_CSV, index=False)
    print(f"[+] Agrégation terminée : {len(agg)} pays.")

if __name__ == "__main__":
    main()
