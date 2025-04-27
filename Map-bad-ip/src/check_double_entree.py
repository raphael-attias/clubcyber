import pandas as pd

# Chemin du fichier CSV
DATA_DIR = "data"
INPUT_CSV = f"{DATA_DIR}/geo_enriched.csv"

def remove_duplicates():
    # Charger le fichier CSV dans un DataFrame
    df = pd.read_csv(INPUT_CSV)

    # Supprimer les doublons en fonction de la colonne 'ip'
    df_unique = df.drop_duplicates(subset=["ip"])

    # Sauvegarder le fichier sans doublons
    df_unique.to_csv(INPUT_CSV, index=False)
    print(f"[✔] Doublons supprimés, {len(df_unique)} entrées uniques.")

if __name__ == "__main__":
    remove_duplicates()
