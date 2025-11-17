## Document pour le chargement des données brutes, le traitement et la fusion des différents datasets.vi

## prendre en feuille 3 (2023), en csv faire des médianes (plus intéréssants que moyenne ?) par départements des APL en EPT

import streamlit as st
import pandas as pd
import geopandas as gpd

@st.cache_data
def load_data():
    """
    TODO : charger ici les données agrégées au niveau départemental.

    Idéalement :
      - un GeoDataFrame avec une ligne par département
      - colonnes :
          - code_dep, nom_dep, population
          - colonnes socio-éco (tx_pauvrete, fdep, etc.)
          - colonnes accès aux soins (apl_medecins, apl_infirmiers, etc.)
          - géométrie (polygones des départements)
    """
    # Exemple structure (à remplacer par ton vrai chargement) :
    # gdf = gpd.read_file("data/departements_indices.parquet")
    # return gdf

    # Squelette : dataframe vide pour éviter de crasher si quelqu’un lance tel quel
    gdf = gpd.GeoDataFrame(
        {
            "code_dep": [],
            "nom_dep": [],
            # "geometry": []  # quand tu auras tes géométries
        }
    )
    return gdf
