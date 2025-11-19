import numpy as np
from src.variables import COLOR_RANGE
import pandas as pd
import json
import os

# ===========================
# Fonctions utilitaires
# ===========================

def load_variables():
    """Retourne la liste des différentes variables issue des fichiers
    variable_communes.json et variable_departements.json
    sous forme de dictionnaire {nom_humain: nom_colonne}"""
    
    variables = {}
    
    # Charger variable_communes.json
    fichier_communes = "data/variable_communes.json"
    if os.path.exists(fichier_communes):
        with open(fichier_communes, 'r', encoding='utf-8') as f:
            data_communes = json.load(f)
            for nom_humain, infos in data_communes.items():
                if nom_humain not in variables:
                    variables[nom_humain] = infos.get("nom_col")
    
    # Charger variable_departements.json
    fichier_departements = "data/variable_departements.json"
    if os.path.exists(fichier_departements):
        with open(fichier_departements, 'r', encoding='utf-8') as f:
            data_departements = json.load(f)
            for nom_humain, infos in data_departements.items():
                if nom_humain not in variables:
                    variables[nom_humain] = infos.get("nom_col")
    
    print("\n ✅ Variables chargées depuis les fichiers :", fichier_communes, "et", fichier_departements)
    return variables


def load_socio_variables():
    """Retourne uniquement les variables socio-économiques issue des fichiers
    variable_communes.json et variable_departements.json
    sous forme de dictionnaire {nom_humain: nom_colonne}"""
    
    variables_socio = {}
    
    # Charger variable_communes.json
    fichier_communes = "data/variable_communes.json"
    if os.path.exists(fichier_communes):
        with open(fichier_communes, 'r', encoding='utf-8') as f:
            data_communes = json.load(f)
            for nom_humain, infos in data_communes.items():
                if infos.get("type") == "socio" and nom_humain not in variables_socio:
                    variables_socio[nom_humain] = infos.get("nom_col")
    
    # Charger variable_departements.json
    fichier_departements = "data/variable_departements.json"
    if os.path.exists(fichier_departements):
        with open(fichier_departements, 'r', encoding='utf-8') as f:
            data_departements = json.load(f)
            for nom_humain, infos in data_departements.items():
                if infos.get("type") == "socio" and nom_humain not in variables_socio:
                    variables_socio[nom_humain] = infos.get("nom_col")
    
    return variables_socio


def load_sante_variables():
    """Retourne uniquement les variables de santé issue des fichiers
    variable_communes.json et variable_departements.json
    sous forme de dictionnaire {nom_humain: nom_colonne}"""
    
    variables_sante = {}
    
    # Charger variable_communes.json
    fichier_communes = "data/variable_communes.json"
    if os.path.exists(fichier_communes):
        with open(fichier_communes, 'r', encoding='utf-8') as f:
            data_communes = json.load(f)
            for nom_humain, infos in data_communes.items():
                if infos.get("type") == "sante" and nom_humain not in variables_sante:
                    variables_sante[nom_humain] = infos.get("nom_col")
    
    # Charger variable_departements.json
    fichier_departements = "data/variable_departements.json"
    if os.path.exists(fichier_departements):
        with open(fichier_departements, 'r', encoding='utf-8') as f:
            data_departements = json.load(f)
            for nom_humain, infos in data_departements.items():
                if infos.get("type") == "sante" and nom_humain not in variables_sante:
                    variables_sante[nom_humain] = infos.get("nom_col")
    
    return variables_sante

def compute_socio_score(df, selected_vars, weights):
    """
    Calcule le score de vulnérabilité socio-économique V
    en fonction des variables sélectionnées et des poids choisis.

    df : GeoDataFrame des départements
    selected_vars : liste de noms "humains" (clés de SOCIO_VARIABLES)
    weights : dict {nom_humain: poids_float}
    """
    if not selected_vars:
        df["score_socio"] = np.nan
        return df

    # Normalisation simple min-max + combinaison pondérée
    tmp = df.copy()
    score = 0
    total_weight = sum(weights[v] for v in selected_vars)

    for var_label in selected_vars:
        col = load_socio_variables()[var_label]
        if col not in tmp.columns:
            continue

        col_data = tmp[col].astype(float)

        # min-max
        col_min = col_data.min()
        col_max = col_data.max()
        if col_max == col_min:
            norm = 0
        else:
            norm = (col_data - col_min) / (col_max - col_min)

        w = weights[var_label] / total_weight if total_weight > 0 else 0
        score = score + w * norm

    tmp["score_socio"] = score
    return tmp


def compute_access_score(df, access_col):
    """
    Calcule le score de difficulté d'accès aux soins
    à partir d'une colonne APL (plus APL est haut, meilleur est l'accès).
    On renverse pour obtenir une "difficulté".
    """
    tmp = df.copy()

    if access_col not in tmp.columns:
        tmp["score_acces"] = np.nan
        return tmp

    apl = tmp[access_col].astype(float)
    apl_min = apl.min()
    apl_max = apl.max()
    if apl_max == apl_min:
        norm_apl = 0
    else:
        norm_apl = (apl - apl_min) / (apl_max - apl_min)

    tmp["score_acces"] = 1 - norm_apl  # 1 = difficulté max
    return tmp


def compute_double_vulnerability(df, alpha=0.5):
    """
    Combine les scores socio (V) et accès (D_access) en un score DV.
    DV = alpha * V + (1 - alpha) * score_acces
    """
    tmp = df.copy()
    if "score_socio" not in tmp.columns or "score_acces" not in tmp.columns:
        tmp["score_double"] = np.nan
        return tmp

    tmp["score_double"] = alpha * tmp["score_socio"] + (1 - alpha) * tmp["score_acces"]
    return tmp


def get_color_scale(value, min_val, max_val, color_range=COLOR_RANGE):
    """Calcule la couleur basée sur la valeur dans la plage min/max."""
    if pd.isna(value) or max_val == min_val:
        return [128, 128, 128, 100] # Gris pour les données manquantes ou si le range est nul
    
    # Normalisation de la valeur entre 0 et 1
    normalized = (value - min_val) / (max_val - min_val)
    
    # Trouver l'index dans la plage de couleurs
    index = int(normalized * (len(color_range) - 1))
    
    # Simplement retourner la couleur à cet index
    return color_range[index]