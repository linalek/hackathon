# Hackathon : Diagnostic Territorial de Santé Publique

## Défi Open Data University & Fondation Roche

Ce projet a été réalisé dans le cadre du défi **"Réaliser un diagnostic territorial de santé publique"**, proposé par la Fondation Roche et l'Open Data University.

## Sommaire

- [Contexte et objectif du projet](#contexte-et-objectif-du-projet)
- [Description de la solution](#description-de-la-solution)
- [Préparation de l&#39;environnement](#préparation-de-lenvironnement)
- [Acquisition des données](#acquisition-des-données)
- [Explication des indicateurs utilisés](#explication-des-indicateurs-utilisés)
- [Utilisation](#utilisation)
- [Contributeurs](#contributeurs)
- [Technologies Utilisées](#technologies-utilisées)

## Contexte et objectif du projet

Pour améliorer la santé d'une population, les pouvoirs publics doivent identifier les besoins locaux et organiser l'offre de soins. La santé est influencée par des facteurs multiples : l'offre médicale, mais aussi les pratiques sociales, les revenus ou l'environnement.

Notre projet répond à la problématique suivante : **Comment aider les acteurs locaux à réaliser un diagnostic de santé publique sur leur territoire ?**

Pour répondre à cette problématique, 2 questions se posent :

- **Existe-t-il des territoires qui souffrent d’un manque d’accès à la prévention et aux soins ?**
- **Où sont situées les populations a priori les plus vulnérables ?**

C'est en combinant ces deux dimensions que nous pourrons identifier les zones à risque et c'est l'objectif de notre application.

L'objectif est de fournir un outil d'aide à la décision permettant de guider les collectivités (élaboration de Contrats Locaux de Santé, installation de maisons de santé) en identifiant les territoires à risque.

## Description de la solution

Notre application permet d'identifier et de viualiser, à l'échelle des communes ou à l'échelle des départements, les zones à double vulnérabilité combinant :

- **La vulnérabilité socio-économique** : mesuré par les indices, tels que le taux de pauvreté, chômage, composition familiale, proportion de personnes âgées, indice EDI.
- **La difficulté d'accés au soin** : basé sur des indicateurs d'accessibilité potentielle localisée (APL), pour diverses professions de santé (médecins généralistes, infirmières, sages-femmes, chirurgiens dentistes, kinésithérapeutes).

### Fonctionnalités principales

Notre application offre une interface interactive permettant de :

* Sélectionner et pondérer les critères socio-économiques
* Visualiser les cartes intermédiaires par variable
* Générer un score de vulnérabilité socio économique
* Sélectionner un corps de métier de santé et visualiser leur présence sur le territoire sélectionné
* Visualiser les zones à double vulnérabilité
* Visualiser un classement des territoires les plus vulnérables.

### Calcul des scores

#### Score vulnérabilité socio-économique :

Normalisation des poids pour une variable i :

```math
w_i = \frac{\text{poids}_i}{\sum_{j \in S} \text{poids}_j}
```

Calcul du score avec les valeurs normalisés des variables :

```math

\text{Score}_{socio} = 100 \times \sum_{i \in S} w_i \cdot \text{norm}_{X_i} 

```

#### Score accès aux soins : 

Calcul du score avec l'APL normalisé :

```math
\text{Score}_{acces} = 100 \times (1 - \text{norm}_{APL})
```

On prend soustrait l'APL à 1 car c'est un indicateur inversé, un APL élévé est bon signe.

#### Score de la Double Vulnérabilté :

```math
\text{Score}_{double} = \alpha \cdot \text{Score}_{socio}
                       + (1 - \alpha) \cdot \text{Score}_{acces}
```

## Préparation de l'environnement

1. Cloner le dépôt GitHub :

   ```bash
   git clone [URL_DU_DEPOT]
   cd hackathon
   ```
2. Création et activation d'un environnement virtuel Python :

   ```bash
   python -m venv env
   source env/bin/activate  # Sur Windows : env\Scripts\activate
   ```
3. Installation des dépendances :

   ```bash
    pip install -r requirements.txt
   ```

## Les données

### Acquisition des données

Les données utilisées proviennent de différentes sources (Open Data) :

* **APL (Accessibilité Potentielle Localisée)** : Fichiers excel par profession : https://defis.data.gouv.fr/datasets/62263314072c63d4d53e0c50
* **FEDI (French European Deprivation Index)** : https://odisse.santepubliquefrance.fr/explore/dataset/french-european-deprivation-index-f-edi-2021-par-commune/information/?disjunctive.reglib&disjunctive.libgeo&sort=commune_code
* **Famille monoparentale, Part des personnes agées, Taux de chômage, Taux de pauvreté** : Les colonnes nécessaires ont été extraites de la base de données suivantes : https://statistiques-locales.insee.fr/#bbox=-637658,6637052,2480,1361&c=indicator&i=rp.pt_fammonop&s=2022&view=map1
* **Données géographiques des communes et départements** : https://defis.data.gouv.fr/datasets/5808de39c751df1e0679df72

### Fusion des données

Chacun des indices a été extrait à partir d'un script Python dédié situé dans le dossier `src/scripts_data`. Puis par le fichier `fusion_json.py`, toutes les données ont été fusionnées dans un seul fichier `data/communes.json` et `data/departements.json`, auquel on ajoute la localisation des communes et des départements et qui seront nétoyés par le fichier `nettoyage_communes.py`.

### Explication des indicateurs utilisés

Certains indicateurs sont peu évidents et méritent une explication plus détaillée :

* **APL** (Accessibilité Potentielle Localisée) : Cet indicateur mesure la facilité avec laquelle les habitants d'une zone peuvent accéder aux services de santé. Il prend en compte la distance aux professionnels de santé, la densité de population et la disponibilité des services.
* **EDI** (European Deprivation Index) : C'est un indice composite qui évalue la privation socio-économique à l'échelle locale. Il est calculé à partir de plusieurs variables telles que le niveau d'éducation, le statut d'emploi, les conditions de logement, etc. Un score EDI élevé indique une plus grande privation.

### Format des données

Les données sont stockées dans :

* `data/communes.json` : Données au niveau des communes
* `data/departements.json` : Données au niveau des départements.

Les variables de référence sont documentées dans :

* `data/variables_communes.json`
* `data/variables_departements.json`.

## Utilisation

1. Assurez-vous que l'environnement virtuel est activé.
2. Exécutez le script principal :
   ```bash
   streamlit run app.py
   ```

L'application sera accessible via votre navigateur à l'adresse `http://localhost:8501`.
Le site a aussi été déployé et est accessible à l'adresse suivante : `https://hackathon-llm.streamlit.app/` .

3. Fonctionnalités principales :

* **Vulnérabilité socio-économique** : Sélectionnez et pondérez les critères socio-économiques pour générer une carte de vulnérabilité.
* **Accessibilité aux soins** : Choisissez une profession de santé pour visualiser leur accessibilité sur le territoire.
* **Double vulnérabilité** : Combinez les deux aspects pour identifier les zones les plus à risque.
* **Navigation interactive** : Utilisez l'interface pour explorer les donnéeses au niveau Départements (communes) ou au niveau France (départements).

## Contributeurs

- Maxence AGRA
- Lucine GIRAUD
- Lina LEKBOURI

## Technologies utilisées

- **Langage** : Python 3.9+
- **Interface Web** : Streamlit
- **Manipulation de données** : Pandas, NumPy, JSON
- **Géomatique** : Geopandas
