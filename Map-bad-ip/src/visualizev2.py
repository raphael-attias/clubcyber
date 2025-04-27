#!/usr/bin/env python3
"""
visualize.py - Version améliorée
Génère une carte interactive avec :
- Choroplèthe par pays (échelle rouge)
- Marqueurs par ville/point (taille et couleur selon la densité, échelle bleu-rouge)
- Meilleure intégration avec Plotly Express
- Gestion des projections et styles avancés
"""

import os
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from geopy.geocoders import Nominatim
from collections import defaultdict

# Configuration
DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
GEO_CSV = os.path.join(DATA_DIR, "geo_enriched.csv")
AGG_CSV = os.path.join(DATA_DIR, "agg_by_country.csv")
OUTPUT_HTML = os.path.join(os.path.dirname(__file__), "..", "map.html")  # À la racine

def prepare_data():
    """Charge et enrichit les données"""
    df_geo = pd.read_csv(GEO_CSV)
    df_agg = pd.read_csv(AGG_CSV)
    
    # Calcul de la densité par ville
    city_counts = df_geo.groupby(['city', 'latitude', 'longitude']).size().reset_index(name='count')
    df_geo = df_geo.merge(city_counts, on=['city', 'latitude', 'longitude'])
    
    # Normalisation pour les couleurs (0-1)
    df_geo['color_intensity'] = (df_geo['count'] - df_geo['count'].min()) / \
                               (df_geo['count'].max() - df_geo['count'].min())
    
    return df_geo, df_agg

def create_map(df_geo, df_agg):
    """Crée la carte interactive avec Plotly"""
    # 1. Carte choroplèthe (pays)
    fig = px.choropleth(
        df_agg,
        locations="country_code",
        color="count",
        hover_name="country",
        color_continuous_scale="Reds",
        range_color=(0, df_agg['count'].max()),
        labels={'count': 'Nombre d\'IP'},
        projection="natural earth"
    )
    
    # 2. Marqueurs (villes)
    fig.add_trace(go.Scattergeo(
        lon=df_geo["longitude"],
        lat=df_geo["latitude"],
        text=df_geo.apply(
            lambda r: f"""
            <b>Ville:</b> {r.city}<br>
            <b>IPs:</b> {r.count}<br>
            <b>Pays:</b> {r.country}<br>
            <b>Org:</b> {r.get('org', 'N/A')[:30]}...
            """, axis=1
        ),
        mode="markers",
        marker=dict(
            size=df_geo['count']*0.5 + 1,
            color=df_geo['color_intensity'],
            colorscale=[[0, 'blue'], [0.5, 'yellow'], [1, 'red']],
            cmin=0,
            cmax=1,
            opacity=0.7,
            line=dict(width=0.5, color='black')
        ),
        name="Points d'IP",
        hoverinfo="text"
    ))
    
    # 3. Style final
    fig.update_layout(
        title_text="<b>Carte mondiale des IP malveillantes</b>",
        title_font=dict(size=24),
        geo=dict(
            showframe=True,
            showcoastlines=True,
            coastlinecolor="lightgray",
            landcolor="white",
            countrycolor="lightgray",
            projection_type="natural earth",
            bgcolor="#f0f0f0"
        ),
        coloraxis_colorbar=dict(title="IPs par pays"),
        hoverlabel=dict(bgcolor="white", font_size=12)
    )
    
    # Ajout d'une légende pour les marqueurs
    fig.update_layout(
        annotations=[dict(
            x=0.02,
            y=0.02,
            xref="paper",
            yref="paper",
            text="<b>Échelle marqueurs:</b><br>🔵 Peu d'IP<br>🟡 Moyen<br>🔴 Beaucoup d'IP",
            showarrow=False,
            bgcolor="white",
            bordercolor="black"
        )]
    )
    
    return fig

def main():
    print("[+] Préparation des données...")
    df_geo, df_agg = prepare_data()
    
    print("[+] Génération de la carte...")
    fig = create_map(df_geo, df_agg)
    
    print("[+] Export HTML...")
    fig.write_html(
        OUTPUT_HTML,
        include_plotlyjs="cdn",  # Plus léger
        full_html=True,
        config={"responsive": True}
    )
    
    print(f"[+] Carte générée : file://{os.path.abspath(OUTPUT_HTML)}")

if __name__ == "__main__":
    main()