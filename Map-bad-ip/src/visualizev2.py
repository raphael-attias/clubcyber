#!/usr/bin/env python3
"""
visualizev2.py - Génère un dashboard de cybersécurité avec une carte Mapbox cyberpunk.
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

def prepare_data():
    """Charge et nettoie les données"""
    try:
        df_geo = pd.read_csv(GEO_CSV)
        df_agg = pd.read_csv(AGG_CSV)
        
        # Nettoyage des coordonnées
        df_geo = df_geo.dropna(subset=['latitude', 'longitude'])
        df_geo = df_geo[
            (df_geo['latitude'].between(-90, 90)) & 
            (df_geo['longitude'].between(-180, 180))
        ]
        
        # Agrégation par ville
        city_data = df_geo.groupby(['city', 'country']).agg({
            'latitude': 'mean',
            'longitude': 'mean'
        }).reset_index()
        
        # Comptage des IPs
        ip_counts = df_geo.groupby(['city', 'country']).size().reset_index(name='ip_count')
        city_data = city_data.merge(ip_counts, on=['city', 'country'])
        
        return city_data, df_agg
    
    except Exception as e:
        print(f"❌ Erreur préparation données: {str(e)}")
        raise

def create_mapbox_figure(city_data):
    """Crée la carte Mapbox style Darkmatter"""
    
    fig = go.Figure()

    # Ajout des marqueurs (villes avec IPs)
    fig.add_trace(go.Scattermapbox(
        lat=city_data["latitude"],
        lon=city_data["longitude"],
        mode='markers',
        marker=go.scattermapbox.Marker(
            size=city_data["ip_count"].apply(lambda x: min(15, 5 + x/10)), # Taille dynamique plafonnée
            color=city_data["ip_count"],
            colorscale='Viridis', # Ou Custom: [[0, 'cyan'], [1, 'red']]
            showscale=False,
            opacity=0.8
        ),
        text=city_data.apply(
            lambda r: f"<b>{r.city} ({r.country})</b><br>IPs détectées: {r.ip_count}", axis=1
        ),
        hoverinfo='text'
    ))

    # Configuration du layout Mapbox
    fig.update_layout(
        mapbox_style="carto-darkmatter",
        mapbox_zoom=1.5,
        mapbox_center={"lat": 20, "lon": 0},
        margin={"r":0,"t":0,"l":0,"b":0},
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
    )
    
    return fig

def generate_dashboard_html(fig, df_agg):
    """Génère le HTML complet du dashboard avec CSS Cyberpunk"""
    
    # Calcul des stats
    total_ips = df_agg['count'].sum()
    top_countries = df_agg.sort_values(by='count', ascending=False).head(5)
    
    # Génération du top 5 HTML
    top_list_html = "".join([
        f"<li style='display:flex; justify-content:space-between; margin-bottom:10px; border-bottom: 1px solid #1f2937; padding-bottom:5px;'>"
        f"<span>{{row['country']}}</span><span style='color:#ff003c; font-weight:bold;'>{{row['count']}}</span>"
        f"</li>" for _, row in top_countries.iterrows()
    ])

    plotly_div = fig.to_html(full_html=False, include_plotlyjs='cdn', config={'displayModeBar': False})

    html_content = f"""
    <!DOCTYPE html>
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
                font-family: 'JetBrains+Mono', monospace;
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
            
            #map-container {{
                position: relative;
                width: 100%;
                height: 100%;
            }}
            .top-countries {{
                list-style: none;
                padding: 0;
                margin-top: 20px;
                font-size: 0.9rem;
            }}
            .footer {{
                margin-top: auto;
                font-size: 0.7rem;
                color: #484f58;
                text-align: center;
            }}
            /* Customizing Plotly */
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
    return html_content

def main():
    print("🛠️  Préparation des données...")
    city_data, df_agg = prepare_data()
    
    print("🌍 Création de la carte Mapbox...")
    fig = create_mapbox_figure(city_data)
    
    print("🎨 Génération du Dashboard Cyberpunk...")
    html_dashboard = generate_dashboard_html(fig, df_agg)
    
    print(f"💾 Sauvegarde dans {OUTPUT_HTML}...")
    os.makedirs(os.path.dirname(OUTPUT_HTML), exist_ok=True)
    
    with open(OUTPUT_HTML, "w", encoding="utf-8") as f:
        f.write(html_dashboard)
    
    print("✅ Dashboard généré avec succès!")
    print(f"📌 Emplacement: {os.path.abspath(OUTPUT_HTML)}")

if __name__ == "__main__":
    main()
