import pandas as pd
import json
import os

# --- Configuration des chemins ---
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))

# Chemins d'entrée
COMMUNES_JSON_PATH = os.path.join(BASE_DIR, 'data', 'communes.json')
FEDI_CSV_PATH = os.path.join(BASE_DIR, 'data', 'fedi', 'fedi.csv')

# Chemin de sortie ajouté
OUTPUT_JSON_PATH = os.path.join(BASE_DIR, 'data', 'fedi', 'fedi_departements.json')

def calculer_edi_departements(csv_path, json_path, output_path):
    """
    Calcule l'EDI moyen pondéré par la population pour chaque département
    et enregistre le résultat au format JSON dans data/fedi/fedi_departements.json.
    """
    print("--- Démarrage du processus de calcul de l'EDI Départemental ---")
    
    # 1. Chargement et préparation des données EDI (CSV)
    try:
        df_edi = pd.read_csv(csv_path, sep=r'[,;]\s*', engine='python', skipinitialspace=True)
        df_edi.columns = df_edi.columns.str.strip()
        df_edi = df_edi.rename(columns={'Commune Code': 'Code commune', 
                                        'Département': 'nom_departement'})
        
        df_edi['Code commune'] = df_edi['Code commune'].astype(str).str.zfill(5)
        df_edi['EDI'] = pd.to_numeric(df_edi['EDI'], errors='coerce')
        df_edi = df_edi.dropna(subset=['EDI']) 

    except FileNotFoundError:
        print(f"ERREUR: Le fichier CSV EDI est introuvable à {csv_path}")
        return
    except Exception as e:
        print(f"ERREUR lors du chargement ou de la préparation du CSV EDI: {e}")
        return


    # 2. Chargement et préparation des données de population (JSON)
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data_communes = json.load(f)
    except FileNotFoundError:
        print(f"ERREUR: Le fichier JSON de population est introuvable à {json_path}")
        return
    except Exception as e:
        print(f"ERREUR lors du chargement du JSON de population: {e}")
        return
    
    # Création du dictionnaire de recherche rapide {Code commune: population_totale}
    population_map = {
        k: v.get('population_totale')
        for k, v in data_communes.items() 
        if isinstance(v.get('population_totale'), (int, float))
    }

    # 3. Ajout de la population au DataFrame EDI et gestion des manquants
    df_edi['Population'] = df_edi['Code commune'].map(population_map)
    
    communes_manquantes = df_edi[df_edi['Population'].isna()]
    if not communes_manquantes.empty:
        print("-" * 60)
        print(f"INFO: {len(communes_manquantes)} communes n'ont pas de population trouvée et seront exclues du calcul (EDI pondéré) :")
        for index, row in communes_manquantes[['Code commune', 'Commune', 'nom_departement']].head(10).iterrows():
            print(f"  > Code: {row['Code commune']}, Commune: {row['Commune']}")
        if len(communes_manquantes) > 10:
             print("  ... (Affichage limité aux 10 premières)")
        print("-" * 60)
        
    df_calul = df_edi.dropna(subset=['Population']).copy()
    
    if df_calul.empty:
        print("ERREUR: Aucun couple EDI/Population valide n'est disponible pour le calcul.")
        return

    # 4. Calcul de l'EDI pondéré
    df_calul['EDI_Pondere'] = df_calul['EDI'] * df_calul['Population']

    resultats_agreges = df_calul.groupby(['departement_code', 'nom_departement']).agg(
        somme_edi_pondere=('EDI_Pondere', 'sum'),
        somme_population=('Population', 'sum')
    ).reset_index()

    # Calcul de l'EDI moyen pondéré (Formule : Somme(EDI * Pop) / Somme(Pop))
    resultats_agreges['EDI'] = round(
        resultats_agreges['somme_edi_pondere'] / resultats_agreges['somme_population'], 2
    )
    
    df_final = resultats_agreges[['departement_code', 'nom_departement', 'EDI']]

    # 5. Formatage de la sortie JSON
    output_dict = {}
    for index, row in df_final.iterrows():
        dept_code = str(row['departement_code'])
        output_dict[dept_code] = {
            "nom_departement": row['nom_departement'],
            "EDI": row['EDI']
        }
    
    # 6. Enregistrement du fichier JSON
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            # Enregistrement du JSON avec indentation et formatage pour les accents
            json.dump(output_dict, f, indent=4, ensure_ascii=False)
        print(f"\n✅ Résultat enregistré avec succès dans : {output_path}")

    except Exception as e:
        print(f"ERREUR lors de l'enregistrement du fichier JSON: {e}")
        
    # Affichage du début du résultat dans le terminal pour vérification rapide
    print("\n--- Aperçu du JSON généré ---")
    print(json.dumps(dict(list(output_dict.items())[:5]), indent=4, ensure_ascii=False))


if __name__ == "__main__":
    calculer_edi_departements(FEDI_CSV_PATH, COMMUNES_JSON_PATH, OUTPUT_JSON_PATH)