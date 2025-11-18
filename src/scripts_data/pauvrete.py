import pandas as pd
import json
import os # Utile pour gérer les chemins et vérifier l'existence du dossier de sortie

## -----------------------------------------------------------
## Fonctions de Traitement et de Calcul (Retournent un dictionnaire)
## -----------------------------------------------------------

def calculer_taux_commune(chemin_taux_pauvrete, chemin_composition_communale):
    """
    Construit et retourne le dictionnaire des communes de France métropolitaine 
    avec le taux de pauvreté de leur bassin de vie, au format demandé.
    Clé : CODGEO | Valeur : {"tx_pauvrete": xxx}
    """
    # 1. Charger et préparer les données de taux de pauvreté (par BV2022)
    # Note: `header` doit être spécifié si les en-têtes ne sont pas à la ligne 0
    df_taux = pd.read_excel(
        chemin_taux_pauvrete,
        usecols=['Code', 'Taux de pauvreté 2021']
    ).rename(columns={
        'Code': 'BV2022',
        'Taux de pauvreté 2021': 'tx_pauvrete'
    })
    df_taux['BV2022'] = df_taux['BV2022'].astype(str).str.zfill(5)

    # 2. Charger, préparer et filtrer les données de composition communale (Métropole)
    df_composition = pd.read_excel(
        chemin_composition_communale,
        usecols=['CODGEO', 'BV2022', 'DEP']
    )

    df_composition['CODGEO'] = df_composition['CODGEO'].astype(str).str.zfill(5)
    df_composition['BV2022'] = df_composition['BV2022'].astype(str).str.zfill(5)
    df_composition['DEP'] = df_composition['DEP'].astype(str).str.zfill(2)
    
    # Filtrage France Métropolitaine (DEP <= '95')
    df_composition = df_composition[df_composition['DEP'].le('95')].drop(columns=['DEP'])
    
    # 3. Joindre les deux DataFrames
    df_resultat = pd.merge(
        df_composition,
        df_taux,
        on='BV2022',
        how='left'
    )
    
    # 4. Construction du dictionnaire final avec gestion des types/erreurs
    df_resultat['tx_pauvrete'] = df_resultat['tx_pauvrete'].where(pd.notnull(df_resultat['tx_pauvrete']), None)
    resultat_simple_dict = df_resultat.set_index('CODGEO')['tx_pauvrete'].to_dict()
    
    cv_final = {}
    for code, tx in resultat_simple_dict.items():
        float_tx = None
        if tx is not None:
            try:
                float_tx = float(tx)
            except ValueError:
                float_tx = None
        
        cv_final[code] = {"tx_pauvrete": float_tx}
        
    return cv_final

# ---

def calculer_taux_departement(chemin_excel):
    """
    Charge le fichier Excel de taux de pauvreté par département et retourne le dictionnaire.
    Clé : DEP | Valeur : {"tx_pauvrete": xxx}
    """
    df = pd.read_excel(
        chemin_excel,
        usecols=['Code', 'Libellé', 'Taux de pauvreté 2021']
    ).rename(columns={
        'Code': 'DEP',
        'Libellé': 'nom_dep',
        'Taux de pauvreté 2021': 'tx_pauvrete'
    })

    df['DEP'] = df['DEP'].astype(str).str.zfill(2)
    df = df[df['DEP'].le('95')] # Filtre Métropole pour uniformité
    
    df['tx_pauvrete'] = df['tx_pauvrete'].where(pd.notnull(df['tx_pauvrete']), None)
    
    cv_final = {}
    
    for index, row in df.iterrows():
        float_tx = None
        if row['tx_pauvrete'] is not None:
            try:
                float_tx = float(row['tx_pauvrete'])
            except ValueError:
                float_tx = None
                
        cv_final[row['DEP']] = {
            "tx_pauvrete": float_tx,
            "nom_departement": row['nom_dep']
        }
    return cv_final


## -----------------------------------------------------------
## Fonction d'Exportation Unique
## -----------------------------------------------------------

def exporter_en_json(data_dict, chemin_fichier_json):
    """
    Exporte un dictionnaire Python en un fichier JSON formaté.
    """
    # Créer le dossier si non existant
    output_dir = os.path.dirname(chemin_fichier_json)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    with open(chemin_fichier_json, 'w', encoding='utf-8') as f:
        json.dump(data_dict, f, indent=4, ensure_ascii=False)

    print(f"✅ Export réussi ! Le fichier JSON '{chemin_fichier_json}' a été créé.")


## -----------------------------------------------------------
## Exécution et Appel Uniformisé
## -----------------------------------------------------------

if __name__ == '__main__':
    # Définition des chemins de fichiers (pour une meilleure lisibilité)
    PATH_TAUX_BV = "data/tx_pauvrete/taux_pauvrete.xlsx"
    PATH_COMPOSITION = "data/tx_pauvrete/BV2022.xlsx"
    PATH_TAUX_DEP = "data/tx_pauvrete/taux_pauvrete_dep.xlsx"
    
    OUTPUT_COMMUNES = "data/tx_pauvrete/tx_pauvrete_communes.json"
    OUTPUT_DEPARTEMENTS = "data/tx_pauvrete/tx_pauvrete_departements.json"
    
    print("--- Démarrage du Traitement ---")
    
    # 1. Traitement des données par Commune (à partir des bassins de vie)
    try:
        data_communes = calculer_taux_commune(PATH_TAUX_BV, PATH_COMPOSITION)
        print(len(data_communes), "communes traitées.")
        exporter_en_json(data_communes, OUTPUT_COMMUNES)
    except Exception as e:
        print(f"❌ Erreur lors du traitement des communes : {e}")

    # 2. Traitement des données par Département (à partir du fichier direct)
    try:
        data_departements = calculer_taux_departement(PATH_TAUX_DEP)
        print(len(data_departements), "départements traités.")
        exporter_en_json(data_departements, OUTPUT_DEPARTEMENTS)
    except Exception as e:
        print(f"❌ Erreur lors du traitement des départements : {e}")