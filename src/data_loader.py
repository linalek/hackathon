import streamlit as st
import pandas as pd
import geopandas as gpd
import json
import os

@st.cache_data
def load_data(chemin_communes, chemin_departements):
    """
    Charge les données des fichiers JSON spécifiés et les retourne sous forme de dictionnaires.

    Args:
        chemin_communes (str): Chemin d'accès au fichier JSON des données par commune.
        chemin_departements (str): Chemin d'accès au fichier JSON des données par département.

    Returns:
        tuple: Un tuple contenant (data_communes, data_departements).
    """
    data_communes = None
    data_departements = None

    # Charger les données des communes
    try:
        if not os.path.exists(chemin_communes):
            raise FileNotFoundError(f"Fichier non trouvé : {chemin_communes}")
            
        with open(chemin_communes, 'r', encoding='utf-8') as f:
            data_communes = json.load(f)
            print(f"✅ Chargement réussi : {chemin_communes}")

    except Exception as e:
        print(f"❌ Erreur lors du chargement de {chemin_communes} : {e}")

    # Charger les données des départements
    try:
        if not os.path.exists(chemin_departements):
            raise FileNotFoundError(f"Fichier non trouvé : {chemin_departements}")
            
        with open(chemin_departements, 'r', encoding='utf-8') as f:
            data_departements = json.load(f)
            print(f"✅ Chargement réussi : {chemin_departements}")

    except Exception as e:
        print(f"❌ Erreur lors du chargement de {chemin_departements} : {e}")
        
    return data_communes, data_departements


@st.cache_data
def load_data_2():
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
