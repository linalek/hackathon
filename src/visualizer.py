import streamlit as st
import pydeck as pdk
import pandas as pd
import numpy as np
import geopandas as gpd
from shapely.geometry import shape
from src.utils import get_color_scale

def plot_map(title, subtitle, data, scope_mode):
    """
    Affiche une carte PyDeck pour visualiser une variable selon le périmètre (France/Département).
    
    Args:
        title (str): Le titre de la carte (ex: "Taux de pauvreté").
        subtitle (str): Le nom de la colonne de la variable (ex: "tx_pauvrete").
        data (pd.DataFrame): Le DataFrame filtré (départements ou communes).
        scope_mode (str): "France" (départements) ou "Département" (communes).
    """
    col_name = subtitle
    st.subheader(f"Carte : {title}")
    
    if data.empty or col_name not in data.columns:
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
        zoom=5,
        pitch=0,
    )
    
    # ----------------------------------------------------------------
    # CAS 1: MODE FRANCE
    # ----------------------------------------------------------------
    if scope_mode == "France":
        
        # Vérification des données de géométrie
        if 'geojson_geometry' not in data_plot.columns:
            st.error("La colonne 'geojson_geometry' est manquante. Assurez-vous d'avoir enrichi les données départementales.")
            return
        
         
        # Application de la fonction de couleur sur chaque ligne
        data_plot['fill_color'] = data_plot.apply(
            lambda row: get_color_scale(row[col_name], min_val, max_val), axis=1
        )

        # Conversion temporaire en GeoDataFrame à partir du JSON (plus fiable)
        try:
            # Re-créer la colonne 'geometry' de type Shapely
            geometry_series = data_plot['geojson_geometry'].apply(shape)
            
            # Créer le GeoDataFrame temporaire avec la colonne de couleur
            gdf_temp = gpd.GeoDataFrame(
                data_plot.drop(columns=['geojson_geometry']), 
                geometry=geometry_series, 
                crs=4326 # WGS84
            )
            
            # 3. Exporter au format GeoJSON (FeatureCollection)
            # La colonne 'fillColor' passe dans les propriétés de la Feature.
            data_geo_json = gdf_temp.to_json() 
            
        except Exception as e:
            st.error(f"Erreur lors de la conversion GeoJSON pour PyDeck : {e}")
            return
        
        # Le GeoJSONLayer utilise une colonne GeoJSON pour la visualisation des polygones
        layer = pdk.Layer(
            "GeoJsonLayer",
            # Passer la chaîne GeoJSON (FeatureCollection)
            data=data_geo_json, 
            opacity=0.8,
            stroked=True,
            filled=True,
            extruded=False,
            wireframe=True,
            # Accès à la propriété 'fillColor' qui est dans les Feature properties
            get_fill_color="properties.fillColor", 
            get_line_color=[0, 0, 0, 255],   
            get_line_width=10, # 10 mètres de large pour le trait
            pickable=True,
        )
        # Mettre à jour la vue pour la France entière
        
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
            lambda x: 100 + (x - min_val) / (max_val - min_val) * 800 if not pd.isna(x) else 0 
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