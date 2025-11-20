import streamlit as st
import pydeck as pdk
import pandas as pd
import json
import geopandas as gpd
from src.utils import *
from src.variables import COLOR_RANGE

def plot_map(title, col_name, data, scope_mode, type_data, df_scores=None, change_var=None):
    """
    Affiche une carte PyDeck pour visualiser une variable selon le périmètre (France/Département).
    
    Args:
        title (str): Le titre de la carte (ex: "Taux de pauvreté").
        col_name (str): Le nom de la colonne de la variable (ex: "tx_pauvrete").
        data (pd.DataFrame): Le DataFrame filtré (départements ou communes).
        scope_mode (str): "France" (départements) ou "Département" (communes).
        type_data (str): Le type de donnée ("socio" ou "sante").
        df_scores (pd.DataFrame, optional): DataFrame des scores pour les variables de score
    """
    deck = build_map_deck(title, col_name, data, scope_mode, type_data, df_scores, change_var)
    if deck:
        if df_scores is None:
            st.pydeck_chart(deck, height=300, width='stretch')
        else:
            st.pydeck_chart(deck, width='stretch')

        # RÉCUP DES STATS POUR LA LÉGENDE
        if col_name.startswith("score"):
            # scores → on prend les quantiles calculés sur df_scores
            stats = get_score_stats(df_scores, col_name) if df_scores is not None else None
        else :
            # autres variables → on prend les stats sur data
            stats = get_variable_stats(col_name, type_data, scope_mode)
           
        if stats is not None:
            # AFFICHAGE DE LA LÉGENDE
            legend_colors = COLOR_RANGE[::-1]     # haut=rouge, bas=vert

            # valeurs affichées dans la légende
            if stats["order_normal"]:
                legend_values = ["> " + str(stats["p95"]), stats["q3"], stats["q2"], stats["q1"], "< " + str(stats["p5"])]
            else:
                # inverser l'ordre pour que la valeur haute soit en bas
                legend_values = ["< " + str(stats["p5"]), stats["q1"], stats["q2"], stats["q3"], "> " + str(stats["p95"])]
        
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
                    max-width:120px;
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
                                for c in legend_colors
                            ])}
                        </div>

                        <!-- VALEURS -->
                        <div style="
                            display:flex;
                            flex-direction:column;
                            justify-content:space-between;
                            height:220px;
                            font-size:0.85rem;
                        ">
                            <div>{legend_values[0]}</div>
                            <div>{legend_values[1]}</div>
                            <div>{legend_values[2]}</div>
                            <div>{legend_values[3]}</div>
                            <div>{legend_values[4]}</div>
                        </div>
                    </div>

                    <!-- Unité -->
                    <div style="
                        margin-top:6px;
                        font-size:0.65rem;
                        opacity:0.8;
                        white-space:normal;
                        word-wrap:break-word;
                        margin-left:auto;
                        margin-right:auto;
                    ">
                        {stats["unit"]}
                    </div>

                </div>
                """

            
            st.html(legend_html)

@st.cache_data
def build_map_deck(title, col_name, _data, scope_mode, type_data, _df_scores=None, change_var=None):
    print(f"🔄 Construction de la carte pour {title} en mode {scope_mode}")
    data = _data.copy()
    df_scores = _df_scores.copy() if _df_scores is not None else None

    st.markdown(f"##### {title}")
    
    if data is None or data.empty or col_name not in data.columns:
        st.info(f"Aucune donnée disponible pour {title} ou la colonne '{col_name}' est manquante.")
        return False

    # Nettoyage et préparation de la variable cible
    data_plot = data.copy()
    data_plot[col_name] = pd.to_numeric(data_plot[col_name], errors='coerce')
    

    # Détermination de l'état initial de la vue
    # Centre de la France par défaut (ou centre des données si disponible)
    initial_view_state = pdk.ViewState(
        latitude=46.6,
        longitude=-1 if df_scores is None else 2.2,
        zoom=3.5 if df_scores is None else 4,
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
            return get_color_scale(x, col_name, type_data, scope_mode, df_scores=df_scores)
        
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
            lambda x: get_color_scale(x, col_name, type_data, scope_mode, df_scores=df_scores)
        )
        
        # Adapter la vue au centre du département sélectionné
        initial_view_state = pdk.ViewState(
            latitude=data_plot["lat"].mean() if not data_plot.empty else 46.6,
            longitude=data_plot["lon"].mean() - 0.1 if not data_plot.empty else 2.1 if df_scores is None else 2.2,
            zoom=6.8 if df_scores is None else 7.5,
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
    if scope_mode == "Département":
        tooltip_text = f"{{{data.columns[1]}}} : {{{col_name}}}"
    else:
        tooltip_text = f"{{{data.columns[8]}}} ({{{data.columns[1]}}}) : {{{col_name}}}"
    
    return pdk.Deck(
        map_style="light",
        layers=[layer],
        initial_view_state=initial_view_state,
        tooltip={"html": tooltip_text, "style": {"color": "white"}},
    )
