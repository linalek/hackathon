import geopandas as gpd
import json
import os
import pandas as pd
from shapely.geometry import mapping 

CHEMIN_GPKG = "data/communes.gpkg" 

def enrichir_communes_et_sauvegarder(chemin_json_communes, chemin_gpkg, layer_name='commune'):
    """
    Lit le JSON des communes, l'enrichit avec code postal, lat/lon du centroïde 
    à partir du GeoPackage, puis réécrit le fichier JSON.
    """
    if not os.path.exists(chemin_json_communes):
        print(f"Fichier JSON non trouvé : {chemin_json_communes}")
        return

    # 1. Chargement des données JSON existantes
    with open(chemin_json_communes, 'r', encoding='utf-8') as f:
        data_communes = json.load(f)
        
    print(f"Chargement de la couche '{layer_name}' depuis le GeoPackage...")
    
    # 2. Charger la couche géographique des communes
    try:
        gdf = gpd.read_file(chemin_gpkg, layer=layer_name)
    except Exception as e:
        print(f"Erreur lors du chargement du GPKG : {e}")
        return
    
    if gdf.crs and gdf.crs.to_epsg() != 4326:
        print(f"Reprojection de {gdf.crs.to_epsg()} vers WGS84 (EPSG:4326)...")
        gdf = gdf.to_crs(epsg=4326)
    else:
        print("Géométrie déjà en WGS84 ou CRS indéfini (vérifiez si la carte reste vide).")

    # 3. Préparation et calcul des données géographiques
    code_col_gpkg = 'code_insee' # Basé sur votre description (image_09cb05.png)

    # Assurer le format de la clé (ex: '01001')
    gdf[code_col_gpkg] = gdf[code_col_gpkg].astype(str).str.zfill(5)
    
    # Calculer le centroïde pour obtenir les coordonnées lat/lon
    gdf['lon'] = gdf.geometry.centroid.x
    gdf['lat'] = gdf.geometry.centroid.y
    
    # Colonnes à extraire : Code Postal, Longitude, Latitude
    gdf_enrichissement = gdf.set_index(code_col_gpkg)[['code_postal', 'lon', 'lat']].copy()
    dict_enrichissement = gdf_enrichissement.to_dict('index')

    # 4. Fusionner avec le dictionnaire de données et mettre à jour
    count_enriched = 0
    for code_insee, data in data_communes.items():
        if code_insee in dict_enrichissement:
            data.update(dict_enrichissement[code_insee])
            count_enriched += 1
        else:
            data.update({
                'code_postal': None,
                'lon': None,
                'lat': None
            })
        
    # 5. Réécriture du fichier JSON
    with open(chemin_json_communes, 'w', encoding='utf-8') as f:
        json.dump(data_communes, f, indent=4, ensure_ascii=False)
        
    print(f"Fichier JSON des communes mis à jour : {chemin_json_communes} ({count_enriched} entrées enrichies).")
    
# --- Fonction pour les Départements (Polygones GeoJSON) ---

def enrichir_departements_et_sauvegarder(chemin_json_deps, chemin_gpkg, layer_name='departement'):
    """
    Lit le JSON des départements, l'enrichit avec la géométrie GeoJSON 
    à partir du GeoPackage, puis réécrit le fichier JSON.
    """
    if not os.path.exists(chemin_json_deps):
        print(f"Fichier JSON non trouvé : {chemin_json_deps}")
        return

    with open(chemin_json_deps, 'r', encoding='utf-8') as f:
        data_deps = json.load(f)

    print(f"Chargement de la couche '{layer_name}' depuis le GeoPackage...")

    try:
        gdf = gpd.read_file(chemin_gpkg, layer=layer_name)
    except Exception as e:
        print(f"Erreur lors du chargement du GPKG : {e}")
        return

    if gdf.crs and gdf.crs.to_epsg() != 4326:
        print(f"Reprojection de {gdf.crs.to_epsg()} vers WGS84 (EPSG:4326)...")
        gdf = gdf.to_crs(epsg=4326)
    else:
        print("Géométrie déjà en WGS84 ou CRS indéfini (vérifiez si la carte reste vide).")

    # Préparation
    code_col_gpkg = 'code_insee' # Clé de jointure pour les départements
    if code_col_gpkg not in gdf.columns:
        print(f"Colonne de jointure '{code_col_gpkg}' introuvable. Abandon de l'enrichissement.")
        return
    
    gdf[code_col_gpkg] = gdf[code_col_gpkg].astype(str).str.zfill(2)

    # Convertir la géométrie en format GeoJSON/dict
    gdf['geojson_geometry'] = (
        gdf.geometry
        .simplify(500, preserve_topology=True) # <-- Simplification ajoutée
        .apply(mapping)
    )   
    gdf_enrichissement = gdf.set_index(code_col_gpkg)[['geojson_geometry']].copy()
    gdf_enrichissement = gdf.drop(columns=["geojson_geometry"])

    dict_enrichissement = gdf_enrichissement.to_dict('index')

    # Fusionner et mettre à jour
    count_enriched = 0
    for code_dep, data in data_deps.items():
        if code_dep in dict_enrichissement:
            data.update(dict_enrichissement[code_dep])
            count_enriched += 1


    # Réécriture du fichier JSON
    with open(chemin_json_deps, 'w', encoding='utf-8') as f:
        json.dump(data_deps, f, indent=4, ensure_ascii=False)

    print(f"Fichier JSON des départements mis à jour : {chemin_json_deps} ({count_enriched} entrées enrichies).")

CHEMIN_JSON_COMMUNES = "data/communes.json"
CHEMIN_JSON_DEPARTEMENTS = "data/departements.json"

enrichir_communes_et_sauvegarder(CHEMIN_JSON_COMMUNES, CHEMIN_GPKG)
#enrichir_departements_et_sauvegarder(CHEMIN_JSON_DEPARTEMENTS, CHEMIN_GPKG)