# 🍽️ Restaurant Docker — MongoDB + Mongo Express + Python Importer

## 1. Présentation du projet
Mini-projet Docker réalisé dans le cadre de la 2ème année Intelligence Artificielle – Option Big Data.
Il met en place une petite base de données MongoDB pour un **restaurant fictif**, consultable depuis
une interface web, et alimentée automatiquement par un script Python.

## 2. Objectif
Démontrer l'utilisation de Docker et Docker Compose :
- un **Dockerfile** écrit manuellement ;
- un fichier **docker-compose.yml** avec 3 services ;
- un **volume** pour la persistance des données ;
- un lancement complet avec **une seule commande**.

## 3. Architecture

```
                  docker compose up
                         │
        ┌────────────────┼─────────────────┐
        ▼                ▼                 ▼
    mongodb ◄─────── importer         mongo-express
        │            (Python)                │
   volume mongodb_data                 localhost:8081
```

Les conteneurs communiquent sur le réseau `restaurant_net` via le nom de service `mongodb`.

## 4. Technologies utilisées
- Docker et Docker Compose
- MongoDB 7.0
- Mongo Express 1.0.2
- Python 3.12 et pymongo

## 5. Structure des fichiers
```
restaurant-docker/
├── docker-compose.yml   # orchestration des services
├── Dockerfile           # image Python de l'importer
├── requirements.txt     # dépendances Python
├── importer.py          # génération + insertion des données fictives
├── README.md            # ce fichier
└── data/
    └── README.md        # explication sur les données fictives
```

## 6. Description des services
| Service | Rôle |
|---|---|
| **mongodb** | Base de données (image `mongo:7.0`), volume `mongodb_data` monté sur `/data/db`, healthcheck (ping). |
| **importer** | Service Python construit avec le Dockerfile. Attend que MongoDB soit *healthy*, insère les données, affiche « Importation terminée avec succès. » puis s'arrête (code 0). |
| **mongo-express** | Interface web (`mongo-express:1.0.2`) accessible sur le port 8081, connectée à `mongodb://mongodb:27017/`. |

## 7. Description du dataset fictif
Base : **restaurant_db** — toutes les données sont inventées.

| Collection | Documents | Champs |
|---|---|---|
| `clients` | 10 | `client_id`, `nom`, `ville` |
| `plats` | 10 | `plat_id`, `nom`, `categorie`, `prix`, `disponible` |
| `commandes` | 15 | `commande_id`, `client_id`, `plats[{plat_id, quantite}]`, `total`, `statut` |

- Catégories de plats : Burger, Pizza, Pâtes, Salade, Dessert, Boisson.
- Statuts : En préparation, Prête, Livrée, Annulée.
- Les totaux sont calculés par le script et les `client_id` / `plat_id` des commandes existent toujours.

## 8. Installation
Prérequis : Docker Desktop installé et démarré.
```bash
cd restaurant-docker
```
Aucune autre installation n'est nécessaire (pas de Python local, pas de dataset à télécharger).

## 9. Lancement
```bash
docker compose up
```
Cette unique commande construit l'image de l'importer, démarre MongoDB, attend qu'il soit healthy,
importe les données et démarre Mongo Express.

## 10. Accès à Mongo Express
👉 http://localhost:8081
Ouvrir `restaurant_db` puis les collections `clients`, `plats`, `commandes`.

## 11. Vérification des conteneurs
```bash
docker compose ps
docker compose ps -a
```
`mongodb` doit être *healthy*, `mongo-express` *Up*. L'importer apparaît avec `-a` : *Exited (0)*, c'est normal.

## 12. Affichage des logs
```bash
docker compose logs
docker compose logs importer
```

## 13. Test de persistance
1. Lancer : `docker compose up`
2. Ajouter un client de test :
```bash
   docker compose exec mongodb mongosh restaurant_db --eval 'db.clients.insertOne({client_id: 11, nom: "Test", ville: "Rabat"})'
```
3. Arrêter : `docker compose down` (**sans** `-v`)
4. Relancer : `docker compose up`
5. Vérifier que le client 11 existe toujours et que l'importer indique : *« Les données existent déjà dans le volume (persistance) »*.

## 14. Arrêt du projet
```bash
docker compose down        # arrête et supprime les conteneurs, GARDE le volume
```
⚠️ `docker compose down -v` supprime aussi le volume (et donc les données) : à utiliser uniquement pour repartir de zéro.

## 15. Commandes MongoDB utilisées
```bash
docker compose exec mongodb mongosh restaurant_db
```
```javascript
// 1. Tous les clients
db.clients.find()
// 2. Plats disponibles
db.plats.find({ disponible: true })
// 3. Commandes livrées
db.commandes.find({ statut: "Livrée" })
// 4. Nombre de clients
db.clients.countDocuments()
// 5. Commandes par statut
db.commandes.aggregate([{ $group: { _id: "$statut", nombre: { $sum: 1 } } }])
// 6. Commandes par client
db.commandes.aggregate([{ $group: { _id: "$client_id", nombre_commandes: { $sum: 1 } } }, { $sort: { _id: 1 } }])
// 7. Prix moyen des plats
db.plats.aggregate([{ $group: { _id: null, prix_moyen: { $avg: "$prix" } } }])
// 8. Chiffre d'affaires fictif des commandes livrées
db.commandes.aggregate([{ $match: { statut: "Livrée" } }, { $group: { _id: null, chiffre_affaires: { $sum: "$total" } } }])
// 9. Commandes avec total > 100
db.commandes.find({ total: { $gt: 100 } })
// 10. Plats regroupés par catégorie
db.plats.aggregate([{ $group: { _id: "$categorie", nombre_plats: { $sum: 1 }, plats: { $push: "$nom" } } }])
```

## 16. Conclusion
Ce projet montre comment Docker Compose orchestre plusieurs services (base de données, interface web,
script Python) avec un Dockerfile personnel, un healthcheck pour l'ordre de démarrage, un réseau interne
et un volume nommé pour la persistance, le tout lancé avec une seule commande.

## 17. Déploiement en ligne (Vercel + MongoDB Atlas)

Vercel n'exécute pas Docker : la base est hébergée sur **MongoDB Atlas** (gratuit). Le lancement local avec Docker reste inchangé.
Fichiers ajoutés : `vercel.json`, `api/index.py`, `.vercelignore`.

1. **Atlas** : cluster M0 Free, utilisateur (Database Access), accès `0.0.0.0/0` (Network Access), copier l'URI `mongodb+srv://...`.
2. **Importer les données dans Atlas** (une fois, PowerShell) :
```powershell
pip install pymongo
$env:MONGO_URI="mongodb+srv://USER:PASSWORD@cluster0.xxxxx.mongodb.net/"
$env:DB_NAME="restaurant_db"
python importer.py
```
3. **GitHub** : `git add .` / `git commit -m "Vercel"` / `git push`.
4. **Vercel** : Add New → Project → importer le repository → Framework Preset **Other** → variables `MONGO_URI` et `DB_NAME=restaurant_db` → **Deploy**.


### Mise à jour importante pour Vercel

- Le fichier `requirements.txt` installe `pymongo[srv]` (donc le support DNS SRV) et `certifi` (certificats CA TLS).
- Sur Vercel, ajouter `MONGO_URI` et `DB_NAME` dans **Settings → Environment Variables**, puis redéployer.
- `MONGO_URI` doit être l'URI Atlas `mongodb+srv://...`, sans espaces et avec le mot de passe correctement encodé si nécessaire. Ne jamais publier cette URI sur GitHub.
- Vérifier dans Atlas que le cluster est actif, que l'utilisateur Database Access existe et que Network Access autorise les connexions de l'application. Pour un test, `0.0.0.0/0` autorise toutes les adresses IP : à utiliser seulement avec un mot de passe fort et en comprenant le risque.
- Les collections `clients`, `plats` et `commandes` doivent déjà être importées dans Atlas avec `importer.py` avant d'ouvrir le site.
- Après toute modification de `requirements.txt` ou `app.py`, faire un nouveau déploiement Vercel.
