import json
import os
import glob

# Définition des chemins
DATA_DIR = "data"
OUTPUT_DIR = "data"

def fusionner_communes_json():
    """
    Fusionne tous les fichiers JSON se terminant par 'communes.json' 
    dans le dossier data et ses sous-dossiers.
    La clé est le code INSEE de la commune.
    """
    
    # Dictionnaire principal pour stocker toutes les données fusionnées
    communes_fusionnees = {}
    communes_exclues = 0
    
    # Rechercher tous les fichiers se terminant par 'communes.json'
    pattern = os.path.join(DATA_DIR, '**', '*communes.json')
    tous_fichiers = glob.glob(pattern, recursive=True)
    
    # Exclure variable_communes.json
    fichiers_communes = [f for f in tous_fichiers if not f.endswith('variable_communes.json')]
    
    print(f"Fichiers communes trouvés : {len(fichiers_communes)}")
    
    # Parcourir chaque fichier JSON
    for fichier in fichiers_communes:
        print(f"  -> Traitement de : {fichier}")
        
        try:
            with open(fichier, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Fusionner les données
            for code_insee, donnees_commune in data.items():
                # Exclure les communes d'outre-mer (code commençant par 97)
                if code_insee.startswith('97'):
                    communes_exclues += 1
                    continue
                
                if code_insee not in communes_fusionnees:
                    # Créer une nouvelle entrée pour cette commune
                    communes_fusionnees[code_insee] = donnees_commune
                else:
                    # Fusionner avec les données existantes
                    communes_fusionnees[code_insee].update(donnees_commune)
            
            print(f"     ✓ {len(data)} communes traitées")
            
        except Exception as e:
            print(f"     ✗ ERREUR lors du traitement de {fichier}: {e}")
            continue
    
    if communes_exclues > 0:
        print(f"\n{communes_exclues} commune(s) d'outre-mer exclue(s)")
    
    # Trier les communes par ordre croissant de code INSEE
    communes_triees = dict(sorted(communes_fusionnees.items()))
    
    # Sauvegarder le fichier fusionné
    fichier_output = os.path.join(OUTPUT_DIR, 'communes.json')
    with open(fichier_output, 'w', encoding='utf-8') as f:
        json.dump(communes_triees, f, ensure_ascii=False, indent=4)
    
    print("\n" + "=" * 60)
    print(f"Fichier communes fusionné créé : {fichier_output}")
    print(f"   Nombre total de communes : {len(communes_triees)}")
    
    return communes_fusionnees


def fusionner_departements_json():
    """
    Fusionne tous les fichiers JSON se terminant par 'departements.json' 
    dans le dossier data et ses sous-dossiers.
    La clé est le code du département.
    """
    
    # Dictionnaire principal pour stocker toutes les données fusionnées
    departements_fusionnes = {}
    departements_exclus = 0
    
    # Rechercher tous les fichiers se terminant par 'departements.json'
    pattern = os.path.join(DATA_DIR, '**', '*departements.json')
    tous_fichiers = glob.glob(pattern, recursive=True)
    
    # Exclure variable_departements.json
    fichiers_departements = [f for f in tous_fichiers if not f.endswith('variable_departements.json')]
    
    print(f"Fichiers départements trouvés : {len(fichiers_departements)}")
    
    # Parcourir chaque fichier JSON
    for fichier in fichiers_departements:
        print(f"  -> Traitement de : {fichier}")
        
        try:
            with open(fichier, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Fusionner les données (en excluant l'outre-mer)
            for code_dept, donnees_dept in data.items():
                # Exclure les départements d'outre-mer (commençant par 97)
                if code_dept.startswith('97'):
                    departements_exclus += 1
                    continue
                
                if code_dept not in departements_fusionnes:
                    # Créer une nouvelle entrée pour ce département
                    departements_fusionnes[code_dept] = donnees_dept
                else:
                    # Fusionner avec les données existantes
                    departements_fusionnes[code_dept].update(donnees_dept)
            
            print(f"     ✓ {len(data)} départements traités")
            
        except Exception as e:
            print(f"     ✗ ERREUR lors du traitement de {fichier}: {e}")
            continue
    
    if departements_exclus > 0:
        print(f"\n{departements_exclus} département(s) d'outre-mer exclu(s)")
    
    # Sauvegarder le fichier fusionné
    fichier_output = os.path.join(OUTPUT_DIR, 'departements.json')
    with open(fichier_output, 'w', encoding='utf-8') as f:
        json.dump(departements_fusionnes, f, ensure_ascii=False, indent=4)
    
    print(f"\nFichier départements fusionné créé : {fichier_output}")
    print(f"   Nombre total de départements : {len(departements_fusionnes)}")
    
    return departements_fusionnes


if __name__ == "__main__":
    print("=" * 60)
    print("FUSION DES FICHIERS JSON - COMMUNES")
    print("=" * 60)
    fusionner_communes_json()
    
    print("\n" + "=" * 60)
    print("FUSION DES FICHIERS JSON - DÉPARTEMENTS")
    print("=" * 60)
    fusionner_departements_json()
    
    print("\nFusion terminée avec succès !")
