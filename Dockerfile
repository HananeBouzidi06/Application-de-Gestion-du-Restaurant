# 1. FROM : image de départ (Python officiel, version légère)
FROM python:3.12-slim

# 2. WORKDIR : dossier de travail dans le conteneur
WORKDIR /app

# Affiche les print() immédiatement dans docker compose logs
ENV PYTHONUNBUFFERED=1

# 3. COPY : on copie d'abord requirements.txt (optimise le cache Docker)
COPY requirements.txt .

# 4. RUN : installation des dépendances Python (pymongo)
RUN pip install --no-cache-dir -r requirements.txt

# 3 (bis). COPY : on copie ensuite le script
COPY importer.py .
COPY app.py .

# 5. CMD : commande exécutée au démarrage du conteneur
CMD ["python", "importer.py"]