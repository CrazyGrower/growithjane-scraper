# GrowLog Scraper 🌱

Un outil simple pour extraire vos journaux de culture de GrowWithJane et générer un rapport PDF détaillé ainsi qu'une vidéo récapitulative.

## 🚀 Fonctionnalités

- Interface web pour une saisie facile des URLs et des options
- Extraction automatique de votre journal GrowWithJane
- Génération de PDF propre avec vos photos et actions
- Génération optionnelle d'une vidéo récapitulative de croissance
- Suivi de la progression (germination, croissance, etc.)
- Historique complet des arrosages et nutriments 
- Formatage automatique des dates et durées

## 📂 Structure du Projet

```
growithjane-scraper/
├── src/                    # Code source
│   ├── __init__.py        # Initialisation du package
│   ├── scraper.py         # Fonctionnalités de scraping
│   ├── pdf_generator.py   # Génération de PDF
│   ├── video_generator.py # Génération de vidéo
│   ├── web_interface.py   # Interface web
│   └── utils.py           # Fonctions utilitaires
├── static/                # Fichiers statiques pour l'interface web
│   └── css/              
│       └── style.css
├── templates/             # Templates HTML
│   ├── index.html        # Template interface web
│   └── template.html     # Template PDF
├── output/               # Fichiers générés
│   ├── *.pdf            # PDFs générés
│   └── *.mp4            # Vidéos générées
├── tests/                # Fichiers de test
│   ├── __init__.py
│   ├── test_scraper.py
│   └── test_pdf_generator.py
├── .gitignore           # Règles git ignore
├── LICENSE              # Licence MIT
├── README.md           # Ce fichier
└── requirements.txt    # Dépendances Python
```

## 📋 Prérequis

Avant d'installer le script, assurez-vous d'avoir :

- Python 3.x installé
- Accès Internet

## 💾 Installation

1. **Cloner le dépôt**
```bash
git clone https://github.com/your-username/growithjane-scraper.git
cd growithjane-scraper
```

2. **Créer un environnement virtuel**
```bash
# Sur Linux/macOS
python3 -m venv venv
source venv/bin/activate

# Sur Windows
python -m venv venv
venv\Scripts\activate
```

3. **Installer les dépendances**
```bash
pip install -r requirements.txt
playwright install
```

## 🎯 Utilisation

1. **Démarrer le serveur web**
```bash
python main.py
```

2. **Accéder à l'interface web**
- Ouvrez votre navigateur et allez sur `http://localhost:8000`
- Entrez votre URL GrowWithJane au format : `https://growithjane.com/growlog/votre-id-de-growlog`
- Choisissez vos options :
  - Générer une vidéo (optionnel)
  - Mode verbose pour les logs détaillés
- Cliquez sur "Générer le rapport"

Le PDF et la vidéo (si sélectionnée) seront générés dans le dossier `output`.

## 🧪 Exécution des Tests

Pour lancer la suite de tests :
```bash
python -m unittest discover tests
```

## 📸 Exemple de Sortie

Les fichiers générés incluent :

### Rapport PDF
- Une page de titre avec le nom de votre culture
- Un état d'avancement (En cours/Terminé)
- Les entrées du journal avec :
  - Date et jour de culture
  - État de la plante
  - Actions (arrosage, nutriments, etc.)
  - Photos de progression

### Vidéo Récapitulative (Optionnelle)
- Time-lapse de la progression de votre culture
- Photos datées montrant le développement de la plante
- Ajustement automatique de la durée

## 🔧 Dépannage

### Erreur : "No module named 'playwright'"
**Solution :**
```bash
pip install -r requirements.txt
playwright install
```

### Erreur : "URL invalide"
**Solution :**
Assurez-vous que votre URL suit le format correct :
```
https://growithjane.com/growlog/votre-identifiant-unique/
```

### Erreur : "Failed to launch browser"
**Solution :**
```bash
playwright install chromium
```

## 📄 Licence

Ce projet est sous licence MIT. Voir le fichier [LICENSE](LICENSE) pour plus de détails.