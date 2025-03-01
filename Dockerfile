# 1️⃣ Utiliser une image de base Python avec Playwright préinstallé
FROM mcr.microsoft.com/playwright/python:v1.41.0-focal

# 2️⃣ Définir le répertoire de travail
WORKDIR /app

# 3️⃣ Copier les fichiers de ton projet dans le conteneur
COPY . /app

# 4️⃣ Installer les dépendances Python
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# 5️⃣ Exposer le port 8000 pour Render
EXPOSE 8000

# 6️⃣ Démarrer l'application avec Uvicorn
CMD ["uvicorn", "src.web_interface:app", "--host", "0.0.0.0", "--port", "8000"]
