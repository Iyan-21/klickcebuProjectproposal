# KlickCebu — Camera Rental System

A Django-based web platform for renting cameras and photography gear in Cebu. Built as part of CSIT327.

## Tech Stack

- **Language:** Python
- **Framework:** Django
- **Frontend:** HTML, CSS (custom theme), Bootstrap-based structure
- **Database:** PostgreSQL via [Supabase](https://supabase.com)
- **Auth:** Custom user model (email-based login)
- **Version Control:** Git & GitHub
- **Deployment (planned):** Render or PythonAnywhere

## Features

- User registration with duplicate-email prevention
- User login/logout with custom email-based authentication
- Custom Admin Dashboard (built from scratch, not Django's default admin)
- Live stats: total users, cameras listed, total bookings
- Camera and booking models (in progress)

## Project Structure
klickcebu/
├── accounts/       # Registration, login, logout, custom User model
├── dashboard/      # Custom admin dashboard
├── rentals/        # Camera and booking models
├── config/         # Project settings, URLs
├── static/css/     # Shared theme (theme.css)
├── templates/      # Shared base template
├── requirements.txt
└── manage.py


## Setup Instructions

### 1. Clone the repository

```bash
git clone https://github.com/Iyan-21/klickcebuProjectproposal.git
cd klickcebuProjectproposal
```

### 2. Create and activate a virtual environment

**Windows (PowerShell):**
```bash
python -m venv venv
.\venv\Scripts\Activate.ps1
```

**Mac/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

> If you're using PyCharm, you can instead go to **File → Settings → Project → Python Interpreter → Add Interpreter → Virtualenv Environment → New**, and PyCharm will create and activate it automatically in new terminal tabs.

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Set up environment variables

Create a `.env` file in the project root (same folder as `manage.py`) with the following:
SECRET_KEY=your-django-secret-key
DEBUG=True
DATABASE_URL=your-supabase-connection-string
> Get your Supabase connection string from your project dashboard → **Connect** → **Server** tab → **Session pooler**. Replace `[YOUR-PASSWORD]` with your actual database password.
>
> ⚠️ `.env` is excluded via `.gitignore` and should never be committed — it contains real credentials.

### 5. Run migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

### 6. Run the development server

```bash
python manage.py runserver
```

Visit `http://127.0.0.1:8000/accounts/register/` to create an account, or `http://127.0.0.1:8000/accounts/login/` to log in.

## Notes

- The default Django admin panel is disabled in favor of a custom-built dashboard at `/dashboard/`.
- Passwords are hashed automatically by Django's authentication system (PBKDF2-SHA256) — never stored in plain text.

## Author

Ian Joreim Abesia — CSIT327-GO1
