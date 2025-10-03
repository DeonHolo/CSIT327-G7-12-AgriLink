# AgriLink

AgriLink is a web-based platform designed to connect farmers directly with buyers, fostering a fair, transparent, and sustainable local food ecosystem.

## Features

- User Authentication (Registration & Login)
- Supabase PostgreSQL Database Integration
- Session Management
- Form Validation (Frontend & Backend)

## Tech Stack

- **Backend**: Django 5.0.6
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
1. Copy `.env.example` to `.env`
2. Update with your Supabase credentials:
   - Get credentials from: Supabase Dashboard → Settings → Database
   - Update `DB_USER`, `DB_PASSWORD`, `DB_HOST`

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
└── .env.example         # Environment variables template
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

## Contributing

1. Create a new branch for your feature
2. Make your changes
3. Submit a pull request

## License

© 2025 AgriLink. All rights reserved.
