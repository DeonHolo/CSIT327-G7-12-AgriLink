# AgriLink

AgriLink is a web-based platform designed to connect farmers directly with buyers, fostering a fair, transparent, and sustainable local food ecosystem.

## Features

- User Authentication (Registration & Login)
- Supabase PostgreSQL Database Integration
- Session Management
- Form Validation (Frontend & Backend)

## Tech Stack

- **Backend**: Django 5.2.6
- **Database**: Supabase (PostgreSQL)
- **Authentication**: Django Auth with custom User model

## Setup Instructions

### 1. Clone the Repository
```bash
git clone https://github.com/DeonHolo/AgriLink.git
cd AgriLink
```

### 2. Create Virtual Environment
```bash
python -m venv venv
venv\Scripts\activate  # Windows
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables
1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```

2. Generate a Django secret key:
   ```bash
   python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
   ```

3. Get your Supabase Session Pooler credentials:
   - Go to: [Supabase Dashboard](https://supabase.com/dashboard) → Your Project → Connect → Connection Info
   - Copy the **Session Pooler** connection string (not direct DB)
   - It should look like: `postgresql://postgres:PASSWORD@aws-0-PROJECTREF.pooler.supabase.com:6543/postgres?sslmode=require`

4. Update your `.env` file with:
   - `SECRET_KEY`: Paste the generated secret key
   - `DATABASE_URL`: Paste your Supabase Session Pooler connection string

### 5. Run Migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

### 6. Create Superuser (Optional)
```bash
python manage.py createsuperuser
```

### 7. Run Development Server
```bash
python manage.py runserver
```

Visit: `http://127.0.0.1:8000/`

**Note**: If you get a `SECRET_KEY` error, make sure you've properly configured your `.env` file with a valid secret key.

## Project Structure

```
AgriLink/
├── agrilink_project/      # Main project settings
│   ├── settings.py        # Django settings with Supabase config
│   └── urls.py           # Main URL routing
├── authentication/        # Authentication app
│   ├── models.py         # Custom User model
│   ├── forms.py          # Registration forms
│   ├── views.py          # Auth views (register, login, logout)
│   └── urls.py           # Auth URL routing
├── manage.py             # Django management script
├── requirements.txt      # Python dependencies
├── .env.example         # Environment variables template
├── .gitignore           # Git ignore rules
└── README.md            # This file
```

## API Endpoints

- `/auth/register/` - User registration
- `/auth/login/` - User login
- `/auth/logout/` - User logout
- `/admin/` - Django admin panel

## Database Schema

### Users Table
- `id` - Primary key
- `username` - Unique username
- `email` - Unique email
- `password` - Hashed password
- `phone_number` - Optional phone
- `is_verified` - Email verification status
- `created_at` - Timestamp
- `updated_at` - Timestamp

## Supabase Configuration

This project uses Supabase PostgreSQL via **Session Pooler** for better connection management:

### Required Packages
- `psycopg2` - PostgreSQL adapter
- `dj-database-url` - Database URL parsing
- `python-dotenv` - Environment variable loading

### Connection Setup
1. Get Session Pooler URL from Supabase Dashboard → Connect → Connection Info
2. Format: `postgresql://postgres:PASSWORD@aws-0-PROJECTREF.pooler.supabase.com:5432/postgres?sslmode=require`
3. Add to `.env` as `DATABASE_URL`

## Contributing

1. Create a new branch for your feature
2. Make your changes
3. Submit a pull request

## License

© 2025 AgriLink. All rights reserved.
