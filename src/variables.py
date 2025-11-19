# ===========================
# Constantes / Métadonnées
# ===========================

SOCIO_VARIABLES = {
    "Taux de pauvreté":{
        "nom_col" :"tx_pauvrete",
        "echelle": ["departement", "commune "],
        "min": 0,
        "max": 100
    },
    "Part des familles monoparentales": "part_familles_monoparentales",
    "Part des 75 ans et +": "part_personnes_agees_75_plus",
    "Taux de chômage": "tx_chomage",
}

ACCESS_PROFESSIONS = {
    "Dentistes": "apl_dentistes",
    "Sages-femmes": "apl_sagesfemmes",
    "Médecins généralistes": "apl_medecins",
    "Infirmiers": "apl_infirmiers",
    "Kinésithérapeutes": "apl_kine",
}

CHEMIN_COMMUNES = "data/communes.json"
CHEMIN_DEPARTEMENTS = "data/departements.json"

COLOR_RANGE = [
    [0, 102, 204],   # Bleu foncé
    [51, 153, 255],  # Bleu moyen
    [102, 204, 255], # Bleu clair
    [255, 204, 102], # Jaune
    [255, 102, 51],  # Orange
    [204, 0, 0]      # Rouge foncé
]