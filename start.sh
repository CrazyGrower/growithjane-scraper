#!/bin/bash

# Désactiver toute tentative de Playwright d'installer Chromium avec 'su'
export PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=1
export PLAYWRIGHT_BROWSERS_PATH=~/.cache/ms-playwright

# Installer Chromium manuellement dans Render
npx playwright install chromium --with-deps

# Lancer FastAPI avec uvicorn
uvicorn src.web_interface:app --host 0.0.0.0 --port $PORT
