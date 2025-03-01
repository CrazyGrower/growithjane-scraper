#!/bin/bash

# Détection de l'OS
OS="$(uname -s)"

# Vérification de Python
if ! command -v python3 &> /dev/null; then
    echo "Python3 non trouvé. Installation en cours..."
    if [[ "$OS" == "Linux" ]]; then
        sudo apt update && sudo apt install -y python3 python3-venv python3-pip
    elif [[ "$OS" == "Darwin" ]]; then
        brew install python3
    elif [[ "$OS" == "MINGW"* || "$OS" == "MSYS"* ]]; then
        echo "Veuillez installer Python manuellement depuis https://www.python.org/downloads/"
        exit 1
    else
        echo "Système non supporté."
        exit 1
    fi
else
    echo "Python3 est déjà installé."
fi

# Création et activation de l'environnement virtuel
python3 -m venv venv
source venv/bin/activate || source venv/Scripts/activate

# Installation des dépendances
pip install --upgrade pip
pip install -r requirements.txt
playwright install

# Lancer l'application
python main.py
