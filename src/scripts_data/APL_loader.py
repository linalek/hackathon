import pandas as pd
import json
import os

# Définition des chemins et des noms des fichiers
DATA_DIR = "data/APL"
OUTPUT_DIR = "data/APL/processed/"
METIERS = {
    'dentistes': 'APL_chirurgiens_dentistes.xlsx',
    'sagesfemmes': 'APL_sages_femmes.xlsx',
    'medecins': 'APL_medecins_generalistes.xlsx',
    'infirmiers': 'APL_infirmieres.xlsx',
    'kine': 'APL_kinesitherapeutes.xlsx',
}
# Index des colonnes de population pour chaque métier (population standardisée, population totale)
COLONNES_POPULATION = {
    'dentistes': (3, 4),  # colonnes 4 et 5 (index 3 et 4)
    'sagesfemmes': (3, 4),
    'medecins': (6, 7),  # colonnes 7 et 8 (index 6 et 7)
    'infirmiers': (3, 4),
    'kine': (3, 4),
}
SHEET_INDEX = 2 # Index de la feuille 3 contenant la donnée nécessaire


# Fonction pour créer le fichier JSON communes
def creer_json_communes_apl():
    """
    Lit les 5 fichiers Excel APL, extrait les données 2023 (se trouvant en page 3)
    et crée un dictionnaire JSON agrégé par commune.
    """
    
    # Dictionnaire principal où les données agrégées seront stockées
    # Clé: Code commune INSEE
    communes_data = {}
    
    # 1. Traitement de chaque fichier métier
    for cle_metier, nom_fichier in METIERS.items():
        chemin_fichier = os.path.join(DATA_DIR, nom_fichier)
        print(f"-> Traitement du fichier : {nom_fichier}")

        try:
            # Charger la page souhaitée
            # Les données ne commencent qu'à partir de la ligne 11 (index 10)
            df = pd.read_excel(chemin_fichier, sheet_name=SHEET_INDEX, header=9)
            
        except FileNotFoundError:
            print(f"ERREUR: Fichier non trouvé à {chemin_fichier}. Ignoré.")
            continue
        except ValueError:
             print(f"ERREUR: La feuille d'index {SHEET_INDEX} n'existe pas dans {nom_fichier}. Ignoré.")
             continue
        
        # 2. Identification des colonnes
        # On utilise les index numériques pour plus de robustesse car les titres varient.
        idx_pop_std, idx_pop_tot = COLONNES_POPULATION[cle_metier]
        
        if df.shape[1] < max(3, idx_pop_std + 1, idx_pop_tot + 1):
             print(f"ERREUR: Pas assez de colonnes dans {nom_fichier}. Attendu {max(3, idx_pop_std + 1, idx_pop_tot + 1)} minimum.")
             continue
        
        # Renommage temporaire des colonnes pour la manipulation
        df.columns.values[0] = 'Code_commune_INSEE'
        df.columns.values[1] = 'Nom_commune'
        
        # On prend le nom de la colonne APL qui varie selon le métier
        nom_col_apl = df.columns.values[2]
        nom_col_pop_std = df.columns.values[idx_pop_std]
        nom_col_pop_tot = df.columns.values[idx_pop_tot]
        
        # Sélection des colonnes nécessaires
        df = df[['Code_commune_INSEE', 'Nom_commune', nom_col_apl, nom_col_pop_std, nom_col_pop_tot]].copy()
        
        # Renommage des colonnes pour le stockage dans le JSON
        df.rename(columns={
            nom_col_apl: f'apl_{cle_metier}',
            nom_col_pop_std: 'population_standardisee',
            nom_col_pop_tot: 'population_totale'
        }, inplace=True)
        
        # 3. Remplissage du dictionnaire agrégé
        for index, row in df.iterrows():
            code_insee = str(row['Code_commune_INSEE'])
            
            # Utiliser la version du code INSEE sur 5 caractères
            code_insee = code_insee.zfill(5)
            
            # S'assurer que la clé est un code INSEE valide (accepter les codes Corse avec A/B)
            if len(code_insee) != 5:
                continue
            
            # Exclure les communes d'outre-mer (code commençant par 97)
            if code_insee.startswith('97'):
                continue
            
            # Initialisation de l'entrée pour la commune si elle n'existe pas
            if code_insee not in communes_data:
                # Récupérer les populations (communes à tous les fichiers)
                pop_std = row['population_standardisee']
                pop_tot = row['population_totale']
                
                communes_data[code_insee] = {
                    'nom_commune': row['Nom_commune'],
                    'population_standardisee': None if pd.isna(pop_std) else pop_std,
                    'population_totale': None if pd.isna(pop_tot) else pop_tot,
                }
            
            # Ajout de l'APL spécifique
            apl_valeur = row[f'apl_{cle_metier}']
            
            # Gestion des valeurs non numériques
            if pd.isna(apl_valeur):
                apl_valeur = None
            
            communes_data[code_insee][f'apl_{cle_metier}'] = apl_valeur
            
    # 4. Sauvegarde du fichier JSON des communes
    fichier_output_communes = os.path.join(OUTPUT_DIR, 'apl_communes.json')
    with open(fichier_output_communes, 'w', encoding='utf-8') as f:
        json.dump(communes_data, f, ensure_ascii=False, indent=4)
        
    print(f"\nFichier JSON des communes créé avec succès : {fichier_output_communes}")
    print(f"Nombre total de communes traitées : {len(communes_data)}")
    
    return communes_data

# Fonction pour créer le fichier JSON départements
def creer_json_departements_apl():
    """
    Crée un fichier JSON des départements avec les APL calculés par moyenne pondérée.
    La formule utilisée : APL_D = Σ(APL_i × P_i) / Σ(P_i)
    où P_i est la population standardisée de chaque commune i du département.
    """
    
    # 1. Charger les données des communes depuis le fichier JSON
    fichier_communes = os.path.join(OUTPUT_DIR, 'apl_communes.json')
    
    if not os.path.exists(fichier_communes):
        print(f"ERREUR: Le fichier {fichier_communes} n'existe pas.")
        print("Veuillez d'abord exécuter creer_json_communes_apl().")
        return None
    
    with open(fichier_communes, 'r', encoding='utf-8') as f:
        communes_data = json.load(f)
    
    print(f"-> Chargement de {len(communes_data)} communes depuis {fichier_communes}")
    
    # 2. Dictionnaire pour stocker les données départementales
    departements_data = {}
    
    # 3. Regrouper les communes par département
    for code_insee, donnees_commune in communes_data.items():
        # Extraire le code département (gestion spéciale pour la Corse)
        code_dept = code_insee[:2]
        
        if code_dept is None:
            continue
        
        # Exclure les départements d'outre-mer (code commençant par 97)
        if code_dept.startswith('97'):
            continue
        
        # Initialiser le département s'il n'existe pas encore
        if code_dept not in departements_data:
            departements_data[code_dept] = {
                'population_totale': 0,
                'population_standardisee': 0,
            }
            # Initialiser les sommes pour chaque métier
            for cle_metier in METIERS.keys():
                departements_data[code_dept][f'somme_apl_{cle_metier}_x_pop'] = 0
                departements_data[code_dept][f'somme_pop_{cle_metier}'] = 0


        # Récupérer la population standardisée de la commune
        pop_std = donnees_commune.get('population_standardisee')
        pop_tot = donnees_commune.get('population_totale')
        
        # Ajouter la population totale du département
        if pop_tot is not None and pop_tot != 0:
            departements_data[code_dept]['population_totale'] += pop_tot
        
        # Pour chaque métier, calculer les sommes nécessaires
        for cle_metier in METIERS.keys():
            apl_commune = donnees_commune.get(f'apl_{cle_metier}')
            
            # Si l'APL et la population sont valides
            if apl_commune is not None and pop_std is not None and pop_std != 0:
                departements_data[code_dept][f'somme_apl_{cle_metier}_x_pop'] += apl_commune * pop_std
                departements_data[code_dept][f'somme_pop_{cle_metier}'] += pop_std


    # 4. Calculer l'APL final pour chaque département et métier
    departements_final = {}
    
    for code_dept, donnees in departements_data.items():
        departements_final[code_dept] = {
            'population_totale': round(donnees['population_totale'], 0),
        }
        
        # Calculer l'APL pour chaque métier selon la formule
        for cle_metier in METIERS.keys():
            somme_apl_x_pop = donnees[f'somme_apl_{cle_metier}_x_pop']
            somme_pop = donnees[f'somme_pop_{cle_metier}']
            
            if somme_pop > 0:
                apl_dept = somme_apl_x_pop / somme_pop
                departements_final[code_dept][f'apl_{cle_metier}'] = round(apl_dept, 2)
            else:
                departements_final[code_dept][f'apl_{cle_metier}'] = None
    
    # 5. Sauvegarde du fichier JSON des départements
    fichier_output_departements = os.path.join(OUTPUT_DIR, 'apl_departements.json')
    with open(fichier_output_departements, 'w', encoding='utf-8') as f:
        json.dump(departements_final, f, ensure_ascii=False, indent=4)
    
    print(f"\nFichier JSON des départements créé avec succès : {fichier_output_departements}")
    print(f"Nombre total de départements traités : {len(departements_final)}")
    
    return departements_final

if __name__ == "__main__":
    # Créer le fichier JSON des communes
    creer_json_communes_apl()
    
    # Créer le fichier JSON des départements
    creer_json_departements_apl()