# Sailing Logbook
## macOS: Application double‑clic avec icône

Objectif: démarrer le serveur Django et ouvrir le navigateur en double‑cliquant une App macOS.

Deux méthodes faciles:

1) Automator (sans dépendance externe)
- Ouvrez Automator → Nouvelle application
- Action « Exécuter un script Shell »
- Shell: /bin/zsh — Passer l’entrée: en arguments
- Script:
	- cd "${HOME}/chemin/vers/sailing_logbook/macos"
	- chmod +x launch_server.sh
	- ./launch_server.sh
- Fichier → Enregistrer sous (ex: "Sailing Logbook.app")
- Icône: faites un clic droit sur l’App → Lire les informations, glissez un fichier .icns sur l’icône en haut à gauche.

2) Platypus (packager bash en .app)
- Installez Platypus: https://sveinbjorn.org/platypus
- Create New App → Script Type: /bin/zsh
- Script Path: macos/launch_server.sh
- Interface: None (Background)
- App Name: Sailing Logbook
- Bundle Identifier: com.votre.domaine.sailinglogbook
- Icon: sélectionnez un .icns
- Advanced: cochez "Remain running after execution" si vous voulez que l’App reste ouverte (optionnel).
- Create App

Notes:
- Le script crée un virtualenv .venv, installe les dépendances, applique les migrations, ouvre http://127.0.0.1:8000 et lance le serveur.
- Pour changer le port, définissez PORT (ex: PORT=8001). Pour modifier l’adresse, changez HOST dans macos/launch_server.sh.
- Vous pouvez dupliquer l’App pour plusieurs environnements (ex: prod/dev) avec des variables d’environnement encapsulées via Platypus.


# Sailing Logbook (Django + DRF + Uploads)

## Installation
```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python manage.py makemigrations nautical
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```
- Site : http://127.0.0.1:8000/
- Admin : http://127.0.0.1:8000/admin/
- API : http://127.0.0.1:8000/api/

## Notes
- Médias: `MEDIA_URL=/media/`, fichiers dans `media/` (servis en DEBUG).
- Form “Nouvelle sortie” : widgets `datetime-local`, filtre équipage, upload cover.
