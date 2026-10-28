# Projet Data Science – Vélib

**Objectif :** prédire le nombre de vélos Vélib disponibles dans 30 minutes, dans n'importe quelle station.

## Pistes

- Feature engineering pour trouver des motifs (heure, jour de la semaine, historique de la station, etc.)
- Analyser l'effet de l'horaire
- Analyser l'effet de la météo (éventuellement avec d'autres datasets météo)

## Données

Relevés des stations (API open data Vélib) toutes les 5 min, collectés par GitHub Actions et stockés dans la release `data` (`historique_stations.csv`).

Relevés des données météo (API dd'open data Météo) toutes les 15 min, collectés par appel API (`script get_weather.py`) et exportés dans un csv (`meteo_paris_octobre_2026.csv`).

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
- introduction de la variable **deltat30** (avaliable_t30 - avaliable) pour étudier si des vélos disparaissent ou arrivent
- introduction de la catégorie **tendence** : hausse, baisse ou stable
- intoduction de la répresentation cyclique cos / sin du jour
- introduction de la variable **is_weekend**
- introduction de la variable **is_rush_hour** en définissant le percentile 0.75 pour définir les horaires où l'activité est haute. Nous considérons séparément les weekends et les jours de la semaine en adaptant bien la valeur de la variable.

## Données météo

### Récupération et préparation des données
- récuperation avec le script `get_weather.py`
- renommage de la colonne date en horodatage pour avoir les mêmes noms dans les deux tables et ensuite la conversion de la colonne en datetime
- suppresion des doublons sur les données météo et configuration de l'index sur horodatage.

### Jointure avec les données vélib
La récupération de données météo se fait toutes les 15 minutes, contrairement aux données vélib qui a été fait toutes les 15 minutes.
Pour maximiser la récupération des données et éviter de la perte de lignes à cause de données temporelles non alignées, nous avons décidé de:
- séparer les données météo que l'on souhaite garder en trois types : continues, cumulées et textuelles
- les données continues comme la temperature ou la vitesse du vent peuvent être interpolées
- les donnes cumulées comme la pluie ou les précipitations vont prendre la dernière valeur disponible, datée de moins de 15 minutes
- les données textuelles vont prendre la dernière valeur disponible, datée de moins de 8 minutes.
- arrondissement des floats à 2 chiffres après la virgule

On effectue une jointure à gauche avec les données vélos. 