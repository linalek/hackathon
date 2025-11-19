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

def load_dico_communes():
    """ Retourne le dictionnaire des variables pour les communes sous le même forme que le json"""
    
    fichier_communes = "data/variable_communes.json"
    if os.path.exists(fichier_communes):
        with open(fichier_communes, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    return {}


def load_dico_departements():
    """ Retourne le dictionnaire des variables pour les départements sous le même forme que le json"""
    
    fichier_departements = "data/variable_departements.json"
    if os.path.exists(fichier_departements):
        with open(fichier_departements, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    return {}

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

    tmp["score_socio"] = round(score * 100, 2)
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

    tmp["score_acces"] = round(100 - norm_apl * 100, 2)  # 100 = difficulté max
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


def get_color_scale(value, col_name, type_data, scope_mode, color_range=COLOR_RANGE):
    """
    Retourne une couleur RGBA pour une valeur.

    - L’échelle est globale : min/max (ou p5/p95) viennent de toutes les données.
    - Pour les variables non "score", on utilise p5/p95 pour éviter que les extrêmes
      écrasent la palette. Les valeurs < p5 prennent la couleur de p5,
      les valeurs > p95 prennent la couleur de p95.

    type_data :
        - "socio" → taux : faible = vert, élevé = rouge
        - "sante" → APL : élevé = vert, faible = rouge
    """
    if scope_mode == "France":
        all_vars = load_dico_departements()
    else:
        all_vars = load_dico_communes()

    data_info = find_variable_info(all_vars, col_name, type_data)

    # 1) Définition de la plage utilisée pour la couleur
    if col_name.startswith("score"):
        # scores déjà normalisés 0–100
        min_val = 0
        max_val = 100
    else:
        # on privilégie p5/p95 si disponibles et cohérents
        p5 = data_info["p5"]
        p95 = data_info["p95"]

        if p5 is not None and p95 is not None and p95 > p5:
            min_val = p5
            max_val = p95
        else:
            # fallback : min/max classiques
            min_val = data_info["min"]
            max_val = data_info["max"]

    # 2) Cas particulier : valeur manquante ou range nul
    if pd.isna(value) or max_val == min_val:
        return [128, 128, 128, 100]   # gris

    # 3) Clipping sur [min_val, max_val] pour saturer les extrêmes
    if value < min_val:
        value_clipped = min_val
    elif value > max_val:
        value_clipped = max_val
    else:
        value_clipped = value

    # 4) Normalisation de 0 à 1
    normalized = (value_clipped - min_val) / (max_val - min_val)

    # 5) Inversion selon le type de données
    if type_data == "sante":
        normalized = 1 - normalized

    # 6) Index dans la palette
    index = int(normalized * (len(color_range) - 1))

    # 7) Couleur RGB + alpha
    r, g, b = color_range[index]
    return [r, g, b, 180]


def find_variable_info(all_vars, col_name, type_data):
    for key, info in all_vars.items():
        if info["nom_col"] == col_name and info["type"] == type_data:
            return info
    return None