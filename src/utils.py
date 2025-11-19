import numpy as np
from src.variables import SOCIO_VARIABLES, COLOR_RANGE
import pandas as pd

# ===========================
# Fonctions utilitaires
# ===========================

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
    # TODO : à adapter/raffiner selon ta méthode exacte
    tmp = df.copy()
    score = 0
    total_weight = sum(weights[v] for v in selected_vars)

    for var_label in selected_vars:
        col = SOCIO_VARIABLES[var_label]
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

    tmp["score_socio"] = score * 100
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


def get_color_scale(value, min_val, max_val, type_data, color_range=COLOR_RANGE):
    """
    Retourne une couleur RGBA en fonction d'une valeur normalisée entre min_val et max_val.
    
    type_data :
        - "socio" → taux : faible = vert, élevé = rouge
        - "sante" → APL : élevé = vert, faible = rouge
    """

    # 1) Cas particulier : valeur manquante ou range nul
    if pd.isna(value) or max_val == min_val:
        return [128, 128, 128, 100]   # gris

    # 2) Normalisation de 0 à 1
    normalized = (value - min_val) / (max_val - min_val)
    normalized = max(0, min(1, normalized))  # clamp pour éviter dépassements

    # 3) Inversion selon le type de données
    # socio : plus c'est haut → pire → vers le rouge → donc normal
    # sante : plus c'est haut → mieux → on inverse pour aller vers le vert
    if type_data == "sante":
        normalized = 1 - normalized

    # 4) Index dans la palette
    index = int(normalized * (len(color_range) - 1))

    # 5) Couleur RGB + alpha
    r, g, b = color_range[index]
    return [r, g, b, 180]   # alpha 180 pour visible sur carte
