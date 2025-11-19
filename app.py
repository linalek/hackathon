# app.py

import streamlit as st
import pandas as pd
import geopandas as gpd
import numpy as np
import json
from src.data_loader import load_data
from src.utils import compute_socio_score, compute_access_score, compute_double_vulnerability, load_sante_variables, load_socio_variables
from src.variables import CHEMIN_COMMUNES, CHEMIN_DEPARTEMENTS, CHEMIN_GEOJSON
from src.visualizer import plot_map

# ===========================
# Configuration générale
# ===========================

st.set_page_config(
    page_title="Santé & Territoires - Double vulnérabilité",
    layout="wide"
)


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

    # Chargement des dataframes
    df_communes, df_departements = load_data(CHEMIN_COMMUNES, CHEMIN_DEPARTEMENTS, CHEMIN_GEOJSON)

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

    selected_dep = None

    if scope_mode == "Département":
        st.sidebar.subheader("Choix du département")

        dep_options = []
        if df_departements is not None and not df_departements.empty:
            # Obtient les codes triés (ex: '01', '02', '03'...)
            df_departements = df_departements.sort_values("code_insee")
            
            # Construit la liste d'options au format "Code - Nom"
            dep_options = df_departements.apply(
                lambda row: f"{row['code_insee']} - {row['nom_departement']}",
                axis=1
            ).tolist()

        selected_dep = st.sidebar.selectbox(
            "Département",
            options=dep_options,
            key="selected_dep"
        )

    df_view = pd.DataFrame() 

    # 3) Filtrage des données en fonction du périmètre
    code_dep_selected = None
    if selected_dep and " - " in selected_dep:
        code_dep_selected = selected_dep.split(" - ", 1)[0]
    elif selected_dep and len(selected_dep) <= 2 and selected_dep.isdigit():
        code_dep_selected = selected_dep

    if scope_mode == "France":
        if df_departements is not None and not df_departements.empty:
            df_view = df_departements.copy()
            df_view = df_view.reset_index(drop=True)

    elif scope_mode == "Département" and code_dep_selected:    
        if df_communes is not None and not df_communes.empty:
            mask = df_communes["code_insee"].astype(str).str.startswith(code_dep_selected)
            df_view = df_communes.loc[mask].copy()
            df_view = df_view.reset_index(drop=True)


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
        # valeur de départ : par exemple taux de pauvreté
        st.session_state.socio_criteria = ["Taux de pauvreté"]

    # Liste des critères encore disponibles à ajouter
    available_criteria = [
        label for label in load_socio_variables().keys()
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
        add_clicked = st.button("Ajouter", width='stretch')

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
    df_socio = compute_socio_score(df_view, selected_vars, weights)

    # Mini-cartes par variable
    if selected_vars:
        st.subheader("Cartes des variables sélectionnées")

        cols = st.columns(2)
        for i, var in enumerate(selected_vars):
            with cols[i % 2]:
                plot_map(
                    title=var,
                    col_name=load_socio_variables()[var],
                    data=df_view,
                    scope_mode=scope_mode,
                    type_data="socio"
                )

    # Carte du score socio-éco
    st.subheader("Carte du score de vulnérabilité socio-économique")
    plot_map(
        title="Score socio-économique agrégé",
        col_name="score_socio",
        data=df_socio,
        scope_mode=scope_mode,
        type_data="socio"
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
            options=list(load_sante_variables().keys()),
            index=0,
        )
        access_col = load_sante_variables()[prof_label]

    # Calcul du score d'accès
    df_access = compute_access_score(df_socio, access_col)

    with col_access_right:
        st.markdown("#### Carte de l’indicateur d’accès aux soins")
        plot_map(
            title=f"Accès aux soins – {prof_label}",
            col_name=access_col,
            data=df_access,
            scope_mode=scope_mode,
            type_data="sante"
        )


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

    # Carte finale
    st.subheader("Carte des zones à double vulnérabilité")
    plot_map(
        title="Score de double vulnérabilité",
        col_name="score_acces",
        data=df_final,
        scope_mode=scope_mode,
        type_data="socio"
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
        if scope_mode == "Département":
            cols_to_show = [c for c in ["nom_commune", "population_totale", "score_socio", "score_acces", "score_double"] if c in df_final.columns]
        else: 
            cols_to_show = [c for c in ["nom_departement", "population_totale", "score_socio", "score_acces", "score_double"] if c in df_final.columns]

        st.dataframe(
            df_final[cols_to_show].sort_values("score_double", ascending=False),
            width='stretch',
        )
    else:
        st.info("Les données finales ne sont pas encore disponibles.")


# ===========================
# Entrée principale
# ===========================

if __name__ == "__main__":
    main()
