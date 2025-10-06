# AgriLink

AgriLink is a web-based platform designed to connect farmers directly with buyers, fostering a fair, transparent, and sustainable local food ecosystem.

## Tech Stack

- Backend: Django 5.2.6
- Database: SQLite (dev) / PostgreSQL via Supabase (prod)
- Frontend: HTML5, CSS, JavaScript, Bootstrap Icons
- API: Django REST Framework 3.15.1
- Config/Env: python-decouple, python-dotenv
- CORS: django-cors-headers

## Setup & Run

1) Clone and enter project
```bash
git clone https://github.com/DeonHolo/AgriLink.git
cd AgriLink
```

2) Create and activate virtual environment (Windows)
```bash
python -m venv venv
venv\Scripts\activate
```

3) Install dependencies
```bash
pip install -r requirements.txt
```

4) Configure environment
```env
SECRET_KEY=<generate with: python -c "from django.core.management.utils import get_random_secret_key as g; print(g())" >
DEBUG=True (set to False in prod)
# For Supabase PostgreSQL: Supabase Dashboard → Your Project → Connect → Connection Info (Or check pinned message in Teams chat for Supabase key)
# Optional for PostgreSQL (leave empty to use SQLite locally)
DATABASE_URL=postgresql://user:password@host:port/database
```

5) Apply migrations and run
```bash
python manage.py migrate
python manage.py runserver
```

## Team Members

| Name                              | Role             | CIT-U Email                            |
| :-------------------------------- | :--------------: | --------------------------------------:|
| Jay Yan Tiongzon                  | Product Owner    | jayyan.tiongzon@cit.edu                |
| James Michael Siton               | Business Analyst | jamesmichael.siton@cit.edu             |
| Franz Raven Sanchez               | Scrum Master     | franzraven.sanchez@cit.edu             |
| Ron Luigi Taghoy                  | Developer        | ronluigi.taghoy@cit.edu                |
| Harvey Rod Christian Valmera      | Developer        | harveyrodchristian.valmera@cit.edu     |
| Jusfer Jay Orge                   | Developer        | jusferjay.orge@cit.edu                 |

## Deployed Link

Not available yet
