import json
import os
import re

# Codes INSEE des communes principales
CODES_COMMUNES_PRINCIPALES = {
    "Paris": "75056",
    "Lyon": "69123",
    "Marseille": "13055"
}

# Regex pour identifier un arrondissement (ex: "Marseille 1er Arrondissement")
REGEX_ARRONDISSEMENT = re.compile(r"(.+)\s(\d{1,2}(?:e|er|ème)?)\sArrondissement", re.IGNORECASE)

def nettoyage_arrondissements(data_dir: str = 'data/', chemin_entree: str = "communes.json", 
                               chemin_sortie: str = "communes.json"):
    """
    Lit le fichier 'communes.json', regroupe les données APL et EDI des arrondissements
    vers leurs communes principales (Paris, Lyon, Marseille) en utilisant une moyenne
    pondérée par la population standardisée (pour les APL) ou totale (pour l'EDI).

    Args:
        data_dir (str): Le chemin vers le répertoire contenant le fichier 'communes.json'.

    Returns:
        dict: Le dictionnaire des communes nettoyé.
    """
    chemin_fichier = os.path.join(data_dir, chemin_entree)
    
    try:
        with open(chemin_fichier, 'r', encoding='utf-8') as f:
            communes = json.load(f)
    except FileNotFoundError:
        print(f"Erreur: Le fichier {chemin_fichier} est introuvable.")
        return {}
    except json.JSONDecodeError:
        print(f"Erreur: Impossible de décoder le JSON dans {chemin_fichier}.")
        return {}

    # Dictionnaire pour stocker les totaux pondérés pour chaque ville principale
    villes_principales_data = {
        code: {
            # APLs (utilisation de la population standardisée pour la pondération)
            "somme_pop_stan": 0,
            "somme_apl_dentistes_ponderee": 0,
            "somme_apl_sagesfemmes_ponderee": 0,
            "somme_apl_medecins_ponderee": 0,
            "somme_apl_infirmiers_ponderee": 0,
            "somme_apl_kine_ponderee": 0,
            # EDI (utilisation de la population totale pour la pondération)
            "somme_pop_totale": 0,
            "somme_edi_ponderee": 0,
        }
        for code in CODES_COMMUNES_PRINCIPALES.values()
    }
    
    # Liste pour stocker les codes d'arrondissements à supprimer après le traitement
    codes_arrondissements_a_supprimer = []

    print("--- 🔬 Début du traitement des arrondissements...")

    for code_commune, data in communes.items():
        nom_commune = data.get("nom_commune") or data.get("Commune")
        
        # 1. Identifier si c'est un arrondissement
        match_arrondissement = REGEX_ARRONDISSEMENT.match(str(nom_commune))
        
        if match_arrondissement:
            # Récupérer le nom de la ville principale (ex: "Marseille")
            nom_ville_principale = match_arrondissement.group(1).strip()
            
            # Trouver le code principal correspondant
            code_principal = CODES_COMMUNES_PRINCIPALES.get(nom_ville_principale)
            
            if code_principal and code_principal in villes_principales_data:
                # Récupérer les données de population nécessaires
                pop_stan = data.get("population_standardisee", 0)
                pop_totale = data.get("population_totale", 0)
                
                # S'assurer que les populations sont numériques pour la pondération
                if pop_stan is None: pop_stan = 0
                if pop_totale is None: pop_totale = 0

                # S'assurer que l'arrondissement a des populations pour pondérer
                if pop_stan > 0 or pop_totale > 0:
                    
                    # --- Calcul pour les APL (Pondération par population standardisée) ---
                    villes_principales_data[code_principal]["somme_pop_stan"] += pop_stan
                    
                    for apl_key in ["apl_dentistes", "apl_sagesfemmes", "apl_medecins", "apl_infirmiers", "apl_kine"]:
                        apl_value = data.get(apl_key, 0)
                        if apl_value is None: apl_value = 0
                        # Ajout de la valeur pondérée : APL * PopStandardisée
                        villes_principales_data[code_principal][f"somme_{apl_key}_ponderee"] += (apl_value * pop_stan)
                        
                    # --- Calcul pour l'EDI (Pondération par population totale) ---
                    villes_principales_data[code_principal]["somme_pop_totale"] += pop_totale
                    
                    edi_value = data.get("EDI", 0)
                    if edi_value is None: edi_value = 0
                    # Ajout de la valeur pondérée : EDI * PopTotale
                    villes_principales_data[code_principal]["somme_edi_ponderee"] += (edi_value * pop_totale)
                    
                    codes_arrondissements_a_supprimer.append(code_commune)
                else:
                    print(f"⚠️ Arrondissement sans population: {nom_commune} ({code_commune}). Ignoré pour la pondération.")


    # 2. Calcul des moyennes pondérées et mise à jour de la commune principale
    for code_principal, totals in villes_principales_data.items():
        if code_principal in communes:
            print(f"✅ Calcul et regroupement pour la commune principale: {communes[code_principal]['nom_commune']} ({code_principal})")
            
            # --- Moyenne APL (Pop. standardisée) ---
            pop_stan_totale = totals["somme_pop_stan"]
            if pop_stan_totale > 0:
                for apl_key in ["apl_dentistes", "apl_sagesfemmes", "apl_medecins", "apl_infirmiers", "apl_kine"]:
                    somme_ponderee = totals[f"somme_{apl_key}_ponderee"]
                    # Nouvelle valeur = Somme(APL * PopStan) / Somme(PopStan)
                    communes[code_principal][apl_key] = round(somme_ponderee / pop_stan_totale,2)
                
                # On ajoute aussi la population standardisée totale dans la fiche principale
                communes[code_principal]["population_standardisee"] = pop_stan_totale
            
            # --- Moyenne EDI (Pop. totale) ---
            pop_totale = totals["somme_pop_totale"]
            if pop_totale > 0:
                somme_edi_ponderee = totals["somme_edi_ponderee"]
                # Nouvelle valeur = Somme(EDI * PopTotale) / Somme(PopTotale)
                communes[code_principal]["EDI"] = round(somme_edi_ponderee / pop_totale,2)
                
                # On ajoute aussi la population totale dans la fiche principale
                communes[code_principal]["population_totale"] = pop_totale
            
        else:
            print(f"❌ Erreur: Code commune principal {code_principal} non trouvé dans les données. Regroupement impossible.")


    # 3. Suppression des arrondissements
    for code in codes_arrondissements_a_supprimer:
        if code in communes:
            del communes[code]

    print(f"--- 🧹 Nettoyage terminé. {len(codes_arrondissements_a_supprimer)} arrondissements regroupés et supprimés.")

    # --- 4. Sauvegarde du nouveau fichier JSON ---
    chemin_fichier_sortie = os.path.join(data_dir, chemin_sortie)
    try:
        with open(chemin_fichier_sortie, 'w', encoding='utf-8') as f:
            json.dump(communes, f, indent=4, ensure_ascii=False)
        print(f"💾 Succès: Le résultat a été sauvegardé dans {chemin_fichier_sortie}")
    except IOError as e:
        print(f"❌ Erreur lors de la sauvegarde du fichier : {e}")

    return communes

# --- Exemple d'utilisation (facultatif) ---

if __name__ == "__main__":
    
    nettoyage_arrondissements(data_dir='data/', chemin_entree="communes.json", chemin_sortie="communes.json")    