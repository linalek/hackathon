import numpy as np
from src.variables import COLOR_RANGE
import pandas as pd
import json
import os
import streamlit as st

# ===========================
# Fonctions utilitaires
# ===========================

@st.cache_data
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

@st.cache_data
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

@st.cache_data
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

@st.cache_data
def load_dico_communes():
    """ Retourne le dictionnaire des variables pour les communes sous le même forme que le json"""
    
    fichier_communes = "data/variable_communes.json"
    if os.path.exists(fichier_communes):
        with open(fichier_communes, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    return {}

@st.cache_data
def load_dico_departements():
    """ Retourne le dictionnaire des variables pour les départements sous le même forme que le json"""
    
    fichier_departements = "data/variable_departements.json"
    if os.path.exists(fichier_departements):
        with open(fichier_departements, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    return {}

def compute_socio_score(df, selected_vars, weights, scope_mode):
    """
    Calcule le score de vulnérabilité socio-économique V en [0,100].

    df : GeoDataFrame
    selected_vars : liste de labels "humains" (clés de load_socio_variables())
    weights : dict {label_humain: poids_float}
    scope_mode : "France" ou "Departement" (ou ce que tu utilises)
    """
    print("🔄 Calcul du score socio-économique avec les variables :", selected_vars)
    if not selected_vars:
        df["score_socio"] = np.nan
        return df

    tmp = df.copy()

    # score sera une série; on initialise à 0
    score = pd.Series(0.0, index=tmp.index)

    # somme des poids pour normaliser
    total_weight = sum(weights[v] for v in selected_vars if v in weights)
    if total_weight <= 0:
        tmp["score_socio"] = np.nan
        return tmp

    # dico des variables socio : {nom_humain: nom_colonne}
    socio_vars = load_socio_variables()

    # données de référence pour min/max/order
    if scope_mode == "France":
        all_vars = load_dico_departements()
    else:
        all_vars = load_dico_communes()

    for var_label in selected_vars:
        # sécurité poids + variable connue
        if var_label not in weights or var_label not in socio_vars:
            continue

        col_name = socio_vars[var_label]
        if col_name not in tmp.columns:
            continue

        col_data = tmp[col_name].astype(float)

        # --- récupérer data_info pour cette variable ---
        data_info = find_variable_info(all_vars, col_name, "socio")

        # min / max : d’abord dans data_info, sinon on calcule dans le df
        if data_info is not None and "min" in data_info and "max" in data_info:
            col_min = data_info["min"]
            col_max = data_info["max"]
        else:
            col_min = col_data.min()
            col_max = col_data.max()

        # pas de variation → n'apporte rien
        if pd.isna(col_min) or pd.isna(col_max) or col_max == col_min:
            norm = pd.Series(0.0, index=tmp.index)
        else:
            norm = (col_data - col_min) / (col_max - col_min)

        # --- ordre : True = haut = plus vulnérable ; False = bas = plus vulnérable ---
        order_normal = True
        if data_info is not None and "order" in data_info:
            order_normal = data_info["order"]

        if not order_normal:
            norm = 1 - norm

        # poids normalisé
        w = weights[var_label] / total_weight

        score = score + w * norm

    # score final sur 0–100
    tmp["score_socio"] = (score * 100).round(2)
    return tmp

def compute_access_score(df, access_col, scope_mode):
    """
    Calcule le score de difficulté d'accès aux soins
    à partir d'une colonne APL (plus APL est haut, meilleur est l'accès).
    On renverse pour obtenir une "difficulté".
    """
    print(f"🔄 Calcul du score d'accès aux soins à partir de la colonne {access_col}")
    tmp = df.copy()

    if access_col not in tmp.columns:
        tmp["score_acces"] = np.nan
        return tmp

    apl = tmp[access_col].astype(float)

    if scope_mode == "France":
        all_vars = load_dico_departements()
    else:
        all_vars = load_dico_communes()

    data_info = find_variable_info(all_vars, access_col, "sante")
    if data_info is not None and "min" in data_info and "max" in data_info:
        apl_min = data_info["min"]
        apl_max = data_info["max"]
    else:
        apl_min = apl.min()
        apl_max = apl.max()

    if pd.isna(apl_min) or pd.isna(apl_max) or apl_max == apl_min:
        norm_apl = pd.Series(0.0, index=tmp.index)
    else:
        norm_apl = (apl - apl_min) / (apl_max - apl_min)
    difficulte = 1 - norm_apl

    tmp["score_acces"] = (difficulte * 100).round(2)  # 100 = difficulté max
    return tmp

def compute_double_vulnerability(df, alpha=0.5):
    """
    Combine les scores socio (V) et accès (D_access) en un score DV.
    DV = alpha * V + (1 - alpha) * score_acces
    """
    print(f"🔄 Calcul du score de double vulnérabilité avec alpha={alpha}")
    tmp = df.copy()
    if "score_socio" not in tmp.columns or "score_acces" not in tmp.columns:
        tmp["score_double"] = np.nan
        return tmp

    tmp["score_double"] = alpha * tmp["score_socio"] + (1 - alpha) * tmp["score_acces"]
    return tmp

def get_color_scale(value, col_name, type_data, scope_mode, color_range=COLOR_RANGE, df_scores=None):
    """
    Retourne une couleur RGBA pour une valeur.

    - Pour les variables "simples" : on utilise p5/p95 ou min/max
      issus de data_info (load_dico_* + find_variable_info).
    - Pour les colonnes de SCORE (col_name.startswith("score")) :
      on utilise les percentiles p5/p95 calculés directement sur
      la colonne de scores (df_scores[col_name]), pour éviter que
      l'échelle de couleur aille jusqu'à 0 ou 100 si personne n'y est.

    type_data :
        - "socio" → taux : faible = vert, élevé = rouge (order=True)
        - "sante" → APL : élevé = vert, faible = rouge (order=False)
    """
    # -----------------------------
    # 1) Cas des variables non "score"
    # -----------------------------
    if not col_name.startswith("score"):

        if scope_mode == "France":
            all_vars = load_dico_departements()
        else:
            all_vars = load_dico_communes()

        data_info = find_variable_info(all_vars, col_name, type_data)

        # sécurité
        if data_info is None:
            return [128, 128, 128, 100]

        # ordre (haut = vulnérable ?)
        if "order" in data_info:
            order_normal = data_info["order"]
        else:
            order_normal = True

        # on privilégie p5/p95 si dispo
        p5 = data_info["p5"]
        p95 = data_info["p95"]

        if p5 is not None and p95 is not None and p95 > p5:
            min_val = p5
            max_val = p95
        else:
            min_val = data_info["min"]
            max_val = data_info["max"]  

    # -----------------------------
    # 2) Cas des colonnes de SCORE
    # -----------------------------
    else:
        order_normal = True  # un score plus haut = plus vulnérable

        # si on a les données des scores -> percentiles empiriques
        if df_scores is not None and col_name in df_scores.columns:
            col_scores = df_scores[col_name].astype(float)
            col_scores_valid = col_scores.dropna()

            if not col_scores_valid.empty:
                p5 = np.percentile(col_scores_valid, 5)
                p95 = np.percentile(col_scores_valid, 95)

                if p95 > p5:
                    min_val = p5
                    max_val = p95
                else:
                    min_val = float(col_scores_valid.min())
                    max_val = float(col_scores_valid.max())
            else:
                # fallback si toutes les valeurs sont NaN
                min_val = 0.0
                max_val = 100.0
        else:
            # fallback si on n'a pas passé df_scores
            min_val = 0.0
            max_val = 100.0

    # -----------------------------
    # 3) Valeur manquante ou plage nulle
    # -----------------------------
    if pd.isna(value) or max_val == min_val:
        return [128, 128, 128, 100]   # gris

    # -----------------------------
    # 4) Clipping + normalisation
    # -----------------------------
    if value < min_val:
        value_clipped = min_val
    elif value > max_val:
        value_clipped = max_val
    else:
        value_clipped = value

    normalized = (value_clipped - min_val) / (max_val - min_val)

    # inversion si besoin
    if not order_normal:
        normalized = 1 - normalized

    # -----------------------------
    # 5) Index palette + couleur
    # -----------------------------
    index = int(normalized * (len(color_range) - 1))
    r, g, b = color_range[index]
    return [r, g, b, 180]


@st.cache_data
def find_variable_info(all_vars, col_name, type_data):
    for key, info in all_vars.items():
        if info["nom_col"] == col_name and info["type"] == type_data:
            return info
    return None