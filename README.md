
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
