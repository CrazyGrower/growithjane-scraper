#!/bin/bash

# Mettre à jour la liste des paquets et installer Chromium manuellement
apt-get update && apt-get install -y chromium

# Désactiver l'installation automatique des navigateurs Playwright
export PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=1

# Définir le chemin du navigateur manuellement pour éviter les erreurs
export PLAYWRIGHT_BROWSERS_PATH=/usr/bin

# Vérifier si Chromium est bien installé
which chromium

# Démarrer l'application FastAPI
uvicorn src.web_interface:app --host 0.0.0.0 --port $PORT
