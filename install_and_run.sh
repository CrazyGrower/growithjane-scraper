#!/bin/bash

# Détection de l'OS
OS="$(uname -s)"

# Vérification de Python
if ! command -v python3 &> /dev/null && ! command -v python &> /dev/null; then
    echo "Python n'est pas installé. Veuillez l'installer depuis https://www.python.org/downloads/ et l'ajouter au PATH."
    exit 1
fi

# Utiliser 'python' au lieu de 'python3' sous Windows
if [[ "$OS" == "MINGW"* || "$OS" == "MSYS"* ]]; then
    PYTHON=python
else
    PYTHON=python3
fi

echo "Utilisation de $PYTHON"

# Création et activation de l'environnement virtuel
$PYTHON -m venv venv
if [[ "$OS" == "MINGW"* || "$OS" == "MSYS"* ]]; then
    source venv/Scripts/activate
else
    source venv/bin/activate
fi

# Installation des dépendances
pip install --upgrade pip
pip install -r requirements.txt
pip install PyMuPDF opencv-python weasyprint pygobject  # Ajout des dépendances requises
playwright install

# Installation des bibliothèques requises sous Windows
if [[ "$OS" == "MINGW"* || "$OS" == "MSYS"* ]]; then
    echo "Installation de GTK et des bibliothèques nécessaires pour WeasyPrint..."
    
    # Récupérer l'URL de la dernière version du runtime GTK
    GTK_INSTALLER_URL=$(curl -s https://api.github.com/repos/tschoonj/GTK-for-Windows-Runtime-Environment-Installer/releases/latest | grep "browser_download_url" | cut -d '"' -f 4)

    if [[ -z "$GTK_INSTALLER_URL" ]]; then
        echo "Échec de la récupération de l'URL du GTK Installer."
        exit 1
    fi

    GTK_INSTALLER="gtk-runtime-installer.exe"
    
    curl -L -o $GTK_INSTALLER "$GTK_INSTALLER_URL"
    
    if [[ ! -f $GTK_INSTALLER ]]; then
        echo "Le fichier GTK Runtime Installer n'a pas été téléchargé correctement."
        exit 1
    fi

    chmod +x $GTK_INSTALLER
    ./$GTK_INSTALLER /S
    rm $GTK_INSTALLER
fi


# Lancer l'application
$PYTHON main.py
