#!/usr/bin/env python3
"""
visualize.py - Version finale avec points fixes et frontières visibles
"""

import os
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Configuration
DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
GEO_CSV = os.path.join(DATA_DIR, "geo_enriched.csv")
AGG_CSV = os.path.join(DATA_DIR, "agg_by_country.csv")
OUTPUT_HTML = os.path.join(os.path.dirname(__file__), "..", "map.html")

def prepare_data():
    """Charge et prépare les données"""
    df_geo = pd.read_csv(GEO_CSV)
    df_agg = pd.read_csv(AGG_CSV)
    
    # Validation des coordonnées
    df_geo = df_geo.dropna(subset=['latitude', 'longitude'])
    df_geo = df_geo[(df_geo['latitude'].between(-90, 90)) & (df_geo['longitude'].between(-180, 180))]
    
    # Agrégation par ville
    city_data = df_geo.groupby(['city', 'country']).agg({
        'latitude': 'mean',
        'longitude': 'mean'
    }).reset_index()
    
    # Calcul du nombre d'IPs
    ip_counts = df_geo.groupby(['city', 'country']).size().reset_index(name='ip_count')
    city_data = city_data.merge(ip_counts, on=['city', 'country'])
    
    return city_data, df_agg

def create_map(city_data, df_agg):
    """Crée la carte avec points fixes et bonnes frontières"""
    min_ip = city_data['ip_count'].min()
    max_ip = city_data['ip_count'].max()
    mid_ip = (max_ip + min_ip) / 2

    # Fond de carte avec frontières visibles
    fig = px.choropleth(
        df_agg,
        locations="country_code",
        color="count",
        hover_name="country",
        color_continuous_scale="Greys",
        range_color=(0, df_agg['count'].max()),
        labels={'count': ''},
        projection="natural earth"
    )
    
    # Style des frontières
    fig.update_geos(
        showcountries=True,
        countrycolor="darkgray",
        countrywidth=0.5,
        coastlinecolor="darkgray",
        coastlinewidth=0.8,
        landcolor="white",
        showocean=True,
        oceancolor="#f0f8ff"
    )
    fig.update_layout(coloraxis_showscale=False)

    # Marqueurs avec taille fixe
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
                size=8,  # Taille fixe pour tous les points
                color=city_data['ip_count'],
                colorscale=[[0, 'blue'], [0.5, 'yellow'], [1, 'red']],
                cmin=min_ip,
                cmax=max_ip,
                opacity=0.85,
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

    # Mise en forme finale
    fig.update_layout(
        title_text="<b>Carte des IPs malveillantes</b>",
        title_font=dict(size=14, family="Arial"),
        geo=dict(
            showframe=True,
            framecolor="black",
            framewidth=0.5,
            bgcolor="#f8f8f8"
        ),
        hoverlabel=dict(
            bgcolor="white",
            font_size=11,
            font_family="Arial",
            bordercolor="gray"
        ),
        margin=dict(r=120, l=10, t=60, b=10),
        paper_bgcolor="white"
    )

    return fig

def main():
    print("[+] Chargement des données...")
    try:
        city_data, df_agg = prepare_data()
    except Exception as e:
        print(f"[ERREUR] Problème de chargement: {str(e)}")
        return

    print("[+] Création de la carte...")
    try:
        fig = create_map(city_data, df_agg)
    except Exception as e:
        print(f"[ERREUR] Création carte: {str(e)}")
        return
    
    print("[+] Génération HTML...")
    try:
        fig.write_html(
            OUTPUT_HTML,
            include_plotlyjs="cdn",
            full_html=True,
            config={"displayModeBar": True}
        )
        print(f"[+] Carte générée: file://{os.path.abspath(OUTPUT_HTML)}")
    except Exception as e:
        print(f"[ERREUR] Génération: {str(e)}")

if __name__ == "__main__":
    main()