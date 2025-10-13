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
Éditer `/var/www/yourusername_pythonanywhere_com_wsgi.py`:

```python
import os
import sys

# Ajouter le chemin du projet
path = '/home/yourusername/sailing_logbook'
if path not in sys.path:
    sys.path.insert(0, path)

# Activer l'environnement virtuel
activate_this = '/home/yourusername/sailing_logbook/.venv/bin/activate_this.py'
with open(activate_this) as f:
    exec(f.read(), dict(__file__=activate_this))

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

```bash
cd ~/sailing_logbook
git pull origin main
source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput
# Recharger l'app web dans le dashboard
```

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