# InkQ Backend Setup Guide

## Prerequisites

- Python 3.9+
- PostgreSQL 12+
- Database user `inkq` with password `InkqDev2025!` and database `inkq` already created

## Quick Start

### 1. Create Environment File

Create a `.env` file in the repository root:

```env
INKQ_PG_URL=postgres://inkq:InkqDev2025!@localhost:5432/inkq
```

### 2. Install Backend Dependencies

```bash
cd backend
# (optional but recommended) create and activate virtualenv `.venv` here
pip install -r requirements.txt
```

### 3. Reset Development Database (Optional)

If you need a fresh database:

```powershell
# From repository root
$env:PGPASSWORD = "InkqDev2025!"
psql "host=localhost port=5432 dbname=inkq user=inkq" -f infra/db/reset_dev_schema.sql
```

### 4. Initialize Database

Initialize or update the database schema using the initialization script:

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
python -m app.scripts.init_db
```

This command will:
- Create all required tables from the current SQLAlchemy models
- Run any pending Alembic migrations
- Mark the database as up-to-date with Alembic

**Note:** This script is idempotent and safe to run multiple times. It will never drop existing tables or data.

### 5. Start the Backend Server

```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at:
- API: `http://localhost:8000`
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Testing

Run the test suite:

```bash
cd backend
pytest
```

## Project Structure

```
Inkq_v1.0/
├── backend/              # FastAPI backend
│   ├── app/
│   │   ├── main.py       # FastAPI app
│   │   ├── config.py     # Configuration
│   │   ├── db/           # Database setup
│   │   ├── models/       # SQLAlchemy models
│   │   ├── schemas/      # Pydantic schemas
│   │   └── routes/       # API routes
│   ├── alembic/          # Database migrations
│   └── tests/            # Test suite
├── infra/
│   └── db/
│       └── reset_dev_schema.sql  # DB reset script
├── docs/
│   └── accounts_roles.md  # Feature documentation
└── .env                  # Environment variables (create this)
```

## Common Commands

### Database

```bash
# Reset dev database
psql "host=localhost port=5432 dbname=inkq user=inkq" -f infra/db/reset_dev_schema.sql

# Initialize/update database schema (recommended)
cd backend && python -m app.scripts.init_db

# Manual migration commands (alternative to init script)
cd backend && alembic revision --autogenerate -m "Description"
cd backend && alembic upgrade head
cd backend && alembic downgrade -1
```

### Development

```bash
# Start backend
cd backend && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Run tests
cd backend && pytest

# Run tests with coverage
cd backend && pytest --cov=app
```

## API Endpoints

### POST /api/v1/auth/signup

Create a new user account.

**Request:**
```json
{
  "email": "user@example.com",
  "password": "password123",
  "username": "username",
  "account_type": "artist"
}
```

**Response (201):**
```json
{
  "id": 1,
  "email": "user@example.com",
  "username": "username",
  "account_type": "artist",
  "onboarding_completed": false,
  "created_at": "2025-11-21T00:00:00",
  "updated_at": "2025-11-21T00:00:00"
}
```

### GET /api/v1/users/me

Get current user (stub endpoint - requires authentication in production).

## Troubleshooting

### Database Connection Issues

- Verify PostgreSQL is running
- Check `INKQ_PG_URL` in `.env` file
- Ensure database `inkq` exists
- Verify user `inkq` has proper permissions

### Database Initialization

The recommended way to initialize or update your local database is:

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
python -m app.scripts.init_db
```

This script:
- Is **idempotent** - safe to run multiple times without side effects
- Creates all missing tables from SQLAlchemy models
- Runs pending Alembic migrations if needed
- Never drops existing tables or data

### Migration Issues

- Make sure database is reset before first migration
- Check that all models are imported in `alembic/env.py`
- Review generated migration file before applying
- Use `python -m app.scripts.init_db` instead of manually running Alembic commands

### Import Errors

- Ensure you're in the `backend` directory when running commands
- Verify all dependencies are installed: `pip install -r requirements.txt`
- Check Python path includes the backend directory
- The backend uses Pydantic's `EmailStr` type; the required `email_validator` dependency is provided via the `pydantic[email]` extra in `backend/requirements.txt`.

## Frontend Development Server

From the repository root:

```bash
npm install
npm run dev
```


