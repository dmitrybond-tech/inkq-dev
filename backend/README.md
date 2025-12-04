# InkQ Backend

FastAPI backend for the InkQ application.

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Create a `.env` file in the repository root with:
```env
INKQ_PG_URL=postgres://inkq:InkqDev2025!@localhost:5432/inkq
```

3. Reset the dev database (if needed):
```powershell
$env:PGPASSWORD = "InkqDev2025!"
psql "host=localhost port=5432 dbname=inkq user=inkq" -f ../infra/db/reset_dev_schema.sql
```

4. Run migrations:
```bash
alembic upgrade head
```

5. Start the server:
```bash
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`

## API Documentation

Once the server is running, visit:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Testing

Run tests with:
```bash
pytest
```

## Project Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI app entry point
│   ├── config.py            # Configuration settings
│   ├── db/
│   │   ├── __init__.py
│   │   └── base.py          # Database engine and session
│   ├── models/
│   │   ├── __init__.py
│   │   ├── user.py          # User model
│   │   ├── artist.py        # Artist role model
│   │   ├── studio.py        # Studio role model
│   │   └── model.py         # Model role model
│   ├── schemas/
│   │   ├── __init__.py
│   │   └── user.py          # Pydantic schemas
│   └── routes/
│       ├── __init__.py
│       ├── auth.py          # Authentication routes
│       └── users.py         # User routes
├── alembic/                 # Database migrations
├── tests/                   # Test suite
├── alembic.ini              # Alembic configuration
├── pytest.ini               # Pytest configuration
└── requirements.txt         # Python dependencies
```

## Environment Variables

- `INKQ_PG_URL`: PostgreSQL connection string (required)
- `SECRET_KEY`: Secret key for JWT tokens (optional, defaults to dev key)

