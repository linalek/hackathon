# ===========================
# Constantes / Métadonnées
# ===========================

CHEMIN_COMMUNES = "data/communes.json"
CHEMIN_DEPARTEMENTS = "data/departements.json"
CHEMIN_GEOJSON = "data/departements_polygon.geojson"

# 📝 Définition du mapping pour renommer les colonnes
COLUMN_MAPPING = {
    "nom_commune": "Commune",
    "nom_departement": "Département",
    "score_double": "Score Double",  # Nouveau nom souhaité
    "score_socio": "Score Social",    # Nouveau nom souhaité
    "score_acces": "Score Accès",    # Nouveau nom souhaité
    "population_totale": "Population Totale", # Nouveau nom souhaité
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