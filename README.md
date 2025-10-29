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

4) Create (.env) file and copy content from (.env.example) following the configuration instructions
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

## Deployment to Render

### Prerequisites
- GitHub account with the AgriLink repository
- Render account (sign up at https://render.com)

### Steps

1. **Prepare your repository**
   - Ensure all changes are committed and pushed to GitHub
   - The repository should contain: `Procfile`, `requirements.txt`, `build.sh`

2. **Create PostgreSQL Database on Render**
   - Log in to Render Dashboard
   - Click "New +" → "PostgreSQL"
   - Choose database name, region, and plan
   - Click "Create Database"
   - Wait for the database to be provisioned
   - Copy the "Internal Database URL" (will be used as DATABASE_URL)

3. **Create Web Service**
   - In Render Dashboard, click "New +" → "Web Service"
   - Connect your GitHub repository (authorize if needed)
   - Select the `CSIT327-G7-12-AgriLink` repository
   - Configure the service:
     - **Name**: agrilink (or your preferred name)
     - **Environment**: Python 3
     - **Build Command**: `./build.sh`
     - **Start Command**: `gunicorn agrilink_project.wsgi`
     - **Instance Type**: Free tier or higher

4. **Configure Environment Variables**
   Click "Advanced" and add the following environment variables:
   
   ```env
   SECRET_KEY=your-generated-secret-key
   DEBUG=False
   ALLOWED_HOSTS=agrilink.onrender.com
   DATABASE_URL=<Internal Database URL from step 2>
   ```
   
   To generate a SECRET_KEY, run:
   ```bash
   python -c "from django.core.management.utils import get_random_secret_key as g; print(g())"
   ```

5. **Deploy**
   - Click "Create Web Service"
   - Render will automatically build and deploy your application
   - Wait for the deployment to complete (typically 3-5 minutes)
   - Your app will be available at: `https://agrilink.onrender.com` (replace with your service name)

6. **Update Deployed Link**
   - Copy the deployed URL and update the "Deployed Link" section below

### Post-Deployment

- The first deployment will take longer as it installs dependencies
- You may need to create a superuser account by running:
  ```bash
  python manage.py createsuperuser
  ```
- Monitor logs in the Render Dashboard for any issues
- Static files are automatically served via WhiteNoise
- Media files uploaded by users will be stored in Render's ephemeral filesystem (reset on each deploy)

### Troubleshooting

- Check the build logs if deployment fails
- Verify all environment variables are set correctly
- Ensure DATABASE_URL format is correct (postgresql://...)
- Check ALLOWED_HOSTS includes your Render URL

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
