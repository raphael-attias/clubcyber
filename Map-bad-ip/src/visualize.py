#!/usr/bin/env python3
"""
visualize.py
Génère une carte interactive (map.html) avec :
- une choroplèthe colorant les pays selon le nombre d'IP malveillantes
- des marqueurs pour chaque IP (popup IP, ville, pays)
Utilise Plotly (compatible >= 6).

Script secondaire / usage local — non appelé par la CI.
"""

import os
import pandas as pd
import plotly.graph_objects as go

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
GEO_CSV = os.path.join(DATA_DIR, "geo_enriched.csv")
AGG_CSV = os.path.join(DATA_DIR, "agg_by_country.csv")
OUTPUT_HTML = os.path.join(DATA_DIR, "map.html")


def main():
    df_agg = pd.read_csv(AGG_CSV)
    df_geo = pd.read_csv(GEO_CSV)

    fig = go.Figure()

    # Choroplèthe par pays (les noms de pays complets fonctionnent avec
    # locationmode="country names" ; les codes ISO-2 ne sont pas supportés).
    name_col = "country" if "country" in df_agg.columns else df_agg.columns[0]
    fig.add_trace(
        go.Choropleth(
            locations=df_agg[name_col],
            locationmode="country names",
            z=df_agg["count"],
            text=df_agg[name_col],
            marker_line_color="black",
            marker_line_width=0.5,
            colorbar_title="Nb IP",
        )
    )

    # Marqueurs par IP
    def _popup(row):
        parts = [f"IP: {row.get('ip', '?')}"]
        if row.get("city"):
            parts.append(f"Ville: {row['city']}")
        if row.get("country"):
            parts.append(f"Pays: {row['country']}")
        return "<br>".join(parts)

    fig.add_trace(
        go.Scattergeo(
            lon=df_geo["longitude"],
            lat=df_geo["latitude"],
            text=df_geo.apply(_popup, axis=1),
            mode="markers",
            marker=dict(size=6, opacity=0.7),
            name="IPs",
        )
    )

    fig.update_layout(
        title_text="Carte des IP malveillantes",
        geo=dict(showframe=False, showcoastlines=True, projection_type="equirectangular"),
    )

    os.makedirs(DATA_DIR, exist_ok=True)
    fig.write_html(OUTPUT_HTML)
    print(f"[+] Carte générée : {OUTPUT_HTML}")


if __name__ == "__main__":
    main()
