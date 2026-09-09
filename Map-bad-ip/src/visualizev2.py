#!/usr/bin/env python3
"""
visualizev2.py - Génère un dashboard de cybersécurité avec une carte cyberpunk.

Compatible Plotly >= 6 (traces `Scattermap` / MapLibre, aucun token requis).
Le script est tolérant : si les données sont absentes ou vides, il produit
quand même un `index.html` valide (carte vide + compteurs à zéro).
"""

import os
import pandas as pd
import plotly.graph_objects as go

# Configuration des paths
CLUBCYBER_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
GEO_CSV = os.path.join(DATA_DIR, "geo_enriched.csv")
AGG_CSV = os.path.join(DATA_DIR, "agg_by_country.csv")
OUTPUT_HTML = os.path.join(CLUBCYBER_ROOT, "index.html")

GEO_COLUMNS = ["ip", "source", "latitude", "longitude", "city", "region", "country"]
AGG_COLUMNS = ["country", "country_code", "count"]


def _read_csv_safe(path, expected_columns):
    """Lit un CSV en renvoyant un DataFrame vide (avec les bonnes colonnes)
    si le fichier est absent, vide ou illisible."""
    if not os.path.exists(path) or os.path.getsize(path) == 0:
        return pd.DataFrame(columns=expected_columns)
    try:
        return pd.read_csv(path)
    except Exception as exc:  # pd.errors.EmptyDataError, ParserError, ...
        print(f"⚠️  Lecture impossible de {path}: {exc}")
        return pd.DataFrame(columns=expected_columns)


def prepare_data():
    """Charge et nettoie les données. Renvoie (city_data, df_agg)."""
    df_geo = _read_csv_safe(GEO_CSV, GEO_COLUMNS)
    df_agg = _read_csv_safe(AGG_CSV, AGG_COLUMNS)

    empty_city = pd.DataFrame(columns=["city", "country", "latitude", "longitude", "ip_count"])

    if df_geo.empty or not {"latitude", "longitude"}.issubset(df_geo.columns):
        return empty_city, df_agg

    df_geo = df_geo.copy()
    df_geo["latitude"] = pd.to_numeric(df_geo["latitude"], errors="coerce")
    df_geo["longitude"] = pd.to_numeric(df_geo["longitude"], errors="coerce")
    df_geo = df_geo.dropna(subset=["latitude", "longitude"])
    df_geo = df_geo[
        df_geo["latitude"].between(-90, 90)
        & df_geo["longitude"].between(-180, 180)
    ]

    if df_geo.empty:
        return empty_city, df_agg

    for col in ("city", "country"):
        if col not in df_geo.columns:
            df_geo[col] = "?"
        df_geo[col] = df_geo[col].fillna("?")

    city_data = (
        df_geo.groupby(["city", "country"])
        .agg(latitude=("latitude", "mean"), longitude=("longitude", "mean"))
        .reset_index()
    )
    ip_counts = (
        df_geo.groupby(["city", "country"]).size().reset_index(name="ip_count")
    )
    city_data = city_data.merge(ip_counts, on=["city", "country"])
    return city_data, df_agg


def create_map_figure(city_data):
    """Crée la carte (style sombre, MapLibre — aucun token requis)."""
    fig = go.Figure()

    if not city_data.empty:
        fig.add_trace(
            go.Scattermap(
                lat=city_data["latitude"],
                lon=city_data["longitude"],
                mode="markers",
                marker=go.scattermap.Marker(
                    size=city_data["ip_count"].apply(lambda x: min(15, 5 + x / 10)),
                    color=city_data["ip_count"],
                    colorscale="Viridis",
                    showscale=False,
                    opacity=0.8,
                ),
                text=city_data.apply(
                    lambda r: f"<b>{r.city} ({r.country})</b><br>IPs détectées: {r.ip_count}",
                    axis=1,
                ),
                hoverinfo="text",
            )
        )

    fig.update_layout(
        map_style="carto-darkmatter",
        map_zoom=1.5,
        map_center={"lat": 20, "lon": 0},
        margin={"r": 0, "t": 0, "l": 0, "b": 0},
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    return fig


def generate_dashboard_html(fig, df_agg):
    """Génère le HTML complet du dashboard avec CSS cyberpunk."""
    if not df_agg.empty and "count" in df_agg.columns:
        total_ips = int(df_agg["count"].sum())
        label_col = "country" if "country" in df_agg.columns else df_agg.columns[0]
        top_countries = df_agg.sort_values(by="count", ascending=False).head(5)
        top_list_html = "".join(
            "<li style='display:flex; justify-content:space-between; margin-bottom:10px; "
            "border-bottom: 1px solid #1f2937; padding-bottom:5px;'>"
            f"<span>{row[label_col]}</span>"
            f"<span style='color:#ff003c; font-weight:bold;'>{int(row['count'])}</span>"
            "</li>"
            for _, row in top_countries.iterrows()
        )
    else:
        total_ips = 0
        top_list_html = "<li style='color:#8b949e;'>Aucune donnée</li>"

    plotly_div = fig.to_html(
        full_html=False, include_plotlyjs="cdn", config={"displayModeBar": False}
    )

    return f"""<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ClubCyber - Threat Map</title>
    <link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700&family=JetBrains+Mono:wght@400;700&display=swap" rel="stylesheet">
    <style>
        body {{
            margin: 0;
            padding: 0;
            background-color: #0d1117;
            color: #00ff41;
            font-family: 'JetBrains Mono', monospace;
            overflow: hidden;
        }}
        #dashboard {{
            display: grid;
            grid-template-columns: 350px 1fr;
            height: 100vh;
            width: 100vw;
        }}
        #sidebar {{
            background-color: #0a0d12;
            border-right: 2px solid #1f2937;
            padding: 20px;
            display: flex;
            flex-direction: column;
            z-index: 10;
            box-shadow: 10px 0 20px rgba(0,0,0,0.5);
        }}
        h1 {{
            font-family: 'Orbitron', sans-serif;
            font-size: 1.5rem;
            color: #ff003c;
            text-transform: uppercase;
            letter-spacing: 2px;
            margin-top: 0;
            border-bottom: 2px solid #ff003c;
            padding-bottom: 10px;
            text-shadow: 0 0 10px rgba(255, 0, 60, 0.5);
        }}
        .stat-box {{
            background: #161b22;
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 20px;
            border: 1px solid #30363d;
        }}
        .stat-label {{ color: #8b949e; font-size: 0.8rem; text-transform: uppercase; }}
        .stat-value {{ font-size: 2rem; font-weight: bold; color: #0bc9ee; }}
        #map-container {{ position: relative; width: 100%; height: 100%; }}
        .top-countries {{ list-style: none; padding: 0; margin-top: 20px; font-size: 0.9rem; }}
        .footer {{ margin-top: auto; font-size: 0.7rem; color: #484f58; text-align: center; }}
        .js-plotly-plot {{ height: 100% !important; }}
    </style>
</head>
<body>
    <div id="dashboard">
        <div id="sidebar">
            <h1>Club-Cyber</h1>
            <div class="stat-box">
                <div class="stat-label">Total IPs Malveillantes</div>
                <div class="stat-value">{total_ips}</div>
            </div>
            <div class="stat-box">
                <div class="stat-label">Top 5 - Pays Sources</div>
                <ul class="top-countries">
                    {top_list_html}
                </ul>
            </div>
            <div class="stat-box" style="border-color: #ff003c44;">
                <div class="stat-label">Status</div>
                <div style="color: #00ff41; font-weight:bold;">● SYSTÈME ACTIF</div>
            </div>
            <div class="footer">
                Généré par VisualizeV2 - © rapatt<br>
                ClubCyber Threat Intelligence
            </div>
        </div>
        <div id="map-container">
            {plotly_div}
        </div>
    </div>
</body>
</html>
"""


def main():
    print("🛠️  Préparation des données...")
    city_data, df_agg = prepare_data()

    print("🌍 Création de la carte...")
    fig = create_map_figure(city_data)

    print("🎨 Génération du dashboard...")
    html_dashboard = generate_dashboard_html(fig, df_agg)

    os.makedirs(os.path.dirname(OUTPUT_HTML), exist_ok=True)
    with open(OUTPUT_HTML, "w", encoding="utf-8") as f:
        f.write(html_dashboard)

    print(f"✅ Dashboard généré : {os.path.abspath(OUTPUT_HTML)}")


if __name__ == "__main__":
    main()
