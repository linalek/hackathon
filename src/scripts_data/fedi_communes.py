import csv
import json
import os

def convertir_csv_json(nom_csv, index_ligne, info_cle, info_colonnes, delimiteur=','):
    """
    Convertit un CSV en JSON avec typage strict et gestion des erreurs par ligne.
    
    Args:
        nom_csv (str): Nom du fichier dans app/
        index_ligne (int): Numéro de la ligne des en-têtes (0-based)
        info_cle (tuple): ("NomColonneClé", "type") ex: ("id", "int")
        info_colonnes (list): Liste de tuples [("NomCol", "type"), ...]
        delimiteur (str): Séparateur du CSV (ex: ';')
    """
    
    # --- 1. MAPPING DES TYPES (String -> Fonction) ---
    types_disponibles = {
        'int': int,
        'float': float,
        'str': str,
        'bool': lambda x: str(x).lower() in ['true', '1', 'yes', 'vrai']
    }

    # --- 2. GESTION DES CHEMINS ---
    dossier_actuel = os.path.dirname(os.path.abspath(__file__))
    dossier_src = os.path.dirname(dossier_actuel)
    chemin_entree = os.path.join(os.path.dirname(dossier_src), 'data', 'fedi', nom_csv)
    
    nom_json = os.path.splitext(nom_csv)[0] + ".json"
    chemin_sortie = os.path.join(os.path.dirname(dossier_src), 'data', 'fedi', nom_json)

    if not os.path.exists(chemin_entree):
        print(f"Erreur FATALE : Fichier introuvable -> {chemin_entree}")
        return

    print(f"Lecture de : {nom_csv}...")
    
    # --- 3. TRAITEMENT ---
    donnees_json = {}
    lignes_ignorees = 0
    lignes_traitees = 0

    try:
        with open(chemin_entree, mode='r', encoding='utf-8-sig') as f:
            lecteur = csv.reader(f, delimiter=delimiteur)
            
            # Sauter les lignes avant l'en-tête
            for _ in range(index_ligne):
                next(lecteur, None)

            # Lire l'en-tête
            try:
                en_tetes = next(lecteur)
            except StopIteration:
                print("Erreur : Le fichier semble vide ou la ligne d'en-tête est inaccessible.")
                return

            # Vérifier que les colonnes demandées existent
            map_indices = {} # Nom -> Index
            
            # On récupère le nom CSV de la clé et des colonnes
            colonne_cle_csv = info_cle[0]
            liste_colonnes_csv = [col[0] for col in info_colonnes]
            
            toutes_colonnes_requises = [colonne_cle_csv] + liste_colonnes_csv
            
            for nom_col in toutes_colonnes_requises:
                if nom_col not in en_tetes:
                    print(f"Erreur : La colonne '{nom_col}' n'existe pas dans le CSV.")
                    print(f"Colonnes trouvées dans le fichier : {en_tetes}")
                    return
                map_indices[nom_col] = en_tetes.index(nom_col)

            # Parcourir les données
            for i, ligne in enumerate(lecteur, start=index_ligne + 1):
                if not ligne: continue # Sauter lignes vides
                
                try:
                    objet_temp = {}
                    
                    # A. Traitement de la CLÉ PRIMAIRE (Index du dictionnaire JSON)
                    nom_cle_csv, type_cle_str = info_cle
                    idx_cle = map_indices[nom_cle_csv]
                    if idx_cle >= len(ligne): raise IndexError(f"Clé '{nom_cle_csv}' manquante")
                    
                    valeur_brute_cle = ligne[idx_cle]
                    fonction_type_cle = types_disponibles.get(type_cle_str, str)
                    cle_finale = fonction_type_cle(valeur_brute_cle)

                    # B. Traitement des CHAMPS (avec renommage)
                    for nom_col_csv, nom_cle_json, type_col_str in info_colonnes:
                        idx = map_indices[nom_col_csv]
                        
                        if idx >= len(ligne):
                            # On peut décider de mettre null ou de lever une erreur
                            valeur_finale = None
                        else:
                            valeur_brute = ligne[idx]
                            fonction_type = types_disponibles.get(type_col_str, str)
                            
                            # Gestion des chaînes vides pour les nombres -> None ou 0
                            if valeur_brute.strip() == "" and type_col_str in ['int', 'float']:
                                valeur_finale = None 
                            else:
                                valeur_finale = fonction_type(valeur_brute)

                        objet_temp[nom_cle_json] = valeur_finale

                    # Si tout s'est bien passé, on ajoute au dictionnaire principal
                    donnees_json[cle_finale] = objet_temp
                    lignes_traitees += 1

                except ValueError as e:
                    lignes_ignorees += 1
                    print(f"[Ligne {i} IGNORÉE] Erreur de conversion : {e} -> {ligne}")
                except IndexError as e:
                    lignes_ignorees += 1
                    print(f"[Ligne {i} IGNORÉE] Structure incorrecte : {e}")
                except Exception as e:
                    lignes_ignorees += 1
                    print(f"[Ligne {i} IGNORÉE] Erreur inconnue : {e}")

        # --- 4. ÉCRITURE DU JSON ---
        with open(chemin_sortie, 'w', encoding='utf-8') as f_json:
            json.dump(donnees_json, f_json, indent=4, ensure_ascii=False)

        print("-" * 40)
        print(f"TERMINÉ.")
        print(f"Succès : {lignes_traitees} objets créés.")
        print(f"Échecs : {lignes_ignorees} lignes ignorées.")
        print(f"Fichier généré : {chemin_sortie}")
        print("-" * 40)

    except Exception as global_e:
        print(f"Erreur globale : {global_e}")


# --- EXÉCUTION ---
if __name__ == "__main__":
    # ==========================================
    # CONFIGURATION UTILISATEUR
    # ==========================================
    
    # 1. Nom du fichier (doit être dans app/)
    NOM_CSV = "fedi.csv"
    
    # 2. Ligne des titres (0 = 1ère ligne)
    LIGNE_TITRES = 0
    
    # 3. Délimiteur (souvent ; ou ,)
    DELIMITEUR = ","

    # 4. La colonne qui servira de CLÉ unique dans le JSON
    # Format : ("Nom_Colonne_Exact", "type")
    # Types supportés : "str", "int", "float", "bool"
    INFO_CLE = ("Commune Code","str") 

    # 5. Les autres colonnes à extraire et leur type
    # Format : [ ("Nom_Col1", "type"), ("Nom_Col2", "type") ]
    INFO_COLONNES = [
	("Commune","Commune","str"),
    ("EDI","EDI","float"),
    ]

    # Lancement de la fonction
    convertir_csv_json(NOM_CSV, LIGNE_TITRES, INFO_CLE, INFO_COLONNES, DELIMITEUR)