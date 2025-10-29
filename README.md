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

4) Create (.env) file with the following configuration:
```env
# Generate Secret Key with: python -c "from django.core.management.utils import get_random_secret_key as g; print(g())"
SECRET_KEY=
# Set DEBUG to 'False' in production
DEBUG=True
# Comma-separated list of allowed hosts (e.g., localhost,127.0.0.1,agrilink-q79q.onrender.com)
ALLOWED_HOSTS=localhost,127.0.0.1,agrilink-q79q.onrender.com
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

### Post-Deployment

#### Creating Admin User
To create a superuser account for accessing the Django admin panel, use Render's Shell feature:

1. Go to your Render Dashboard
2. Select your web service
3. Click on "Shell" in the sidebar
4. Run the following command:
   ```bash
   python manage.py createsuperuser
   ```
5. Follow the prompts to enter username, email, and password

#### Monitoring and Logs
- **View Logs**: Check the Render Dashboard → Your Service → Logs for real-time application logs
- **Build Logs**: Review build logs for any deployment issues
- **Health Checks**: Render automatically monitors your service health

#### Static and Media Files
- **Static Files**: Served automatically via WhiteNoise middleware (CSS, JS, images)
- **Media Files**: User-uploaded files are stored in Render's ephemeral filesystem
  - ⚠️ **Important**: Files in the media directory are reset on each deployment
  - For production, consider using cloud storage (AWS S3, Cloudinary, etc.)

#### Database Management
- **Migrations**: Automatically run during deployment via `build.sh`
- **Manual Migrations**: If needed, use Render Shell:
  ```bash
  python manage.py migrate
  ```
- **Database Backups**: Configure automatic backups in Render Dashboard for paid plans
- **Supabase**: Database is hosted on Supabase (PostgreSQL)

#### Deployment Workflow
1. Make changes to the code
2. Commit and push to GitHub (deploy/render-setup branch)
3. Render automatically detects changes and deploys
4. Monitor logs for deployment status
5. Test the live site after successful deployment

#### Troubleshooting

**Build Fails**
- Check build logs for error messages
- Verify all dependencies in `requirements.txt`
- Ensure `build.sh` has executable permissions

**Application Fails to Start**
- Verify environment variables are set correctly
- Check that `DATABASE_URL` format is correct
- Ensure `ALLOWED_HOSTS` includes your Render URL

**Database Connection Errors**
- Verify `DATABASE_URL` is correct
- Check Supabase connection pooling settings
- Ensure IP whitelist allows Render's IPs (if applicable)

**Static Files Not Loading**
- WhiteNoise should handle static files automatically
- Run `python manage.py collectstatic` manually if needed

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

🌐 **Live Application**: [agrilink-q79q.onrender.com](https://agrilink-q79q.onrender.com)
