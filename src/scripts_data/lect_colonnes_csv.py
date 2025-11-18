import pandas as pd
import os

def obtenir_noms_colonnes(nom_csv, index_ligne, nom_dossier):
    """
    Récupère les noms des colonnes d'un CSV situé dans le dossier 'app/'.
    
    Args:
        nom_csv (str): Le nom du fichier (ex: 'data.csv')
        index_ligne (int): Le numéro de la ligne contenant les en-têtes (0 pour la 1ère ligne)
        
    Returns:
        list: La liste des noms de colonnes ou un message d'erreur.
    """
    
    # --- GESTION DES CHEMINS ---
    # Récupère le chemin du dossier où se trouve ce script (src/)
    dossier_actuel = os.path.dirname(os.path.abspath(__file__))
    
    # Remonte d'un cran vers la racine, puis descend dans 'app/'
    dossier_src = os.path.dirname(dossier_actuel)
    chemin_fichier = os.path.join(os.path.dirname(dossier_src), 'data', nom_dossier, nom_csv)

    print(f"Lecture du fichier : {chemin_fichier}")

    if not os.path.exists(chemin_fichier):
        return None, f"Erreur : Le fichier n'a pas été trouvé à l'emplacement : {chemin_fichier}"

    try:
        # --- LECTURE OPTIMISÉE ---
        # nrows=0 permet de lire uniquement l'en-tête sans charger les données en mémoire
        df = pd.read_csv(chemin_fichier, delimiter=";", header=index_ligne, nrows=0)
        return list(df.columns), None
        
    except Exception as e:
        return None, f"Erreur lors de la lecture du CSV : {str(e)}"

# --- EXÉCUTION DU SCRIPT ---
if __name__ == "__main__":
    print("-" * 40)
    print("   EXTRACTEUR DE COLONNES CSV")
    print("-" * 40)

    # 1. Demander le nom du fichier à l'utilisateur
    nom_fichier_input = input(">> Entrez le nom du fichier CSV (ex: data.csv) : ").strip()
    
    # 2. Demander le numéro de ligne
    ligne_input = input(">> Entrez le numéro de la ligne des en-têtes (0 pour la 1ère) : ").strip()

    # 3. Demander le nom du dossier
    nom_dossier_input = input(">> Entrez le nom du dossier contenant le fichier (ex: famille_monoparentale) : ").strip()
    # Conversion de l'entrée ligne en entier
    try:
        index_ligne = int(ligne_input)
    except ValueError:
        print("Erreur : Vous devez entrer un nombre entier pour la ligne.")
        exit(1)

    print("\nTraitement en cours...")
    colonnes, erreur = obtenir_noms_colonnes(nom_fichier_input, index_ligne, nom_dossier_input)

    if erreur:
        print(erreur)
    else:
        print(f"\nSuccès ! {len(colonnes)} colonnes trouvées à la ligne {index_ligne} :")
        print("-" * 30)
        for col in colonnes:
            print(f"• {col}")