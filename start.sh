#!/bin/bash

# Définir le chemin des navigateurs Playwright
export PLAYWRIGHT_BROWSERS_PATH=~/.cache/ms-playwright

# Installer les navigateurs Playwright (sans `--target`)
playwright install --with-deps

# Démarrer l'application FastAPI avec uvicorn
uvicorn src.web_interface:app --host 0.0.0.0 --port $PORT
