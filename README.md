# Projet Data Science – Vélib

**Objectif :** prédire le nombre de vélos Vélib disponibles dans 30 minutes, dans n'importe quelle station.


## Lancer le projet

Les données lourdes ne sont pas dans le dépôt (limite de taille de GitHub). Les relevés bruts sont dans la release `data` du dépôt, et le jeu nettoyé est recréé par le notebook 01.

```bash
git clone https://github.com/PorcherLeo/ProjetDataScience.git
cd ProjetDataScience   # le dossier du dépôt (à adapter si le projet est dans un sous-dossier)

python3 -m venv env
source env/bin/activate
pip install -r requirements.txt

mkdir -p data/raw
curl -L -o data/raw/historique_final_version.csv \
  https://github.com/PorcherLeo/ProjetDataScience/releases/download/data/historique_stations.csv
```

Puis ouvrir les notebooks du dossier `notebooks/` dans VS Code et lancer dans l'ordre :
1. `01-exploration.ipynb` (tout exécuter) : lit `data/raw/historique_final_version.csv` et `data/meteo_paris.csv`, garde les relevés jusqu'au 7 novembre 2026 à 0 h UTC, et écrit `data/clean/historique_nettoye.csv` (environ 1,2 Go, quelques minutes).
2. `02-modelisation.ipynb` (tout exécuter) : lit le fichier nettoyé. Compter environ une heure de calcul et 8 Go de mémoire.

Le téléchargement fait environ 730 Mo. Le fichier de la release peut contenir des relevés après le 7 novembre : ils sont écartés par le notebook 01.

Les fichiers de `data/` : `meteo_paris.csv` est déjà dans le dépôt. Pour le régénérer, lancer `python collecte/get_weather.py`. La collecte des relevés (`collecte/`) est arrêtée depuis le 7 novembre.

## Pistes

- Feature engineering pour trouver des motifs (heure, jour de la semaine, historique de la station, etc.)
- Analyser l'effet de l'horaire
- Analyser l'effet de la météo (éventuellement avec d'autres datasets météo)

## Données

Relevés des stations (API open data Vélib) toutes les 5 min, collectés par GitHub Actions et stockés dans la release `data` (`historique_stations.csv`).

Relevés des données météo (API dd'open data Météo) toutes les 15 min, collectés par appel API (`collecte/get_weather.py`) et exportés dans un csv (`data/meteo_paris.csv`).

### Préparation et nettoyage des données vélib

- Fusion des colonnes "velo_meca" et "velo_elec" pour créer une nouvelle colonne "available" 
- Ecarter les stations en dehors de Paris
- Suppression des stations à capacité nulle (0)
- Suppresion des doublons

### Création de la variable cible 
- le choix de la variable : nombre de vélos disponibles dans 30 minutes
- on cherche la nombre de vélos disponibles 30 min plus tard pour effectuer un shift des données
- Suppresion des lignes où le shift n'était pas possible à cause des données manquantes (avaliabe_t30 est null)

### Modélisation des features : 
- introduction de la variable **delta_t30** (avaliable - avaliabe_last_30) pour étudier si des vélos disparaissent ou arrivent
- introduction de la catégorie **tendence** : hausse, baisse ou stable
- intoduction de la répresentation cyclique cos / sin du jour
- introduction de la variable **is_weekend**
- introduction de la variable **is_rush_hour** en définissant le percentile 0.75 pour définir les horaires où l'activité est haute. Nous considérons séparément les weekends et les jours de la semaine en adaptant bien la valeur de la variable.

## Données météo

### Récupération et préparation des données
- récuperation avec le script `collecte/get_weather.py`
- renommage de la colonne date en horodatage pour avoir les mêmes noms dans les deux tables et ensuite la conversion de la colonne en datetime
- suppresion des doublons sur les données météo et configuration de l'index sur horodatage.

### Jointure avec les données vélib
La récupération de données météo se fait toutes les 15 minutes, contrairement aux données vélib qui a été fait toutes les 5 minutes.
Pour maximiser la récupération des données et éviter de la perte de lignes à cause de données temporelles non alignées, nous avons décidé de:
- séparer les données météo que l'on souhaite garder en trois types : continues, cumulées et textuelles
- les données continues comme la temperature ou la vitesse du vent peuvent être interpolées
- les donnes cumulées comme la pluie ou les précipitations vont prendre la dernière valeur disponible, datée de moins de 15 minutes
- les données textuelles vont prendre la dernière valeur disponible, datée de moins de 8 minutes.
- arrondissement des floats à 2 chiffres après la virgule

On effectue une jointure à gauche avec les données vélos. 

## Organisation du dépôt

- `collecte/` : code pour récupérer la donnée. `fetch_data.py` relève l'état des stations, `ci_collect.sh` et `.github/workflows/fetch.yml` le lancent sur GitHub Actions, `merge_sources.py` fusionne les historiques, `get_weather.py` récupère la météo, `script.sh` permet une collecte en local.
- `notebooks/` : `01-exploration.ipynb` (exploration, nettoyage, création des variables et export), `02-modelisation.ipynb` (validation, comparaison des modèles, test final), `03_modelisation_catboost_ridge.ipynb` (essais CatBoost et Ridge), `02.Velib-Gloire.ipynb` (travail sur les stations voisines, repris dans le notebook 01).
- `data/` : `meteo_paris.csv` (suivi par git), `raw/historique_final_version.csv` (relevés bruts, issus de la release `data`) et `clean/historique_nettoye.csv` (produit par le notebook 01). Les deux derniers ne sont pas versionnés car trop lourds.
- `requirements.txt` : dépendances. Les notebooks se lancent depuis le dossier `notebooks/`.



## Processus expérimental

1. Collecte : un relevé de toutes les stations toutes les 5 minutes, du 16 octobre au 6 novembre 2026 (arrêt le 7 novembre à 0 h UTC), et météo toutes les 15 minutes.

2. Exploration et nettoyage (notebook 01) : filtrage des stations, création de la cible `available_t30`, des variables temporelles, de la météo, des stations voisines et des manifestations, puis export du jeu nettoyé (6,5 millions de lignes, 1 217 stations).
3. Modélisation (notebook 02) : découpage temporel, validation walk-forward sur 15 plis, comparaison de la baseline et de trois modèles, réglage des paramètres, entraînement final, test, importance des variables et analyse des erreurs.

## Choix de modélisation

- Cible : `available_t30`, le nombre de vélos disponibles 30 minutes plus tard. Le modèle prédit la variation (`available_t30 - available`), et la prédiction finale est ramenée entre 0 et la capacité de la station.
- Baseline : la persistance, c'est-à-dire prédire qu'il y aura autant de vélos dans 30 minutes qu'à l'instant présent.
- Métriques : MAE (principale) et RMSE.
- Pas de découpage aléatoire : deux relevés voisins de 5 minutes sont presque identiques et la cible est à 30 minutes, ce qui ferait fuiter l'information du test vers l'entraînement. On coupe donc dans le temps.
- Test : les 5 derniers jours (2 au 6 novembre), soit environ 19 % des lignes. Il n'est utilisé qu'une seule fois à la fin.
- Validation : walk-forward sur 15 plis. Le pli k s'entraîne sur tout ce qui précède un jour donné, moins une marge de 30 minutes (purge) pour que la cible n'empiète pas sur la validation, et valide sur ce jour. 
- Variables : remplissage de la station, nombre de vélos à la même heure la veille, variation sur 30 minutes, heure (sinus et cosinus), week-end, heure de pointe, météo et stations voisines à moins de 500 m (taux de remplissage moyen, variation moyenne, nombre de voisines). Chaque variable n'utilise que des informations connues à l'instant de la prédiction.
- Modèles comparés : XGBoost, XGBoost avec les stations voisines, Random Forest. Les valeurs manquantes des voisines (stations sans voisine à 500 m, 0,06 % des lignes) sont laissées vides pour XGBoost et remplacées par la médiane pour le Random Forest.
- Réglage : grille de paramètres sur les 3 derniers plis avec 25 % des lignes, pour limiter le temps de calcul. Les paramètres retenus sont profondeur 6, 400 arbres et taux d'apprentissage 0,1 pour XGBoost, profondeur 12 et feuille minimale 20 pour le Random Forest.
- Modèle final : XGBoost avec les stations voisines, entraîné une fois sur tout le jeu d'entraînement avec la perte en erreur absolue.

## Résultats

Validation walk-forward, moyenne sur les 15 plis :

| Modèle | MAE | RMSE |
|---|---|---|
| baseline (persistance) | 1,230 | 2,098 |
| XGBoost | 1,235 | 2,127 |
| XGBoost + voisines | 1,218 | 2,097 |
| Random Forest | 1,233 | 2,095 |

Seul XGBoost avec les stations voisines passe sous la baseline. Les modèles sont moins bons que la baseline sur les premiers plis, qui ont peu de données d'entraînement.

Test (2 au 6 novembre), modèle entraîné une fois sur tout le jeu d'entraînement :

| | MAE | RMSE |
|---|---|---|
| baseline | 1,272 | 2,257 |
| modèle final | 1,215 | 2,144 |

Soit 4,5 % de MAE et 5,0 % de RMSE en moins. Le modèle fait mieux que la baseline chaque jour du test.

Ce qu'on en retient :
- La variable la plus utile est la variation moyenne des stations voisines. La météo n'apporte presque rien.
- Le gain vient des heures de pointe (7 h à 9 h et 17 h à 19 h), surtout pour les grandes stations. Hors pointe, le modèle ne fait pas mieux que la persistance.
- Le modèle fait moins bien que la baseline quand la station est remplie à plus de 80 % (MAE 1,298 contre 1,234).
