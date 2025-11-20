# ===========================
# Constantes / Métadonnées
# ===========================

CHEMIN_COMMUNES = "data/communes.json"
CHEMIN_DEPARTEMENTS = "data/departements.json"
CHEMIN_GEOJSON = "data/departements_polygon.geojson"

COLUMN_MAPPING = {
    "nom_commune": "Commune",
    "code_postal": "Code Postal",
    "code_insee": "Numéro",
    "nom_departement": "Département",
    "score_double": "Score Double Vulnérabilité (en %)", 
    "score_socio": "Score Vulnérabilité socio-économique (en %)", 
    "apl_dentistes": "Accès aux dentistes (en ETP/100 000 hab)",
    "apl_medecins": "Accès aux médecins généralistes (en ETP/100 000 hab)",
    "apl_infirmiers": "Accès aux infirmiers (en ETP/100 000 hab)",
    "apl_sagesfemmes": "Accès aux sages-femmes (en ETP/100 000 hab)",
    "apl_kine": "Accès aux kinésithérapeutes (en ETP/100 000 hab)",
    "population_totale": "Population",
}

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