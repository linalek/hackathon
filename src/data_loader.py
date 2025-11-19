import streamlit as st
import pandas as pd
import geopandas as gpd
import json
import os

@st.cache_data
def load_data(chemin_communes, chemin_departements, chemin_geojson):
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

        rows = []
        for code_commune, attrs in data_communes.items():
            row = {"code_insee": code_commune}  
            row.update(attrs)              
            rows.append(row)

        data_communes = pd.DataFrame(rows)

    except Exception as e:
        print(f"❌ Erreur lors du chargement de {chemin_communes} : {e}")

    # Charger les données des départements
    try:
        if not os.path.exists(chemin_departements):
            raise FileNotFoundError(f"Fichier non trouvé : {chemin_departements}")
            
        with open(chemin_departements, 'r', encoding='utf-8') as f:
            data_departements = json.load(f)
            print(f"✅ Chargement réussi : {chemin_departements}")

        rows = []
        for code_dep, attrs in data_departements.items():
            row = {"code_insee": code_dep}  
            row.update(attrs)          
            rows.append(row)

        df_dep = pd.DataFrame(rows)
        print(f"✅ Conversion en DataFrame réussie pour les départements.")

        gdf = gpd.read_file(chemin_geojson)
        print(f"✅ Chargement réussi : {chemin_geojson}")
        
        # Harmoniser les types des codes
        gdf["code_insee"] = gdf["code_insee"].astype(str).str.zfill(2)
        df_dep["code_insee"] = df_dep["code_insee"].astype(str).str.zfill(2)

        gdf = gdf.to_crs(epsg=4326)

        data_departements = gdf.merge(df_dep, on="code_insee", how="left")
        colonnes_json = df_dep.columns.tolist()  # ['code_insee', 'population_totale', ...]
        colonnes_a_garder = ["geometry"] + colonnes_json
        data_departements = data_departements[colonnes_a_garder]

        print(f"✅ Jointure GeoDataFrame réussie pour les départements.")



    except Exception as e:
        print(f"❌ Erreur lors du chargement de {chemin_departements} : {e}")
        
    return data_communes, data_departements
