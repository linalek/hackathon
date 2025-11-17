# app.py

import streamlit as st
import pandas as pd
import geopandas as gpd
import numpy as np
from src.data_loader import load_data

# ===========================
# Configuration générale
# ===========================

st.set_page_config(
    page_title="Santé & Territoires - Double vulnérabilité",
    layout="wide"
)

# ===========================
# Constantes / Métadonnées
# ===========================

# Exemple : mapping nom affiché -> nom de colonne dans ton dataframe départemental
SOCIO_VARIABLES = {
    "Taux de pauvreté": "tx_pauvrete",
    "Indice FDep": "fdep",
    "Part des familles monoparentales": "part_fam_mono",
    "Part des 75 ans et + vivant seuls": "part_75plus_seuls",
    "Taux de chômage des 15-24 ans": "tx_chomage_jeunes",
    # Ajouter ici d'autres variables si besoin
}

# Types de professions pour l'accès aux soins
ACCESS_PROFESSIONS = {
    "Médecins généralistes": "apl_medecins",
    "Infirmiers": "apl_infirmiers",
    "Dentistes": "apl_dentistes",
    "Sages-femmes": "apl_sagesfemmes",
    # etc.
}

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


def plot_map_placeholder(title, subtitle=None):
    """
    Squelette pour les cartes :
    Pour l’instant, juste un encadré texte. À remplacer par le code de carte
    (pydeck, folium, altair, st.map, etc.).
    """
    with st.container(border=True):
        st.markdown(f"### {title}")
        if subtitle:
            st.caption(subtitle)
        st.write("🗺️ TODO : afficher ici la carte (GeoDataFrame + valeur associée).")


# ===========================
# Layout principal
# ===========================

def main():
    # -----------------------
    # Titre & explication
    # -----------------------
    st.title("Diagnostic territorial : zones à double vulnérabilité")

    st.markdown(
        """
        Cette application permet d’identifier, à l’échelle des **départements**,
        les **zones à double vulnérabilité** :
        - vulnérabilité **socio-économique** élevée  
        - **difficulté d’accès aux soins** (offre de soins insuffisante)

        Vous pouvez :
        - choisir les **facteurs socio-économiques** pris en compte et leurs **poids**,
        - visualiser les **cartes intermédiaires**,
        - explorer la **carte finale** des zones prioritaires.
        """
    )

    st.divider()

    # Chargement des données
    df_dep = load_data()

    # ===========================
    # SIDEBAR : Paramètres globaux
    # ===========================

    st.sidebar.header("Paramètres globaux")

    # 1) Slider alpha
    alpha = st.sidebar.slider(
        "Poids de la vulnérabilité socio-économique par rapport à l'accès aux soins :",
        min_value=0.0,
        max_value=1.0,
        value=0.5,
        step=0.05,
        help="α = 1 → 100% socio-économique, α = 0 → 100% accès aux soins"
    )

    # 2) Choix du périmètre
    st.sidebar.subheader("Périmètre des données")

    # Initialisation d’état
    if "scope_mode" not in st.session_state:
        st.session_state.scope_mode = "France"

    scope_mode = st.sidebar.radio(
        "Sélectionnez le périmètre",
        ["France", "Département"],
    )

    st.session_state.scope_mode = scope_mode

    if scope_mode == "Département":
        st.sidebar.subheader("Choix du département")

        dep_options = (
            sorted(df_dep["nom_dep"].unique())
            if not df_dep.empty and "nom_dep" in df_dep.columns
            else []
        )

        selected_dep = st.sidebar.selectbox(
            "Département",
            options=dep_options,
            key="selected_dep"
        )

    # 3) Filtrage des données en fonction du périmètre
    if scope_mode == "Département" and selected_dep:
        df_view = df_dep[df_dep["nom_dep"] == selected_dep]
    else:
        df_view = df_dep



    # ===========================
    # 1) Vulnérabilité socio-économique
    # ===========================
    st.header("Vulnérabilité socio-économique")

    st.markdown(
        """
        Ajoutez des **critères socio-économiques** à prendre en compte dans le score,
        ajustez leur **poids** puis visualisez les cartes associées.
        """
    )

    # --- gestion de l'état des critères sélectionnés ---
    if "socio_criteria" not in st.session_state:
        # valeur de départ : par exemple taux de pauvreté et FDep
        st.session_state.socio_criteria = ["Taux de pauvreté", "Indice FDep"]

    # Liste des critères encore disponibles à ajouter
    available_criteria = [
        label for label in SOCIO_VARIABLES.keys()
        if label not in st.session_state.socio_criteria
    ]

    st.markdown("#### Ajouter un critère")

    add_col1, add_col2 = st.columns([3, 1])

    with add_col1:
        crit_to_add = st.selectbox(
            "Ajouter un critère :",
            options=["— Sélectionner —"] + available_criteria,
            label_visibility="collapsed",
            key="crit_to_add_select",
        )

    with add_col2:
        add_clicked = st.button("Ajouter", use_container_width=True)

    if add_clicked and crit_to_add != "— Sélectionner —":
        st.session_state.socio_criteria.append(crit_to_add)

    st.markdown("---")

    # --- affichage des critères sélectionnés (1 ligne = label + slider + poubelle) ---
    selected_vars = list(st.session_state.socio_criteria)
    weights = {}

    if not selected_vars:
        st.info("Ajoutez au moins un critère pour calculer un score socio-économique.")
    else:
        st.markdown("#### Critères utilisés et poids associés")

        # On stocke ici les critères à supprimer pour ne pas modifier la liste pendant la boucle
        to_remove = []

        for crit in selected_vars:
            col_label, col_slider, col_delete = st.columns([2, 6, 1])

            with col_label:
                st.markdown(f"**{crit}**")

            with col_slider:
                weights[crit] = st.slider(
                    "Poids",
                    min_value=0.0,
                    max_value=1.0,
                    value=0.3,
                    step=0.05,
                    key=f"weight_{crit}",
                    label_visibility="collapsed",
                )

            with col_delete:
                if st.button("🗑️", key=f"delete_{crit}"):
                    to_remove.append(crit)

        # Mise à jour après la boucle
        if to_remove:
            for crit in to_remove:
                if crit in st.session_state.socio_criteria:
                    st.session_state.socio_criteria.remove(crit)

        # Recalcule selected_vars et weights après éventuelle suppression
        selected_vars = list(st.session_state.socio_criteria)
        weights = {crit: weights.get(crit, 0.0) for crit in selected_vars}

    # Calcul du score socio-éco
    df_socio = compute_socio_score(df_dep, selected_vars, weights)

    # Mini-cartes par variable
    if selected_vars:
        st.subheader("Cartes des variables sélectionnées")

        # TODO : tu peux faire un layout en grille, par ex. 2 colonnes
        cols = st.columns(3)
        for i, var in enumerate(selected_vars):
            with cols[i % 2]:
                plot_map_placeholder(
                    title=var,
                    subtitle=f"Variable brute : {SOCIO_VARIABLES[var]}"
                )

    # Carte du score socio-éco
    st.subheader("Carte du score de vulnérabilité socio-économique")
    plot_map_placeholder(
        title="Score socio-économique agrégé",
        subtitle="Combinaison normalisée et pondérée des variables sélectionnées."
    )

    st.divider()

    # ===========================
    # 2) Accès aux soins
    # ===========================
    st.header("Accès aux soins")

    st.markdown(
        """
        Les scores d’accès aux soins sont calculés à partir des indicateurs d’**accessibilité potentielle localisée (APL)**.  
        Vous pouvez choisir la **profession de santé** considérée.
        """
    )

    col_access_left, col_access_right = st.columns([1, 2])

    with col_access_left:
        prof_label = st.selectbox(
            "Profession utilisée pour le score d'accès aux soins :",
            options=list(ACCESS_PROFESSIONS.keys()),
            index=0,
        )
        access_col = ACCESS_PROFESSIONS[prof_label]

    # Calcul du score d'accès
    df_access = compute_access_score(df_socio, access_col)

    with col_access_right:
        st.markdown("#### Carte de l’indicateur d’accès aux soins")
        plot_map_placeholder(
            title=f"Accès aux soins – {prof_label}",
            subtitle=f"Données APL : colonne {access_col}"
        )

    # Tu peux ajouter d'autres cartes pour d'autres professions en dessous si tu veux
    # Exemple : plot_map_placeholder("Accès aux soins – Infirmiers", "...")

    st.divider()

    # ===========================
    # 3) Zone à double vulnérabilité
    # ===========================
    st.header("Zones à double vulnérabilité")

    st.markdown(
        """
        Le score de **double vulnérabilité** combine :  
        - le score de **vulnérabilité socio-économique**,  
        - la **difficulté d’accès aux soins**.  

        Les territoires avec un score élevé peuvent être considérés comme **prioritaires**
        pour des actions de prévention ou l’installation de nouvelles offres de soins.
        """
    )

    # Calcul du score final
    df_final = compute_double_vulnerability(df_access, alpha=alpha)

    # TODO : ici tu peux définir une typologie (ex : quantiles) et créer une catégorie
    # df_final["classe_vulnerabilite"] = ...

    # Carte finale
    st.subheader("Carte des zones à double vulnérabilité")
    plot_map_placeholder(
        title="Score de double vulnérabilité",
        subtitle="Combinaison du score socio-économique et de la difficulté d’accès aux soins."
    )

    # Tableau de classement
    st.subheader("Classement des départements")
    st.markdown(
        """
        Classement des départements selon le score de double vulnérabilité
        (du plus vulnérable au moins vulnérable).
        """
    )

    if "score_double" in df_final.columns and not df_final.empty:
        cols_to_show = [c for c in ["code_dep", "nom_dep", "score_socio", "score_acces", "score_double"] if c in df_final.columns]
        st.dataframe(
            df_final[cols_to_show].sort_values("score_double", ascending=False),
            use_container_width=True,
        )
    else:
        st.info("Les données finales ne sont pas encore disponibles (squelette).")


# ===========================
# Entrée principale
# ===========================

if __name__ == "__main__":
    main()
