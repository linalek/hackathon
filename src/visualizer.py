import streamlit as st
import pydeck as pdk
import pandas as pd
import numpy as np
import json
import geopandas as gpd
from shapely.geometry import shape
from src.utils import get_color_scale

def plot_map(title, col_name, data, scope_mode):
    """
    Affiche une carte PyDeck pour visualiser une variable selon le périmètre (France/Département).
    
    Args:
        title (str): Le titre de la carte (ex: "Taux de pauvreté").
        col_name (str): Le nom de la colonne de la variable (ex: "tx_pauvrete").
        data (pd.DataFrame): Le DataFrame filtré (départements ou communes).
        scope_mode (str): "France" (départements) ou "Département" (communes).
    """
    st.subheader(f"Carte : {title}")
    
    if data is None or data.empty or col_name not in data.columns:
        st.info(f"Aucune donnée disponible pour {title} ou la colonne '{col_name}' est manquante.")
        return

    # Nettoyage et préparation de la variable cible
    data_plot = data.copy()
    data_plot[col_name] = pd.to_numeric(data_plot[col_name], errors='coerce')
    
    # Calcul des min/max pour l'échelle de couleur 
    min_val = data_plot[col_name].min(skipna=True)
    max_val = data_plot[col_name].max(skipna=True)

    # Détermination de l'état initial de la vue
    # Centre de la France par défaut (ou centre des données si disponible)
    initial_view_state = pdk.ViewState(
        latitude=46.6,
        longitude=2.2,
        zoom=4,
        pitch=0,
    )
    
    # ----------------------------------------------------------------
    # CAS 1: MODE FRANCE
    # ----------------------------------------------------------------
    if scope_mode == "France":
        if "geometry" not in data_plot.columns:
            st.error("La colonne 'geometry' est absente du DataFrame pour le mode France.")
            return

        # S'assurer que c'est bien un GeoDataFrame
        if not isinstance(data_plot, gpd.GeoDataFrame):
            data_plot = gpd.GeoDataFrame(data_plot, geometry="geometry", crs="EPSG:4326")

        # S'assurer qu'on est bien en WGS84 (lat/lon)
        if data_plot.crs is None or data_plot.crs.to_epsg() != 4326:
            data_plot = data_plot.to_crs(epsg=4326)

        # Virer les géométries vides
        data_plot = data_plot.dropna(subset=["geometry"]).copy()

        # Simplifier les polygones pour alléger l'affichage
        data_plot["geometry"] = data_plot["geometry"].simplify(tolerance=0.02, preserve_topology=True)

        # Colonne code département (pour tooltip)
        if "DEP" not in data_plot.columns:
            if "code_insee" in data_plot.columns:
                data_plot["DEP"] = data_plot["code_insee"].astype(str).str.zfill(2)
            else:
                data_plot["DEP"] = ""

        def _color_or_default(x):
            if pd.isna(x):
                # gris clair si pas de valeur
                return [220, 220, 220, 60]
            return get_color_scale(x, min_val, max_val)
        
        data_plot['fill_color'] = data_plot[col_name].apply(_color_or_default)

        geojson_dict = json.loads(data_plot.to_json())
        
        layer = pdk.Layer(
            "GeoJsonLayer",
            data=geojson_dict,
            pickable=True,
            stroked=True,
            filled=True,
            get_fill_color="properties.fill_color",
            get_line_color=[100, 100, 100],
            line_width_min_pixels=0.5,
        )


    
    # ----------------------------------------------------------------
    # CAS 2: MODE DÉPARTEMENT (CARTE À POINTS DES COMMUNES)
    # ----------------------------------------------------------------
    elif scope_mode == "Département":

        if 'lon' not in data_plot.columns or 'lat' not in data_plot.columns:
            st.error("Les colonnes 'lon' et 'lat' sont manquantes. Assurez-vous d'avoir enrichi les données des communes.")
            return

        # Nettoyage des coordonnées (éviter les NaNs)
        data_plot = data_plot.dropna(subset=['lon', 'lat']).copy()
        
        # Application de la fonction de couleur sur chaque point (pour la taille du point)
        data_plot['radius'] = data_plot[col_name].apply(
            lambda x: 100 + (x - min_val) / (max_val - min_val) * 1000 if not pd.isna(x) else 0 
        )
        data_plot['fill_color'] = data_plot[col_name].apply(
            lambda x: get_color_scale(x, min_val, max_val)
        )
        
        # Adapter la vue au centre du département sélectionné
        initial_view_state = pdk.ViewState(
            latitude=data_plot["lat"].mean() if not data_plot.empty else 46.6,
            longitude=data_plot["lon"].mean() if not data_plot.empty else 2.2,
            zoom=7.5, # Zoom plus serré pour un département
            pitch=0,
        )

        # La ScatterplotLayer utilise lat/lon pour la visualisation des points
        layer = pdk.Layer(
            "ScatterplotLayer",
            data=data_plot,
            get_position=['lon', 'lat'],
            get_fill_color="fill_color",
            get_radius='radius', # Utilise la taille calculée
            radius_min_pixels=2,
            radius_max_pixels=30,
            pickable=True,
        )

    # ----------------------------------------------------------------
    # AFFICHAGE PYDECK
    # ----------------------------------------------------------------
    
    # Ajout du Tooltip pour l'interaction
    tooltip_text = f"**{title}**\n\n{{{'CODGEO' if scope_mode == 'Département' else 'DEP' if scope_mode == 'France' else 'Code'}}}: {{{data.columns[0]}}}\n{title}: {{{col_name}}}"
    
    st.pydeck_chart(pdk.Deck(
        layers=[layer],
        initial_view_state=initial_view_state,
        tooltip={"html": tooltip_text, "style": {"color": "black"}},
    ))