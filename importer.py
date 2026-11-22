"""
Importer : génère des données 100 % fictives pour un restaurant
et les insère dans MongoDB (base restaurant_db).
"""

import os
import sys
import time

from pymongo import MongoClient
from pymongo.errors import PyMongoError

# Paramètres reçus via docker-compose (valeurs par défaut au cas où)
MONGO_URI = os.getenv("MONGO_URI", "mongodb://mongodb:27017/")
DB_NAME = os.getenv("DB_NAME", "restaurant_db")

# ---------------------------------------------------------------
# 1. DONNÉES FICTIVES
# ---------------------------------------------------------------
CLIENTS = [
    {"client_id": 1, "nom": "Sara", "ville": "Rabat"},
    {"client_id": 2, "nom": "Youssef", "ville": "Casablanca"},
    {"client_id": 3, "nom": "Lina", "ville": "Temara"},
    {"client_id": 4, "nom": "Omar", "ville": "Salé"},
    {"client_id": 5, "nom": "Nada", "ville": "Fès"},
    {"client_id": 6, "nom": "Adam", "ville": "Marrakech"},
    {"client_id": 7, "nom": "Salma", "ville": "Rabat"},
    {"client_id": 8, "nom": "Ilyas", "ville": "Casablanca"},
    {"client_id": 9, "nom": "Maya", "ville": "Salé"},
    {"client_id": 10, "nom": "Rayan", "ville": "Temara"},
]

PLATS = [
    {"plat_id": 1, "nom": "Burger Atlas", "categorie": "Burger", "prix": 45, "disponible": True},
    {"plat_id": 2, "nom": "Burger Médina", "categorie": "Burger", "prix": 50, "disponible": True},
    {"plat_id": 3, "nom": "Pizza Soleil", "categorie": "Pizza", "prix": 60, "disponible": True},
    {"plat_id": 4, "nom": "Pizza Oasis", "categorie": "Pizza", "prix": 65, "disponible": False},
    {"plat_id": 5, "nom": "Pâtes Andalouses", "categorie": "Pâtes", "prix": 55, "disponible": True},
    {"plat_id": 6, "nom": "Penne Sahara", "categorie": "Pâtes", "prix": 48, "disponible": True},
    {"plat_id": 7, "nom": "Salade Jardin", "categorie": "Salade", "prix": 35, "disponible": True},
    {"plat_id": 8, "nom": "Gâteau Zellige", "categorie": "Dessert", "prix": 30, "disponible": True},
    {"plat_id": 9, "nom": "Citronnade Menthe", "categorie": "Boisson", "prix": 15, "disponible": True},
    {"plat_id": 10, "nom": "Thé Glacé Rif", "categorie": "Boisson", "prix": 12, "disponible": False},
]

# (commande_id, client_id, [(plat_id, quantite), ...], statut)
COMMANDES_BRUTES = [
    (1, 1, [(1, 2), (9, 2)], "Livrée"),
    (2, 2, [(3, 1), (10, 1)], "Livrée"),
    (3, 3, [(2, 2), (7, 1)], "Livrée"),
    (4, 4, [(5, 1), (8, 1)], "Prête"),
    (5, 5, [(6, 2)], "Livrée"),
    (6, 1, [(3, 2), (9, 2)], "En préparation"),
    (7, 6, [(7, 2), (9, 2)], "Livrée"),
    (8, 7, [(1, 1), (10, 1)], "Annulée"),
    (9, 8, [(2, 1), (8, 2)], "Livrée"),
    (10, 3, [(5, 2), (7, 1), (9, 1)], "Livrée"),
    (11, 9, [(6, 1), (8, 1)], "Prête"),
    (12, 2, [(1, 3), (9, 3)], "En préparation"),
    (13, 10, [(3, 1), (7, 1)], "Annulée"),
    (14, 5, [(2, 1), (5, 1), (8, 1)], "Livrée"),
    (15, 1, [(6, 1), (9, 1)], "Livrée"),
]


def construire_commandes():
    """Construit les commandes, vérifie la cohérence et calcule les totaux."""
    prix_par_plat = {p["plat_id"]: p["prix"] for p in PLATS}
    ids_clients = {c["client_id"] for c in CLIENTS}
    commandes = []

    for commande_id, client_id, lignes, statut in COMMANDES_BRUTES:
        assert client_id in ids_clients, f"client_id inexistant : {client_id}"
        total = 0
        plats_commande = []
        for plat_id, quantite in lignes:
            assert plat_id in prix_par_plat, f"plat_id inexistant : {plat_id}"
            total += prix_par_plat[plat_id] * quantite
            plats_commande.append({"plat_id": plat_id, "quantite": quantite})
        commandes.append({
            "commande_id": commande_id,
            "client_id": client_id,
            "plats": plats_commande,
            "total": total,
            "statut": statut,
        })
    return commandes


# ---------------------------------------------------------------
# 2. CONNEXION À MONGODB (avec quelques tentatives par sécurité)
# ---------------------------------------------------------------
def se_connecter(tentatives=10, delai=3):
    for essai in range(1, tentatives + 1):
        try:
            client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
            client.admin.command("ping")
            print(f"Connexion à MongoDB réussie ({MONGO_URI}).")
            return client
        except PyMongoError as erreur:
            print(f"Tentative {essai}/{tentatives} échouée : {erreur}")
            time.sleep(delai)
    print("Impossible de se connecter à MongoDB.")
    sys.exit(1)


# ---------------------------------------------------------------
# 3. IMPORTATION
# ---------------------------------------------------------------
def main():
    print("Démarrage de l'importer...")
    client = se_connecter()
    db = client[DB_NAME]

    # Si les 3 collections contiennent déjà des données (volume persistant),
    # on n'importe pas une seconde fois : pas de doublons.
    deja_importe = all(
        db[nom].count_documents({}) > 0 for nom in ("clients", "plats", "commandes")
    )
    if deja_importe:
        print("Les données existent déjà dans le volume (persistance) : importation ignorée.")
        print("Importation terminée avec succès.")
        client.close()
        return

    commandes = construire_commandes()

    # Repartir d'un état propre (cas d'une importation partielle précédente)
    for nom in ("clients", "plats", "commandes"):
        db[nom].drop()

    db.clients.insert_many(CLIENTS)
    db.plats.insert_many(PLATS)
    db.commandes.insert_many(commandes)

    print(f"Base '{DB_NAME}' :")
    print(f"  - clients   : {db.clients.count_documents({})} documents")
    print(f"  - plats     : {db.plats.count_documents({})} documents")
    print(f"  - commandes : {db.commandes.count_documents({})} documents")
    print("Importation terminée avec succès.")
    client.close()


if __name__ == "__main__":
    main()