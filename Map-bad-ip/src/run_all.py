import subprocess
import os
import sys
import pandas as pd

# Définir le chemin vers le dossier src
src_folder = os.path.dirname(__file__)
data_folder = os.path.join(src_folder, "..", "data")  # adapte si besoin

# Liste des scripts à exécuter dans le bon ordre
scripts = [
    "fetch_ips.py",
    #"geolocate.py",
    "aggregate.py",
    "visualizev2.py"
]

def prepare_geo_csv():
    geo_csv_path = os.path.join(data_folder, "geo_ips.csv")
    if not os.path.exists(geo_csv_path):
        print("[*] Création du fichier geo_ips.csv vide...")
        df = pd.DataFrame(columns=["ip", "country", "country_code", "latitude", "longitude"])
        df.to_csv(geo_csv_path, index=False)

def run_scripts():
    python_cmd = sys.executable
    for script in scripts:
        script_path = os.path.join(src_folder, script)
        print(f"[*] Running {script}...")
        result = subprocess.run([python_cmd, script_path], capture_output=True, text=True)
        print(result.stdout)
        if result.stderr:
            print(f"[!] Erreur lors de l'exécution de {script}:\n{result.stderr}")

if __name__ == "__main__":
    prepare_geo_csv()
    run_scripts()
