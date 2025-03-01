#!/bin/bash

# Désactiver l'utilisation de 'su' pour installer Playwright
export PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=1

# Définir le dossier utilisateur pour les navigateurs Playwright
export PLAYWRIGHT_BROWSERS_PATH=~/.cache/ms-playwright

# Installer les navigateurs dans le dossier utilisateur (sans root)
playwright install chromium --with-deps

# Démarrer l'application FastAPI
uvicorn src.web_interface:app --host 0.0.0.0 --port $PORT
