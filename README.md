# AgriLink 

AgriLink is a web-based platform designed to connect farmers directly with buyers, fostering a fair, transparent, and sustainable local food ecosystem.

## Features

- **User Authentication**: Registration, login, logout with role-based access (Farmer/Buyer)
- **Dynamic Database**: Automatic switching between SQLite (local) and Supabase PostgreSQL (production)
- **Responsive Design**: Modern Bootstrap 5 UI
- **Security**: CSRF protection, secure password validation, and environment-based configuration
- **Session Management**: Persistent user sessions with remember me functionality
- **Form Validation**: Both frontend and backend validation with user feedback

## Tech Stack

- **Backend**: Django 5.2.6
- **Database**: SQLite (development) / Supabase PostgreSQL (production)
- **Frontend**: Bootstrap 5, Bootstrap Icons, HTML5/CSS3/JavaScript
- **Authentication**: Django Auth with custom User model
- **Configuration**: python-decouple for environment variables

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

2. Edit `.env` with your settings:
   ```env
   SECRET_KEY=your-secret-key-here
   DEBUG=False
   ALLOWED_HOSTS=localhost,127.0.0.1
   
   # For Supabase PostgreSQL: Supabase Dashboard → Your Project → Connect → Connection Info (Or check pinned message in Teams chat for Supabase key) (optional - leave empty to use SQLite, recommended for development testing)
   DATABASE_URL=postgresql://user:password@host:port/database
   ```

3. Generate a new SECRET_KEY:
   ```python
   python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
   ```

### 5. Run Migrations
```bash
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

## Database Configuration

The project automatically handles database switching:

- **Without DATABASE_URL**: Uses SQLite (`db.sqlite3`) for local development
- **With DATABASE_URL**: Uses PostgreSQL (Supabase) for production

To use Supabase:
1. Get Session Pooler URL from Supabase Dashboard → Connect → Connection Info (Or check pinned message in Teams chat for Supabase key)
2. Format: postgresql://postgres:PASSWORD@aws-0-PROJECTREF.pooler.supabase.com:5432/postgres?sslmode=require
3. Add to .env as DATABASE_URL

## URL Routes

### Public Routes
- `/` - Home (redirects to landing for guests, dashboard for users)
- `/landing/` - Marketing/About page
- `/auth/register/` - User registration
- `/auth/register/farmer/` - Farmer registration
- `/auth/register/buyer/` - Buyer registration
- `/auth/login/` - User login
- `/auth/password-reset/` - Password reset

### Protected Routes
- `/` - User dashboard (when authenticated)
- `/auth/logout/` - User logout
- `/admin/` - Django admin panel

## User Model

### Custom User Fields
- `id` - Primary key
- `username` - Unique username
- `email` - Unique email
- `password` - Hashed password
- `phone_number` - Optional phone number
- `user_type` - Role: 'farmer', 'buyer', or 'both'
- `is_verified` - Email verification status
- `created_at` - Account creation timestamp
- `updated_at` - Last update timestamp

### Helper Methods
- `is_farmer()` - Returns True if user is farmer or both
- `is_buyer()` - Returns True if user is buyer or both

## Security

- All sensitive data is stored in environment variables
- CSRF protection enabled
- Secure password validation
- Session-based authentication
- SQL injection protection through Django ORM

## License

© 2025 AgriLink. All rights reserved.

