#!/bin/bash

# Désactiver l'installation automatique avec 'su'
export PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=1
export PLAYWRIGHT_BROWSERS_PATH=~/.cache/ms-playwright

# Installer les navigateurs Playwright SANS utiliser `su`
python -m playwright install --with-deps chromium

# Démarrer FastAPI avec uvicorn
uvicorn src.web_interface:app --host 0.0.0.0 --port $PORT
