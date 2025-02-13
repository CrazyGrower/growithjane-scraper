# GrowLog Scraper 🌱

Un outil simple pour extraire vos journaux de culture depuis GrowWithJane et générer un rapport PDF détaillé.

## 🚀 Caractéristiques

- Extraction automatique de votre journal GrowWithJane
- Génération d'un PDF propre avec vos photos et actions
- Suivi de la progression (germination, croissance, etc.)
- Support du mode headless (pas d'interface graphique)
- Historique complet des arrosages et nutriments
- Formatage automatique des dates et durées

## 📋 Prérequis

Avant d'installer le script, assurez-vous d'avoir :

- Python 3.x installé
- Google Chrome installé
- ChromeDriver compatible avec votre version de Chrome ([télécharger ici](https://sites.google.com/chromium.org/driver/))
- Un accès internet

## 💾 Installation

1. **Clonez le repository**
```bash
git clone https://github.com/votre-username/growithjane-scraper.git
cd growithjane-scraper
```

2. **Créez un environnement virtuel**
```bash
# Sur Linux/macOS
python3 -m venv venv
source venv/bin/activate

# Sur Windows
python -m venv venv
venv\Scripts\activate
```

3. **Installez les dépendances**
```bash
pip install -r requirements.txt
```

4. **Configuration**
```bash
cp .env.example .env
```

Éditez le fichier `.env` et configurez vos variables :
```plaintext
# URL de votre grow log sur GrowWithJane
GROWLOG_URL=https://growithjane.com/growlog/growlog-exemple/

# Chemin vers votre ChromeDriver
CHROMEDRIVER_PATH=/path/to/chromedriver
```

**Note importante :** 
- Remplacez `growlog-exemple` dans l'URL par l'identifiant de votre grow log
- Remplacez `/path/to/chromedriver` par le chemin réel vers votre ChromeDriver :
  - Sur macOS (avec Homebrew) : généralement `/opt/homebrew/bin/chromedriver`
  - Sur Linux : utilisez `which chromedriver` pour trouver le chemin
  - Sur Windows : utilisez `where chromedriver` puis copiez le chemin complet

## 🎯 Utilisation

### Mode Simple
```bash
python main.py
```

### Mode Verbose (plus de détails)
```bash
python main.py -v
```

Le PDF sera généré dans le dossier courant avec le nom de votre grow log.

## 📸 Exemple de Sortie

Le PDF généré inclut :
- Une page de titre avec le nom de votre grow
- Un statut de progression (En cours/Terminé)
- Les entrées du journal avec :
  - Date et jour de culture
  - État de la plante
  - Actions (arrosage, nutriments, etc.)
  - Photos de progression

## 🔧 Dépannage

### Erreur : "chromedriver" introuvable
```
selenium.common.exceptions.WebDriverException: Message: 'chromedriver' executable needs to be in PATH
```
**Solution :** 
1. Trouvez le chemin de votre ChromeDriver :
   ```bash
   which chromedriver  # Sur Linux/macOS
   where chromedriver  # Sur Windows
   ```
2. Copiez le chemin complet dans votre fichier `.env` :
   ```plaintext
   CHROMEDRIVER_PATH=/chemin/exact/vers/chromedriver
   ```

### Erreur : "No module named 'selenium'"
**Solution :**
```bash
pip install -r requirements.txt
```

### Erreur : "Invalid URL"
**Solution :**
Vérifiez que l'URL dans votre fichier `.env` est correcte et accessible. Elle devrait ressembler à :
```plaintext
GROWLOG_URL=https://growithjane.com/growlog/votre-identifiant-unique/
```

## 📄 License

Ce projet est sous licence MIT. Voir le fichier LICENSE pour plus de détails.