# ===========================
# Constantes / Métadonnées
# ===========================

SOCIO_VARIABLES = {
    "Taux de pauvreté": "tx_pauvrete",
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
CHEMIN_GEOJSON = "data/departements_polygon.geojson"

COLOR_RANGE = [
    [0, 100, 0],     # Vert foncé
    [0, 140, 0],     # Vert
    [60, 180, 0],    # Vert clair
    [140, 210, 0],   # Jaune-vert
    [200, 230, 0],   # Jaune tirant vers le vert
    [255, 220, 0],   # Jaune vif
    [255, 160, 0],   # Orange
    [255, 120, 0],   # Orange soutenu
    [255, 60, 0],    # Rouge-orangé
    [180, 0, 0]      # Rouge bien foncé
]