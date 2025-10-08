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
git clone https://github.com/DeonHolo/CSIT327-G7-12-AgriLink.git
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

4) Configure environment (.env) - Create (.env) file and copy content from (.env.example) following the configuration instructions
```env
# Generate Secret Key with: python -c "from django.core.management.utils import get_random_secret_key as g; print(g())"
SECRET_KEY=
# Set DEBUG to 'False' in production
DEBUG=True
# Comma-separated list of allowed hosts (e.g., localhost,127.0.0.1,AgriLink.com)
ALLOWED_HOSTS=localhost,127.0.0.1
# For Supabase PostgreSQL (DATABASE_URL=): Supabase Dashboard → Your Project → Connect → Connection String → Session Pooler
# For Supabase PostgreSQL (DATABASE_URL=): Or check pinned message in Teams chat for Supabase key
# Optional for PostgreSQL (leave empty to use SQLite locally for development)
DATABASE_URL=
```

5) Apply migrations and run
```bash
python manage.py migrate
python manage.py runserver
```

## Team Members

| Name                              | Role               | CIT-U Email                            |
| :-------------------------------- | :-----------------:| --------------------------------------:|
| Jay Yan Tiongzon                  | Product Owner      | jayyan.tiongzon@cit.edu                |
| James Michael Siton               | Business Analyst   | jamesmichael.siton@cit.edu             |
| Franz Raven Sanchez               | Scrum Master       | franzraven.sanchez@cit.edu             |
| Ron Luigi Taghoy                  | Lead Developer     | ronluigi.taghoy@cit.edu                |
| Jusfer Jay Orge                   | Frontend Developer | jusferjay.orge@cit.edu                 |
| Harvey Rod Christian Valmera      | Backend Developer  | harveyrodchristian.valmera@cit.edu     |

## Deployed Link

Not available yet
