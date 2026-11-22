import os
from flask import Flask, render_template_string, request, redirect, url_for
from pymongo import MongoClient
import certifi

# En local avec Docker : mongodb://mongodb:27017/
# Sur Vercel : définir MONGO_URI dans Environment Variables (MongoDB Atlas)
MONGO_URI = os.getenv("MONGO_URI", "mongodb://mongodb:27017/")
DB_NAME = os.getenv("DB_NAME", "restaurant_db")

# Atlas utilise mongodb+srv et TLS. certifi fournit le bundle de certificats CA.
client_options = {"serverSelectionTimeoutMS": 10000}
if MONGO_URI.startswith("mongodb+srv://") or "mongodb.net" in MONGO_URI:
    client_options["tlsCAFile"] = certifi.where()

mongo_client = MongoClient(MONGO_URI, **client_options)
db = mongo_client[DB_NAME]
app = Flask(__name__)

STATUTS = ["En préparation", "Prête", "Livrée", "Annulée"]
CLASSES_STATUT = {
    "En préparation": "prep",
    "Prête": "prete",
    "Livrée": "livree",
    "Annulée": "annulee",
}

PAGE = """
<!doctype html>
<html lang="fr">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Gestion Restaurant</title>
  <style>
    :root {
      --rose: #e91e8c;
      --rose-fonce: #c2185b;
      --rose-clair: #fce4ec;
      --rose-pale: #fff5f9;
      --texte: #3b2230;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      font-family: "Segoe UI", Tahoma, Arial, sans-serif;
      background: var(--rose-pale);
      color: var(--texte);
    }
    header {
      background: linear-gradient(135deg, #ff6fb5, var(--rose-fonce));
      color: white;
      padding: 28px 40px;
      box-shadow: 0 4px 14px #c2185b44;
    }
    header h1 { margin: 0; font-size: 30px; letter-spacing: 0.5px; }
    header p { margin: 6px 0 0; opacity: 0.9; font-size: 14px; }
    nav {
      background: white;
      padding: 12px 40px;
      display: flex;
      gap: 12px;
      flex-wrap: wrap;
      box-shadow: 0 2px 8px #0000000d;
      position: sticky;
      top: 0;
      z-index: 5;
    }
    nav a {
      text-decoration: none;
      color: var(--rose-fonce);
      background: var(--rose-clair);
      padding: 8px 18px;
      border-radius: 20px;
      font-weight: 600;
      font-size: 14px;
    }
    nav a:hover { background: var(--rose); color: white; }
    main { padding: 30px 40px 50px; max-width: 1200px; margin: auto; }
    .stats {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(210px, 1fr));
      gap: 20px;
      margin-bottom: 10px;
    }
    .card {
      background: white;
      border-radius: 18px;
      padding: 22px;
      box-shadow: 0 6px 18px #e91e8c1f;
      border-left: 6px solid var(--rose);
      display: flex;
      align-items: center;
      gap: 16px;
    }
    .card .icone { font-size: 34px; }
    .card .valeur { font-size: 28px; font-weight: 700; color: var(--rose-fonce); }
    .card .label { font-size: 13px; color: #8a6a7a; }
    section {
      background: white;
      border-radius: 18px;
      padding: 24px;
      margin-top: 30px;
      box-shadow: 0 6px 18px #e91e8c14;
    }
    section h2 { margin: 0 0 18px; color: var(--rose-fonce); font-size: 22px; }
    .table-wrap { overflow-x: auto; }
    table { border-collapse: separate; border-spacing: 0; width: 100%; }
    th {
      background: var(--rose-clair);
      color: var(--rose-fonce);
      text-align: left;
      padding: 12px 14px;
      font-size: 13px;
      text-transform: uppercase;
      letter-spacing: 0.5px;
    }
    th:first-child { border-radius: 10px 0 0 10px; }
    th:last-child { border-radius: 0 10px 10px 0; }
    td { padding: 12px 14px; border-bottom: 1px solid #f6dce8; font-size: 14px; vertical-align: top; }
    tr:hover td { background: var(--rose-pale); }
    .badge {
      display: inline-block;
      padding: 4px 12px;
      border-radius: 14px;
      font-size: 12px;
      font-weight: 600;
    }
    .oui { background: #e0f7ec; color: #1b8a5a; }
    .non { background: #ffe3e3; color: #c62828; }
    .categorie { background: var(--rose-clair); color: var(--rose-fonce); }
    select.statut {
      border: 0;
      border-radius: 14px;
      padding: 6px 12px;
      font-weight: 600;
      font-size: 13px;
      cursor: pointer;
    }
    select.prep    { background: #fff1d6; color: #b36b00; }
    select.prete   { background: #e3efff; color: #1a56b0; }
    select.livree  { background: #e0f7ec; color: #1b8a5a; }
    select.annulee { background: #ffe3e3; color: #c62828; }
    form.ajout { margin-bottom: 22px; padding: 18px; background: var(--rose-pale); border-radius: 14px; }
    .ligne-client { display: flex; gap: 10px; flex-wrap: wrap; margin-bottom: 14px; }
    .titre-commande { font-weight: 700; color: var(--rose-fonce); margin: 6px 0 10px; }
    .plats-choix {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
      gap: 10px;
      margin-bottom: 16px;
    }
    .plat-choix {
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 8px;
      background: white;
      border: 2px solid var(--rose-clair);
      border-radius: 12px;
      padding: 8px 12px;
      font-size: 14px;
    }
    .plat-choix input { width: 64px; padding: 6px 8px; }
    input {
      padding: 10px 14px;
      border: 2px solid var(--rose-clair);
      border-radius: 12px;
      font-size: 14px;
      outline: none;
    }
    input:focus { border-color: var(--rose); }
    button {
      background: linear-gradient(135deg, #ff6fb5, var(--rose-fonce));
      color: white;
      border: 0;
      padding: 10px 22px;
      border-radius: 12px;
      font-weight: 600;
      cursor: pointer;
    }
    button:hover { opacity: 0.9; }
    footer { text-align: center; color: #a98a9a; font-size: 13px; padding: 20px; }
  </style>
</head>
<body>

  <header>
    <h1>🌸 Application de gestion du restaurant 🌸 </h1>
  </header>

  <nav>
    <a href="#clients">👥 Clients</a>
    <a href="#plats">🍽️ Plats</a>
    <a href="#commandes">🧾 Commandes</a>
  </nav>

  <main>
    <div class="stats">
      <div class="card"><div class="icone">👥</div><div><div class="valeur">{{ clients|length }}</div><div class="label">Clients</div></div></div>
      <div class="card"><div class="icone">🍽️</div><div><div class="valeur">{{ plats|length }}</div><div class="label">Plats</div></div></div>
      <div class="card"><div class="icone">🧾</div><div><div class="valeur">{{ commandes|length }}</div><div class="label">Commandes</div></div></div>
      <div class="card"><div class="icone">💰</div><div><div class="valeur">{{ ca }} DH</div><div class="label">Chiffre d'affaires (livrées)</div></div></div>
    </div>

    <section id="clients">
      <h2>👥 Clients</h2>

      <form class="ajout" method="post" action="{{ url_for('ajouter_client') }}">
        <div class="ligne-client">
          <input name="nom" placeholder="Nom du client" required>
          <input name="ville" placeholder="Ville" required>
        </div>

        <div class="titre-commande">🧾 Commande du client (quantité 0 = non choisi)</div>
        <div class="plats-choix">
          {% for p in plats if p["disponible"] %}
          <label class="plat-choix">
            <span>{{ p["nom"] }} <b>({{ p["prix"] }} DH)</b></span>
            <input type="number" name="qte_{{ p['plat_id'] }}" min="0" max="20" value="0">
          </label>
          {% endfor %}
        </div>

        <button type="submit">+ Ajouter le client et sa commande</button>
      </form>

      <div class="table-wrap">
        <table>
          <tr><th>ID</th><th>Nom</th><th>Ville</th><th>Ce qu'il a commandé</th></tr>
          {% for c in clients %}
          <tr>
            <td>#{{ c["client_id"] }}</td>
            <td>{{ c["nom"] }}</td>
            <td>📍 {{ c["ville"] }}</td>
            <td>
              {% for cmd in cmd_clients.get(c["client_id"], []) %}
              <div style="margin-bottom:6px">
                <b>#{{ cmd["commande_id"] }}</b> :
                {% for l in cmd["plats"] %}{{ noms_plats.get(l["plat_id"], "?") }} ×{{ l["quantite"] }}{% if not loop.last %}, {% endif %}{% endfor %}
                — <b>{{ cmd["total"] }} DH</b> ({{ cmd["statut"] }})
              </div>
              {% else %}
              <i>Aucune commande</i>
              {% endfor %}
            </td>
          </tr>
          {% endfor %}
        </table>
      </div>
    </section>

    <section id="plats">
      <h2>🍽️ Plats</h2>
      <div class="table-wrap">
        <table>
          <tr><th>ID</th><th>Nom</th><th>Catégorie</th><th>Prix</th><th>Disponibilité</th></tr>
          {% for p in plats %}
          <tr>
            <td>#{{ p["plat_id"] }}</td>
            <td>{{ p["nom"] }}</td>
            <td><span class="badge categorie">{{ p["categorie"] }}</span></td>
            <td><b>{{ p["prix"] }} DH</b></td>
            <td>
              {% if p["disponible"] %}<span class="badge oui">Disponible</span>
              {% else %}<span class="badge non">Indisponible</span>{% endif %}
            </td>
          </tr>
          {% endfor %}
        </table>
      </div>
    </section>

    <section id="commandes">
      <h2>🧾 Commandes</h2>
      <div class="table-wrap">
        <table>
          <tr><th>ID</th><th>Client</th><th>Plats commandés</th><th>Total</th><th>Statut</th></tr>
          {% for c in commandes %}
          <tr>
            <td>#{{ c["commande_id"] }}</td>
            <td>{{ noms_clients.get(c["client_id"], "?") }}</td>
            <td>{% for l in c["plats"] %}{{ noms_plats.get(l["plat_id"], "?") }} ×{{ l["quantite"] }}{% if not loop.last %}, {% endif %}{% endfor %}</td>
            <td><b>{{ c["total"] }} DH</b></td>
            <td>
              <form method="post" action="{{ url_for('changer_statut', commande_id=c['commande_id']) }}" style="margin:0">
                <select name="statut" class="statut {{ classes[c['statut']] }}" onchange="this.form.submit()">
                  {% for s in statuts %}
                  <option value="{{ s }}" {{ "selected" if s == c["statut"] }}>{{ s }}</option>
                  {% endfor %}
                </select>
              </form>
            </td>
          </tr>
          {% endfor %}
        </table>
      </div>
    </section>
  </main>

  <footer>🌸 APP : gestion du restaurant  — projet Docker : MongoDB + Mongo Express + Python</footer>
</body>
</html>
"""


@app.route("/")
def index():
    clients = list(db.clients.find({}, {"_id": 0}).sort("client_id", 1))
    plats = list(db.plats.find({}, {"_id": 0}).sort("plat_id", 1))
    commandes = list(db.commandes.find({}, {"_id": 0}).sort("commande_id", 1))
    noms_clients = {c["client_id"]: c["nom"] for c in clients}
    noms_plats = {p["plat_id"]: p["nom"] for p in plats}
    ca = sum(c["total"] for c in commandes if c["statut"] == "Livrée")

    # Commandes regroupées par client (colonne "Ce qu'il a commandé")
    cmd_clients = {}
    for cmd in commandes:
        cmd_clients.setdefault(cmd["client_id"], []).append(cmd)

    return render_template_string(
        PAGE, clients=clients, plats=plats, commandes=commandes,
        noms_clients=noms_clients, noms_plats=noms_plats,
        statuts=STATUTS, classes=CLASSES_STATUT, ca=ca,
        cmd_clients=cmd_clients,
    )


@app.route("/clients/ajouter", methods=["POST"])
def ajouter_client():
    # 1. Création du client
    dernier = db.clients.find_one(sort=[("client_id", -1)])
    nouvel_id = (dernier["client_id"] + 1) if dernier else 1
    db.clients.insert_one({
        "client_id": nouvel_id,
        "nom": request.form["nom"].strip(),
        "ville": request.form["ville"].strip(),
    })

    # 2. Création de sa commande (seulement les plats disponibles avec quantité > 0)
    lignes = []
    total = 0
    for plat in db.plats.find({"disponible": True}).sort("plat_id", 1):
        try:
            quantite = int(request.form.get(f"qte_{plat['plat_id']}", "0"))
        except ValueError:
            quantite = 0
        if quantite > 0:
            lignes.append({"plat_id": plat["plat_id"], "quantite": quantite})
            total += plat["prix"] * quantite

    if lignes:
        derniere = db.commandes.find_one(sort=[("commande_id", -1)])
        nouvelle_commande_id = (derniere["commande_id"] + 1) if derniere else 1
        db.commandes.insert_one({
            "commande_id": nouvelle_commande_id,
            "client_id": nouvel_id,
            "plats": lignes,
            "total": total,
            "statut": "En préparation",
        })
    return redirect(url_for("index"))


@app.route("/commandes/<int:commande_id>/statut", methods=["POST"])
def changer_statut(commande_id):
    statut = request.form["statut"]
    if statut in STATUTS:
        db.commandes.update_one({"commande_id": commande_id}, {"$set": {"statut": statut}})
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)