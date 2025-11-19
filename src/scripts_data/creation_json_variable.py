import json
import os
import numpy as np

# Définition des variables
SOCIO_VARIABLES = {
    "Taux de pauvreté": "tx_pauvrete",
    "Part des familles monoparentales": "part_familles_monoparentales",
    "Part des 75 ans et +": "part_personnes_agees_75_plus",
    "EDI": "EDI",
    "Taux de chômage moyen": "tx_chomage_moyen",
    "Taux de chômage moyen 15-24 ans": "tx_chomage_moyen_15_24_ans",
    "Taux de chômage moyen 25-49 ans": "tx_chomage_moyen_25_49_ans",
    "Taux de chômage moyen 50 ans et plus": "tx_chomage_moyen_50_ans_plus",
    "Taux de chômage moyen femmes": "tx_chomage_moyen_femmes",
    "Taux de chômage moyen hommes": "tx_chomage_moyen_hommes",
}

ACCESS_PROFESSIONS = {
    "Dentistes": "apl_dentistes",
    "Sages-femmes": "apl_sagesfemmes",
    "Médecins généralistes": "apl_medecins",
    "Infirmiers": "apl_infirmiers",
    "Kinésithérapeutes": "apl_kine",
}

def trouver_min_max(fichier_json, echelle):
    """
    Trouve le minimum et le maximum pour chaque variable numérique dans un fichier JSON.
    
    Args:
        fichier_json (str): Chemin vers le fichier JSON
        echelle (str): "commune" ou "departement"
    
    Returns:
        dict: Dictionnaire avec structure
    """
    
    print(f"Lecture du fichier : {fichier_json}")
    
    # Charger le fichier JSON
    with open(fichier_json, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print(f"✓ {len(data)} enregistrements trouvés\n")
    
    # Dictionnaire pour stocker les statistiques temporaires
    stats_temp = {}
    
    # Combiner toutes les variables
    toutes_variables = {**SOCIO_VARIABLES, **ACCESS_PROFESSIONS}
    
    # Créer un mapping inverse : code_variable -> nom_affiché
    code_to_nom = {code: nom for nom, code in toutes_variables.items()}
    
    # Parcourir tous les enregistrements pour collecter les valeurs
    for code, valeurs in data.items():
        if not isinstance(valeurs, dict):
            continue
            
        for variable, valeur in valeurs.items():
            # Ne traiter que les variables définies
            if variable not in toutes_variables.values():
                continue
            
            # Ignorer les valeurs non numériques et None
            if valeur is None or isinstance(valeur, str):
                continue
            
            # Vérifier si c'est un nombre
            try:
                valeur_num = float(valeur)
            except (ValueError, TypeError):
                continue
            
            # Initialiser ou ajouter la valeur
            if variable not in stats_temp:
                stats_temp[variable] = {
                    'values': [valeur_num]
                }
            else:
                stats_temp[variable]['values'].append(valeur_num)
    
    # Convertir au format final avec calcul des statistiques
    stats_dict = {}
    
    for code_variable, donnees in stats_temp.items():
        # Récupérer le nom affiché à partir du code
        nom_affiche = code_to_nom.get(code_variable, code_variable)
        
        # Déterminer le type : "socio" ou "sante"
        if code_variable in SOCIO_VARIABLES.values():
            type_variable = "socio"
        elif code_variable in ACCESS_PROFESSIONS.values():
            type_variable = "sante"
        else:
            type_variable = "autre"
        
        # Calculer les statistiques
        values = np.array(donnees['values'])
        
        stats_dict[nom_affiche] = {
            "nom_col": code_variable,
            "type": type_variable,
            "min": round(float(np.min(values)), 2),
            "max": round(float(np.max(values)), 2),
            "p5": round(float(np.percentile(values, 5)), 2),
            "q1": round(float(np.percentile(values, 25)), 2),
            "q2": round(float(np.percentile(values, 50)), 2),
            "q3": round(float(np.percentile(values, 75)), 2),
            "p95": round(float(np.percentile(values, 95)), 2)
        }
    
    return stats_dict


def trouver_min_max_communes():
    """
    Trouve les min/max pour le fichier communes.json
    """
    fichier = "data/communes.json"
    return trouver_min_max(fichier, "commune")


def trouver_min_max_departements():
    """
    Trouve les min/max pour le fichier departements.json
    """
    fichier = "data/departements.json"
    return trouver_min_max(fichier, "departement")


def sauvegarder_stats(stats, fichier_output):
    """
    Sauvegarde les statistiques dans un fichier JSON.
    
    Args:
        stats (dict): Dictionnaire des statistiques
        fichier_output (str): Chemin du fichier de sortie
    """
    with open(fichier_output, 'w', encoding='utf-8') as f:
        json.dump(stats, f, ensure_ascii=False, indent=4)
    
    print(f"\nStatistiques sauvegardées dans : {fichier_output}")


if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("ANALYSE DES COMMUNES")
    print("=" * 80 + "\n")
    stats_communes = trouver_min_max_communes()
    sauvegarder_stats(stats_communes, "data/variable_communes.json")
    
    print("\n" + "=" * 80)
    print("ANALYSE DES DÉPARTEMENTS")
    print("=" * 80 + "\n")
    stats_departements = trouver_min_max_departements()
    sauvegarder_stats(stats_departements, "data/variable_departements.json")
    
    print("\nAnalyse terminée !")
