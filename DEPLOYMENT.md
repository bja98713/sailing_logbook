# Déploiement sur PythonAnywhere

Guide pour déployer le Sailing Logbook sur PythonAnywhere.

## Prérequis
- Compte PythonAnywhere (gratuit ou payant)
- Code source prêt (ce repo GitHub)

## Étape 1: Upload du code

### Option A: Via Git (recommandé)
```bash
# Dans le terminal PythonAnywhere (Bash console)
cd ~
git clone https://github.com/bja98713/sailing_logbook.git
cd sailing_logbook
```

### Option B: Via l'interface Files
- Télécharge le ZIP depuis GitHub
- Upload via Files → Upload a file
- Extrait dans `/home/yourusername/sailing_logbook/`

## Étape 2: Configuration de l'environnement virtuel

```bash
# Dans la Bash console PythonAnywhere
cd ~/sailing_logbook
python3.10 -m venv .venv
source .venv/bin/activate

# Installation des dépendances
pip install --upgrade pip
pip install -r requirements.txt
```

## Étape 3: Configuration Django

### Variables d'environnement
Créer `~/sailing_logbook/.env`:
```bash
SECRET_KEY=f7!_z@y(uu45sl#8m5061gdoa(j++db3o42j6g)osb9wo3)lys
DEBUG=False
ALLOWED_HOSTS=terry98713.pythonanywhere.com
DATABASE_URL=sqlite:////home/yourusername/sailing_logbook/db.sqlite3
```

### Mise à jour de settings.py
Ajouter en haut de `sailing_logbook/settings.py`:
```python
import os
from pathlib import Path

# Load environment variables
if os.path.exists('.env'):
    with open('.env', 'r') as f:
        for line in f:
            if '=' in line:
                key, value = line.strip().split('=', 1)
                os.environ.setdefault(key, value)

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-CHANGE-THIS')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get('DEBUG', 'False').lower() == 'true'

ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', 'localhost').split(',')
```

### Migrations et collectstatic
```bash
cd ~/sailing_logbook
source .venv/bin/activate

python manage.py migrate
python manage.py collectstatic --noinput
python manage.py createsuperuser  # optionnel
```

## Étape 4: Configuration Web App

### Création de l'application web
1. Dashboard PythonAnywhere → Web
2. "Add a new web app"
3. Choose "Manual configuration"
4. Python version: 3.10
5. Next

### Configuration WSGI
Éditer `/var/www/terry98713_pythonanywhere_com_wsgi.py`:

```python
import os
import sys

# Ajouter le chemin du projet
path = '/home/terry98713/sailing_logbook'
if path not in sys.path:
    sys.path.insert(0, path)

# Méthode moderne pour activer l'environnement virtuel (Python 3.10+)
venv_path = '/home/terry98713/sailing_logbook/.venv'
site_packages = os.path.join(venv_path, 'lib', 'python3.10', 'site-packages')
sys.path.insert(0, site_packages)

# Configuration Django
os.environ['DJANGO_SETTINGS_MODULE'] = 'sailing_logbook.settings'

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
```

**Alternative si la méthode ci-dessus ne fonctionne pas:**
```python
import os
import sys

# Ajouter le chemin du projet
path = '/home/terry98713/sailing_logbook'
if path not in sys.path:
    sys.path.insert(0, path)

# Utiliser directement le virtualenv via le dashboard PythonAnywhere
# (Configure le virtualenv dans l'onglet Web au lieu du code WSGI)

# Configuration Django
os.environ['DJANGO_SETTINGS_MODULE'] = 'sailing_logbook.settings'

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
```

### Configuration des chemins (Web tab)
- **Source code:** `/home/yourusername/sailing_logbook`
- **Working directory:** `/home/yourusername/sailing_logbook`
- **Virtualenv:** `/home/yourusername/sailing_logbook/.venv`

### Fichiers statiques
Dans l'onglet Web → Static files:
- **URL:** `/static/`
- **Directory:** `/home/yourusername/sailing_logbook/static`

Si tu as des fichiers média:
- **URL:** `/media/`
- **Directory:** `/home/yourusername/sailing_logbook/media`

## Étape 5: Finalisation

1. Recharger l'application web (bouton "Reload" dans Web tab)
2. Visiter `https://yourusername.pythonanywhere.com`
3. Tester la création d'un voyage et l'export PDF

## Mise à jour du code

### Récupérer depuis GitHub vers PythonAnywhere
```bash
cd ~/sailing_logbook
git pull origin main
source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput
# Recharger l'app web dans le dashboard
```

### Pousser depuis PythonAnywhere vers GitHub
Si tu as fait des modifications directement sur PythonAnywhere :

```bash
cd ~/sailing_logbook
git add -A
git commit -m "Description des modifications"
git push origin main
```

**Important :** Pour pousser vers GitHub depuis PythonAnywhere, tu dois configurer l'authentification :

1. **Avec un token GitHub (recommandé) :**
   ```bash
   # Première fois seulement - configure ton nom/email
   git config --global user.name "Ton Nom"
   git config --global user.email "ton.email@exemple.com"
   
   # Utilise un Personal Access Token au lieu du mot de passe
   # Génère le token sur GitHub : Settings → Developer settings → Personal access tokens
   git push origin main
   # Quand demandé, utilise ton token comme mot de passe
   ```

2. **Ou configurer une clé SSH :**
   ```bash
   # Génère une clé SSH sur PythonAnywhere
   ssh-keygen -t rsa -b 4096 -C "ton.email@exemple.com"
   cat ~/.ssh/id_rsa.pub
   # Copie la clé publique et ajoute-la à ton compte GitHub
   # GitHub Settings → SSH and GPG keys → New SSH key
   ```

### Sur ton ordinateur local (macOS)
Pour récupérer les dernières modifications depuis GitHub vers ton Mac :

```bash
cd /Users/bronstein/sailing_logbook
git pull origin main

# Si tu as des nouvelles dépendances
source .venv/bin/activate
pip install -r requirements.txt

# Si il y a de nouvelles migrations
python manage.py migrate
```

### Workflow complet (développement)
1. **Développer localement** sur ton Mac
2. **Tester** : `python manage.py runserver`
3. **Commiter et pousser** : 
   ```bash
   git add -A
   git commit -m "Description des changements"
   git push origin main
   ```
4. **Mettre à jour PythonAnywhere** avec les commandes ci-dessus

## Dépannage

### Logs d'erreur
- Dashboard → Web → Log files
- Error log: `/var/log/yourusername.pythonanywhere.com.error.log`
- Server log: `/var/log/yourusername.pythonanywhere.com.server.log`

### Erreurs communes
1. **ImportError:** Vérifier le chemin virtualenv et WSGI
2. **Static files 404:** Vérifier la configuration Static files
3. **Database errors:** Vérifier les permissions sur db.sqlite3
4. **ALLOWED_HOSTS:** Ajouter votre domaine pythonanywhere.com

### Base de données
```bash
# Sauvegarde
cd ~/sailing_logbook
python manage.py dumpdata > backup.json

# Restauration
python manage.py loaddata backup.json
```

## Limitations compte gratuit
- 1 web app
- Pas de HTTPS custom domain
- CPU seconds limités
- Pas de tâches programmées

## Optimisations production
- Configurer HTTPS si compte payant
- Ajouter un domaine custom
- Configurer les logs Django
- Optimiser les requêtes DB
- Mettre en place des sauvegardes automatiques