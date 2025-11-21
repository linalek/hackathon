# app.py

import streamlit as st
import pandas as pd
import geopandas as gpd
import numpy as np
import json
from src.data_loader import load_data
from src.utils import compute_socio_score, compute_access_score, compute_double_vulnerability, load_sante_variables, load_socio_variables
from src.variables import CHEMIN_COMMUNES, CHEMIN_DEPARTEMENTS, CHEMIN_GEOJSON, COLUMN_MAPPING
from src.visualizer import plot_map

# ===========================
# Configuration générale
# ===========================

st.set_page_config(
    page_title="VULNERIS",
    layout="wide"
)


def main():
    print("\n✴️  Rerun de la page")
    # -----------------------
    # Titre & explication
    # -----------------------
    st.title("VULNERIS : Votre présence fait la différence 🩺")
    st.subheader("Professionnel de santé ? Député ? Représentant local ? Entreprise de la santé ? ONG ? Identifiez les zones où votre installation de santé serait la plus utile.")
    st.markdown(
        """
        Cette application interactive vous permet de mettre en évidence les zones de **double vulnérabilité** caractérisées par :
        * une **vulnérabilité socio-économique élevée**,
        * une **difficulté d’accès aux soins** liée à une offre insuffisante.
        """
    )

    st.markdown(
        """
        ► &nbsp; Vous hésitez encore sur la zone où vous installer ? Explorez d’abord les résultats à l’**échelle nationale** pour identifier les départements les plus prioritaires.

        ► &nbsp; Vous avez déjà un département en tête ? Accédez directement au **détail des communes** pour affiner votre analyse.
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
    st.sidebar.header("Périmètre des données :")

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
        Choisissez les **indicateurs socio-économiques** que vous souhaitez inclure,
        définissez leur **pondération**, puis observez l’impact sur la carte du score.
        """
    )

    # --- gestion de l'état des critères sélectionnés ---
    if "socio_criteria" not in st.session_state:
        st.session_state.socio_criteria = []

    if "crit_to_add_select" not in st.session_state:
        st.session_state.crit_to_add_select = "— Sélectionner —"

    def add_criterion_callback():
        crit = st.session_state.crit_to_add_select
        if crit != "— Sélectionner —":
            st.session_state.socio_criteria.append(crit)
        # Reset du selecteur
        st.session_state.crit_to_add_select = "— Sélectionner —"


    # Liste des critères encore disponibles à ajouter
    available_criteria = [
        label for label in load_socio_variables().keys()
        if label not in st.session_state.socio_criteria
    ]

    add_col1, add_col2 = st.columns([3, 1])

    with add_col1:
        crit_to_add = st.selectbox(
            "Ajouter un critère :",
            options=["— Sélectionner —"] + available_criteria,
            label_visibility="collapsed",
            key="crit_to_add_select",
        )

    with add_col2:
        add_clicked = st.button("Ajouter", width='stretch', on_click=add_criterion_callback)

    if add_clicked and crit_to_add != "— Sélectionner —":
        st.session_state.socio_criteria.append(crit_to_add)


    # --- affichage des critères sélectionnés (1 ligne = label + slider + poubelle) ---
    selected_vars = list(st.session_state.socio_criteria)
    weights = {}

    if not selected_vars:
        st.info("Ajoutez au moins un critère pour calculer un score socio-économique.")
    else:

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
    df_socio = compute_socio_score(df_view, selected_vars, weights, scope_mode)

    # Mini-cartes par variable
    if selected_vars:
        st.subheader("Cartes des variables sélectionnées")

        cols = st.columns(3)
        for i, var in enumerate(selected_vars):
            with cols[i % 3]:
                plot_map(
                    title=var,
                    col_name=load_socio_variables()[var],
                    data=df_view,
                    scope_mode=scope_mode,
                    type_data="socio",
                    df_scores=None,
                    change_var=[code_dep_selected]
                )

    # Carte du score socio-éco
    plot_map(
        title="Votre score socio-économique : ",
        col_name="score_socio",
        data=df_socio,
        scope_mode=scope_mode,
        type_data="socio",
        df_scores=df_socio,
        change_var=[code_dep_selected, selected_vars, weights]
    )

    st.divider()

    # ===========================
    # 2) Accès aux soins
    # ===========================
    st.header("Accès aux soins")


    col_access_left, col_access_right = st.columns([1, 1])

    with col_access_left:
        st.markdown(
            """
            Indiquez votre profession de santé :
            """
        )
        prof_label = st.selectbox(
            "Profession utilisée pour le score d'accès aux soins :",
            options=list(load_sante_variables().keys()),
            label_visibility="collapsed",
            index=0,
            width=300
        )
        access_col = load_sante_variables()[prof_label]

        st.markdown("""
            L’**APL (Accessibilité Potentielle Localisée)** est un indicateur qui mesure la facilité pour les habitants d’accéder à un professionnel de santé, en tenant compte de l’offre disponible et du type de population.
            - **Médecins généralistes** : unité = **nombre de consultations accessibles par habitant et par an**.
            - **Autres professions de santé** : unité = **ETP pour 100 000 habitants** (un ETP correspond à un professionnel travaillant à temps plein — par exemple deux mi-temps = 1 ETP).
            """
        )


    # Calcul du score d'accès
    df_access = compute_access_score(df_socio, access_col, scope_mode)

    with col_access_right:
        plot_map(
            title=f"Accessibilité Potentielle Localisée – {prof_label}",
            col_name=access_col,
            data=df_access,
            scope_mode=scope_mode,
            type_data="sante",
            change_var=[code_dep_selected, access_col]
        )


    st.divider()

    # ===========================
    # 3) Zone à double vulnérabilité
    # ===========================
    st.header("Zones à double vulnérabilité")

    st.markdown(
        """
        Un score élevé indique une zone où les populations sont à la fois **socialement fragilisées** *et* **peu couvertes par l’offre de soins** — des territoires particulièrement **stratégiques** pour des actions de prévention, l’installation de nouveaux professionnels ou le renforcement des services existants.

        Cet outil vous aide à **identifier en un coup d’œil** où votre présence pourrait avoir **le plus d’impact** :
        """
    )

    # Calcul du score final
    df_final = compute_double_vulnerability(df_access, alpha)

    # Carte finale
    plot_map(
        title="Score de double vulnérabilité",
        col_name="score_double",
        data=df_final,
        scope_mode=scope_mode,
        type_data="socio",
        df_scores=df_final,
        change_var=[code_dep_selected, access_col, alpha, weights, selected_vars]
    )
    # Tableau de classement

    if scope_mode == "France":
        st.subheader("Classement des départements")
        st.markdown(
            """
            Découvrez les **10 départements les plus vulnérables**, selon leur score de double vulnérabilité : du **plus vulnérable** au **moins vulnérable**.  
            """
        )

    elif scope_mode == "Département":
        st.subheader("Classement des communes")
        st.markdown(
            """
            Découvrez les **10 communes les plus vulnérables** de ce département, classées du **score le plus élevé** (vulnérabilité forte) au **moins élevé**.  
            """
        )

    required_cols = ["score_double", "score_socio", "score_acces"]
    if all(col in df_final.columns for col in required_cols):
        all_scores_computed = all(
            df_final[col].notna().any() for col in required_cols
        )

        if all_scores_computed:
            if scope_mode == "Département":
                cols_to_show = [c for c in ["nom_commune", "code_postal", "score_double",  "score_socio", access_col, "population_totale"] if c in df_final.columns]
            else: 
                cols_to_show = [c for c in ["nom_departement", "code_insee", "score_double",  "score_socio", access_col, "population_totale"] if c in df_final.columns]

            # Créer une copie du DataFrame pour la modification
            df_display = df_final[cols_to_show].copy()
            
            #Renommer les colonnes dans le DataFrame d'affichage
            renaming_dict = {
                original_col: new_name 
                for original_col, new_name in COLUMN_MAPPING.items()
                if original_col in cols_to_show
            }
        
            df_display.rename(columns=renaming_dict, inplace=True)

            # Trier et Afficher (en utilisant le NOUVEAU nom de la colonne de tri)
            sort_column_name = COLUMN_MAPPING.get("score_double", "score_double") # Récupère le nouveau nom ou garde l'ancien par défaut
            df_display = df_display.sort_values(sort_column_name, ascending=False).reset_index(drop=True).head(20)
            df_display.index = df_display.index + 1
            st.dataframe(df_display)
        else:
            st.info("Les données finales ne sont pas encore disponibles.")
    else:
        st.info("Les données finales ne sont pas encore disponibles.")


# ===========================
# Entrée principale
# ===========================

if __name__ == "__main__":
    main()
