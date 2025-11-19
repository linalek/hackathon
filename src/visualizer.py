import streamlit as st
import pydeck as pdk
import pandas as pd
import json
import geopandas as gpd
from src.utils import *
from src.variables import COLOR_RANGE

def plot_map(title, col_name, data, scope_mode, type_data):
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
    if scope_mode == "France":
        all_vars = load_dico_departements()
    else:
        all_vars = load_dico_communes()

    data_info = find_variable_info(all_vars, col_name, type_data)
    if col_name.startswith("score"):
        min_val = 0
        max_val = 100
    else:
        min_val = data_info["min"]
        max_val = data_info["max"]    


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
            return get_color_scale(x, col_name, type_data, scope_mode)
        
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
        
    
        data_plot['fill_color'] = data_plot[col_name].apply(
            lambda x: get_color_scale(x, col_name, type_data, scope_mode)
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
            get_radius=2000, # Taille fixe des points
            pickable=True,
        )

    # ----------------------------------------------------------------
    # AFFICHAGE PYDECK
    # ----------------------------------------------------------------
    
    # Ajout du Tooltip pour l'interaction
    if type_data == "socio":
        tooltip_text = f"{{{data.columns[1]}}} : {{{col_name}}} %"
    else:
        tooltip_text = f"{{{data.columns[1]}}} : {{{col_name}}}"
    
    st.pydeck_chart(pdk.Deck(
        map_style="light",
        layers=[layer],
        initial_view_state=initial_view_state,
        tooltip={"html": tooltip_text, "style": {"color": "white"}},
    ))

    if scope_mode == "France":
        all_vars = load_dico_departements()
    else:
        all_vars = load_dico_communes()

    data_info = find_variable_info(all_vars, col_name, type_data)
    if data_info is None:
        p95 = 100
        q2  = 50
        p5  = 0
    else:
        p95 = data_info["p95"]
        q2  = data_info["q2"] 
        p5  = data_info["p5"]  

    legend_html = f"""
        <div style="
            position:absolute;
            bottom:20px;
            left:15px;
            background:rgba(255,255,255,0.9);
            padding:8px 10px;
            border-radius:10px;
            box-shadow:0 2px 6px rgba(0,0,0,0.25);
            z-index:9999;
            font-family: sans-serif;
        ">

            <!-- Conteneur barre + labels -->
            <div style="display:flex; flex-direction:row; align-items:center;">

                <!-- BARRE VERTICALE -->
                <div style="
                    display:flex;
                    flex-direction:column;
                    height:220px;
                    width:16px;
                    border-radius:4px;
                    overflow:hidden;
                    margin-right:5px;
                ">
                    {''.join([
                        f'<div style="flex:1;background:rgb({c[0]}, {c[1]}, {c[2]});"></div>'
                        for c in COLOR_RANGE[::-1]
                    ])}
                </div>

                <!-- VALEURS -->
                <div style="display:flex; flex-direction:column; justify-content:space-between; height:220px; font-size:0.85rem;">
                    <div style="margin-top:-4px;">› {p95}</div>
                    <div style="margin-top:0px;">{q2}</div>
                    <div style="margin-bottom:-4px;">‹ {p5}</div>
                </div>
            </div>

            <!-- Unité -->
            <div style="margin-top:6px; text-align:center; font-size:0.75rem; opacity:0.8;">
                en %
            </div>

        </div>
        """

    
    st.html(legend_html)

