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
    
    # Rechercher tous les fichiers se terminant par 'communes.json'
    pattern = os.path.join(DATA_DIR, '**', '*communes.json')
    fichiers_communes = glob.glob(pattern, recursive=True)
    
    print(f"Fichiers communes trouvés : {len(fichiers_communes)}")
    
    # Parcourir chaque fichier JSON
    for fichier in fichiers_communes:
        print(f"  -> Traitement de : {fichier}")
        
        try:
            with open(fichier, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Fusionner les données
            for code_insee, donnees_commune in data.items():
                if code_insee not in communes_fusionnees:
                    # Créer une nouvelle entrée pour cette commune
                    communes_fusionnees[code_insee] = donnees_commune
                else:
                    # Fusionner avec les données existantes
                    communes_fusionnees[code_insee].update(donnees_commune)
            
            print(f"     ✓ {len(data)} communes ajoutées/mises à jour")
            
        except Exception as e:
            print(f"     ✗ ERREUR lors du traitement de {fichier}: {e}")
            continue
    
    # # Compter les paramètres pour détecter les données manquantes
    # print("\nSTATISTIQUES DES PARAMÈTRES PAR COMMUNE :")
    # print("-" * 60)
    
    # # Collecter tous les paramètres uniques
    # tous_parametres = set()
    # for donnees in communes_fusionnees.values():
    #     tous_parametres.update(donnees.keys())
    
    # # Compter pour chaque paramètre
    # comptage_parametres = {}
    # for parametre in sorted(tous_parametres):
    #     count = sum(1 for commune in communes_fusionnees.values() 
    #                if parametre in commune and commune[parametre] is not None)
    #     comptage_parametres[parametre] = count
        
    #     # Calculer le pourcentage
    #     pourcentage = (count / len(communes_fusionnees)) * 100 if len(communes_fusionnees) > 0 else 0
        
    #     # Afficher avec indication visuelle
    #     if pourcentage == 100:
    #         statut = "✅"
    #     elif pourcentage >= 80:
    #         statut = "⚠️ "
    #     else:
    #         statut = "❌"
        
    #     print(f"{statut} {parametre:40s} : {count:5d} / {len(communes_fusionnees):5d} ({pourcentage:6.2f}%)")
    
    # Sauvegarder le fichier fusionné
    fichier_output = os.path.join(OUTPUT_DIR, 'communes.json')
    with open(fichier_output, 'w', encoding='utf-8') as f:
        json.dump(communes_fusionnees, f, ensure_ascii=False, indent=4)
    
    print("\n" + "=" * 60)
    print(f"Fichier communes fusionné créé : {fichier_output}")
    print(f"   Nombre total de communes : {len(communes_fusionnees)}")
    # print(f"   Nombre de paramètres uniques : {len(tous_parametres)}")
    
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
    fichiers_departements = glob.glob(pattern, recursive=True)
    
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
