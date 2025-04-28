import os
import pandas as pd

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
INPUT_CSV = os.path.join(DATA_DIR, "geo_enriched.csv")
OUTPUT_CSV = os.path.join(DATA_DIR, "agg_by_country.csv")
TOP_COUNTRIES_CSV = os.path.join(DATA_DIR, "top_countries.csv")

def main():
    # Lecture du fichier CSV
    df = pd.read_csv(INPUT_CSV)
    
    # Vérifie si 'country_code' existe, sinon on utilise 'country' comme fallback
    if 'country_code' not in df.columns:
        print("[!] 'country_code' non trouvé, utilisation de 'country' comme alternative.")
        df['country_code'] = df['country']  # Assigner la colonne 'country' à 'country_code'

    # Agrégation par pays et code pays
    agg = df.groupby(["country", "country_code"]).size().reset_index(name="count")
    
    # Trie les pays par nombre d'IP, du plus élevé au plus bas
    top_countries = agg.sort_values(by="count", ascending=False)
    
    # Enregistrer les résultats agrégés dans un fichier CSV
    os.makedirs(DATA_DIR, exist_ok=True)
    agg.to_csv(OUTPUT_CSV, index=False)
    top_countries.to_csv(TOP_COUNTRIES_CSV, index=False)
    
    print(f"[+] Agrégation terminée : {len(agg)} pays.")
    print(f"[+] Résultats agrégés enregistrés dans {OUTPUT_CSV}")
    print(f"[+] Liste des pays les plus touchés enregistrée dans {TOP_COUNTRIES_CSV}")
    
    # Affichage des 10 pays les plus touchés
    print("\n[+] Top 10 des pays les plus touchés :")
    print(top_countries.head(10))

if __name__ == "__main__":
    main()
