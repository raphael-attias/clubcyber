#!/usr/bin/env python3
"""
visualize.py - Génère la carte dans /clubcyber/index.html
"""

import os
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Configuration des paths - Remonte d'un niveau supplémentaire
CLUBCYBER_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
GEO_CSV = os.path.join(DATA_DIR, "geo_enriched.csv")
AGG_CSV = os.path.join(DATA_DIR, "agg_by_country.csv")
OUTPUT_HTML = os.path.join(CLUBCYBER_ROOT, "index.html")  # Dans /clubcyber

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

def create_map(city_data, df_agg):
    """Crée la visualisation cartographique"""
    min_ip = city_data['ip_count'].min()
    max_ip = city_data['ip_count'].max()
    mid_ip = (max_ip + min_ip) / 2

    # Carte de base
    fig = px.choropleth(
        df_agg,
        locations="country_code",
        color="count",
        hover_name="country",
        color_continuous_scale="Greys",
        range_color=(0, df_agg['count'].max()),
        projection="natural earth"
    )
    
    # Style géographique
    fig.update_geos(
        showcountries=True,
        countrycolor="#555555",
        countrywidth=0.7,
        coastlinecolor="#777777",
        coastlinewidth=1.0,
        landcolor="white",
        showocean=True,
        oceancolor="#e6f3ff"
    )
    fig.update_layout(coloraxis_showscale=False)

    # Marqueurs
    fig.add_trace(
        go.Scattergeo(
            lon=city_data["longitude"],
            lat=city_data["latitude"],
            text=city_data.apply(
                lambda r: (
                    f"<b>{r.city}</b><br>"
                    f"<span style='color:gray'>IPs: </span><b>{r.ip_count}</b><br>"
                    f"<span style='color:gray'>Pays: </span>{r.country}"
                ), axis=1
            ),
            marker=dict(
                size=8,
                color=city_data['ip_count'],
                colorscale=[[0, 'blue'], [0.5, 'yellow'], [1, 'red']],
                cmin=min_ip,
                cmax=max_ip,
                opacity=0.9,
                line=dict(width=0.5, color='black'),
                colorbar=dict(
                    title="<b>Nombre d'IPs</b>",
                    x=1.05,
                    len=0.7,
                    thickness=20,
                    tickvals=[min_ip, mid_ip, max_ip],
                    ticktext=[f"{min_ip}", f"{int(mid_ip)}", f"{max_ip}"],
                    tickfont=dict(size=10)
                )
            ),
            hoverinfo="text",
            hovertemplate="%{text}<extra></extra>",
            mode='markers'
        )
    )

    # Mise en page
    fig.update_layout(
        title_text="<b>Carte des IPs malveillantes by rapatt</b>",
        title_font=dict(size=16, family="Arial"),
        margin=dict(r=120, l=10, t=60, b=10),
        paper_bgcolor="white"
    )
    
    return fig

def main():
    print("🛠️  Préparation des données...")
    city_data, df_agg = prepare_data()
    
    print("🌍 Création de la carte...")
    fig = create_map(city_data, df_agg)
    
    print(f"💾 Sauvegarde dans {OUTPUT_HTML}...")
    # Création du répertoire parent si nécessaire
    os.makedirs(os.path.dirname(OUTPUT_HTML), exist_ok=True)
    
    fig.write_html(
        OUTPUT_HTML,
        include_plotlyjs="cdn",
        full_html=True,
        config={"displayModeBar": True},
        auto_open=False
    )
    
    print("✅ Carte générée avec succès!")
    print(f"📌 Emplacement: {os.path.abspath(OUTPUT_HTML)}")

if __name__ == "__main__":
    main()