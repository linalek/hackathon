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

def nettoyage_arrondissements(communes: dict) -> dict:
    """
    Regroupe les données APL et EDI des arrondissements vers leurs communes principales 
    en utilisant une moyenne pondérée, puis supprime les arrondissements.
    
    Args:
        communes (dict): Le dictionnaire contenant les données des communes.
        
    Returns:
        dict: Le dictionnaire des communes mis à jour.
    """
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
    
    codes_arrondissements_a_supprimer = []

    print("--- 🔬 Début du traitement des arrondissements (Agrégation)...")

    for code_commune, data in communes.items():
        nom_commune = data.get("nom_commune") or data.get("Commune")
        
        match_arrondissement = REGEX_ARRONDISSEMENT.match(str(nom_commune))
        
        if match_arrondissement:
            nom_ville_principale = match_arrondissement.group(1).strip()
            code_principal = CODES_COMMUNES_PRINCIPALES.get(nom_ville_principale)
            
            if code_principal and code_principal in villes_principales_data:
                pop_stan = data.get("population_standardisee", 0) or 0
                pop_totale = data.get("population_totale", 0) or 0

                if pop_stan > 0 or pop_totale > 0:
                    # Pondération APL (Pop. standardisée)
                    villes_principales_data[code_principal]["somme_pop_stan"] += pop_stan
                    for apl_key in ["apl_dentistes", "apl_sagesfemmes", "apl_medecins", "apl_infirmiers", "apl_kine"]:
                        apl_value = data.get(apl_key, 0) or 0
                        villes_principales_data[code_principal][f"somme_{apl_key}_ponderee"] += (apl_value * pop_stan)
                        
                    # Pondération EDI (Pop. totale)
                    villes_principales_data[code_principal]["somme_pop_totale"] += pop_totale
                    edi_value = data.get("EDI", 0) or 0
                    villes_principales_data[code_principal]["somme_edi_ponderee"] += (edi_value * pop_totale)
                    
                    codes_arrondissements_a_supprimer.append(code_commune)

    # Calcul des moyennes et mise à jour
    for code_principal, totals in villes_principales_data.items():
        if code_principal in communes:
            
            pop_stan_totale = totals["somme_pop_stan"]
            if pop_stan_totale > 0:
                for apl_key in ["apl_dentistes", "apl_sagesfemmes", "apl_medecins", "apl_infirmiers", "apl_kine"]:
                    somme_ponderee = totals[f"somme_{apl_key}_ponderee"]
                    communes[code_principal][apl_key] = round(somme_ponderee / pop_stan_totale, 2) 
                communes[code_principal]["population_standardisee"] = pop_stan_totale
            
            pop_totale = totals["somme_pop_totale"]
            if pop_totale > 0:
                somme_edi_ponderee = totals["somme_edi_ponderee"]
                communes[code_principal]["EDI"] = round(somme_edi_ponderee / pop_totale, 2) 
                communes[code_principal]["population_totale"] = pop_totale

    # Suppression des arrondissements
    for code in codes_arrondissements_a_supprimer:
        if code in communes:
            del communes[code]

    print(f"--- 🧹 Nettoyage des arrondissements terminé. {len(codes_arrondissements_a_supprimer)} entrées supprimées.")
    return communes

def supprimer_attribut_commune(communes: dict) -> dict:
    """
    Supprime l'attribut 'Commune' de chaque entrée du dictionnaire de communes.
    Gère les cas où l'attribut est absent.

    Args:
        communes (dict): Le dictionnaire contenant les données des communes.

    Returns:
        dict: Le dictionnaire de communes modifié.
    """
    compteur_suppressions = 0
    print("--- 🧹 Suppression de l'attribut 'Commune'...")
    
    for code_commune, data in communes.items():
        # Utiliser .pop() pour supprimer la clé de manière sécurisée. 
        # Si la clé 'Commune' n'existe pas, .pop() retourne None sans lever d'erreur.
        if data.pop("Commune", None) is not None:
            compteur_suppressions += 1
            
    print(f"✅ Attribut 'Commune' supprimé pour {compteur_suppressions} entrées.")
    return communes

def executer_nettoyage_complet(chemin_entree: str = 'data/communes.json', 
                               chemin_sortie: str = 'data/communes.json') -> dict:
    """
    Fonction principale qui orchestre le chargement, le nettoyage et la sauvegarde des données.
    
    Args:
        chemin_entree (str): Chemin complet vers le fichier JSON d'entrée.
        chemin_sortie (str): Chemin complet vers le fichier JSON de sortie.
        
    Returns:
        dict: Le dictionnaire des communes nettoyé.
    """
    
    # --- 1. Chargement du fichier JSON ---
    print(f"--- 📥 Chargement du fichier : {chemin_entree}")
    try:
        with open(chemin_entree, 'r', encoding='utf-8') as f:
            communes = json.load(f)
        print(f"✅ Chargement réussi. {len(communes)} entrées trouvées.")
    except FileNotFoundError:
        print(f"❌ Erreur: Le fichier d'entrée {chemin_entree} est introuvable.")
        return {}
    except json.JSONDecodeError:
        print(f"❌ Erreur: Impossible de décoder le JSON dans {chemin_entree}.")
        return {}
        
    # --- 2. Application du nettoyage des arrondissements ---
    communes = nettoyage_arrondissements(communes)
    
    # --- 3. Application de la suppression de l'attribut 'Commune' ---
    communes = supprimer_attribut_commune(communes)
    
    # --- 4. Sauvegarde du nouveau fichier JSON ---
    print(f"--- 💾 Sauvegarde du fichier : {chemin_sortie}")
    try:
        with open(chemin_sortie, 'w', encoding='utf-8') as f:
            json.dump(communes, f, indent=4, ensure_ascii=False)
        print("✅ Sauvegarde réussie.")
    except IOError as e:
        print(f"❌ Erreur lors de la sauvegarde du fichier : {e}")
        
    return communes


if __name__ == "__main__":
    
    executer_nettoyage_complet()