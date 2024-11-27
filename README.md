# nosql-project
Mini Projet NoSQL avec MongoDB, Redis et Docker Compose

## Description
Ce projet illustre une application web simple qui collecte des données utilisateur via un formulaire et les stocke dans deux systèmes de stockage différents : MongoDB et Redis. L'objectif est de démontrer l'utilisation des technologies NoSQL et de mettre en œuvre la persistance et la visualisation des données collectées.

# Le projet inclut 
    - La persistance des données utilisateur de manière sécurisée dans MongoDB et Redis.
    - La génération de statistiques :
        *   À partir de MongoDB pour des données globales.
        *   À partir de Redis pour les données des dernières 24 heures.
    - L'affichage convivial des données collectées et des statistiques via une interface web.
    - Un environnement Dockerisé pour faciliter le déploiement et l'utilisation.

## Fonctionnalités

1. Collecte de données:
    *   Formulaire permettant de collecter des informations utilisateur, y compris des données personnelles et sensibles comme les  numéros de carte bancaire.
    *   Validation des champs avant la soumission.

2. Stockage des données:
    *   MongoDB pour le stockage à long terme.
    *   Redis pour le stockage temporaire des données collectées au cours des dernières 24 heures.

3. Sécurité:
    *   Les données sensibles (par exemple, numéros de carte bancaire) sont chiffrées à l'aide de l'algorithme Fernet.

4. Statistiques:
    *   Visualisation des statistiques globales et des dernières 24 heures.
    *   Graphiques pour la distribution des données par tranche d'âge et par banque.

5. Environnement Dockerisé:
    *   Fichiers Docker et Docker compose pour simplifier le déploiement et l'exécution.

6. Interface utilisateur:
    *   Templates HTML réactifs pour soumettre des formulaires et visualiser les données/statistiques.

## Prérequis
    - Python 3.7+
    - MongoDB
    - Redis
    - Docker
    - Docker Compose
    - Flask
    - cryptography

## Installation et Utilisation

1. Cloner le dépôt:

```bash
git clone https://github.com/AMJAD0101/nosql-project.git
cd <répertoire-du-projet>
```

2. Générer une clé de chiffrement
    -   Exécutez le script suivant pour générer une clé de chiffrement sécurisée:
```bash
python3 generate_key.py
```
    -   Cela génère un fichier secret.key dans le répertoire du projet.

3. Démarrer les conteneurs Docker
    -   Pour lancer l'application en mode développement :
```bash
docker-compose up --build
```
    -   Pour lancer l'application en mode production :
```bash
docker-compose -f docker-compose.prod.yml up --build
```
4. Accéder à l'application
    *   Page d'accueil avec formulaire : http://localhost:5000/
    *   Statistiques globales : http://localhost:5000/stats
    *   Statistiques des dernières 24 heures : http://localhost:5000/stats_jours
    *   Des tableaux d'affichages des deux bases de données mongoDB et Redis pour controler la récuppération des valeurs : http://localhost:5000/view_data


## Structure du projet

    ├── app.py                 # Application Flask principale
    ├── Dockerfile             # Dockerfile pour construire l'image de l'application
    ├── docker-compose.yml     # Docker Compose pour le développement
    ├── docker-compose-prod.yml # Docker Compose pour la production
    ├── requirements.txt       # Dépendances Python
    ├── templates/             # Templates HTML pour l'interface utilisateur
    │   ├── index.html         # Formulaire principal
    │   ├── stats.html         # Statistiques globales
    │   ├── stats_jours.html   # Statistiques des dernières 24 heures
    │   └── view_data.html     # Visualisation des données collectées
    ├── generate_key.py        # Script pour générer la clé de chiffrement


## Points d'accès API

1. Page d'accueil : / 
    *   Méthode : /
    *   Description :Affiche le formulaire pour collecter des données utilisateur 

2. Soumettre des données: /submit
    *   Méthode : POST
    *   Description : Gère la soumission des formulaires et stocke les données dans MongoDB et Redis.

3. Statistiques globales: /stats
    *   Méthode : GET
    *   Description : Génère des statistiques globales à partir des données stockées dans MongoDB.

4. Statistiques des dernières 24 heures : /stats_jours
    *   Méthode : GET
    *   Description : Génère des statistiques basées sur les données des dernières 24 heures dans Redis.


##  Sécurité
-   Chiffrement Fernet :
    *   Les données sensibles comme les numéros de carte bancaire sont chiffrées avant d'être stockées.
    *   La clé de chiffrement est stockée en toute sécurité dans le fichier secret.key.

-   Validation des champs :
    *   Chaque champ du formulaire est validé pour garantir des entrées correctes.

## Démploiement
1. Clonez le projet sur votre serveur distant.
2. Assurez-vous que Docker et Docker Compose sont installés.
3. Lancez les conteneurs en mode production :
```bash
docker-compose -f docker-compose-prod.yml up
```








