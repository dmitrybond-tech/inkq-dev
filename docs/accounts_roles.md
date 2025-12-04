# Accounts & Roles Feature

## Overview

The InkQ backend implements a user account system with role-based access. Each user account has a single role (Artist, Studio, or Model) that is determined at signup and cannot be changed.

## Database Schema

### Users Table

The `users` table stores all account information:

- `id` (PK): Unique identifier
- `email` (unique, non-null): User's email address
- `password_hash` (non-null): Bcrypt-hashed password
- `username` (unique, non-null): Username used in URLs
- `account_type` (enum, non-null): One of `artist`, `studio`, or `model`
- `onboarding_completed` (bool, default false): Whether user has completed onboarding
- `created_at` (timestamp): Account creation time
- `updated_at` (timestamp): Last update time

### Role Tables

Three role tables maintain a strict 1-1 relationship with users:

#### Artists Table
- `id` (PK)
- `user_id` (FK to users.id, UNIQUE, NOT NULL)
- `display_name` (optional)
- `created_at`, `updated_at`

#### Studios Table
- `id` (PK)
- `user_id` (FK to users.id, UNIQUE, NOT NULL)
- `display_name` (optional)
- `created_at`, `updated_at`

#### Models Table
- `id` (PK)
- `user_id` (FK to users.id, UNIQUE, NOT NULL)
- `display_name` (optional)
- `created_at`, `updated_at`

## Invariants

The following invariants are enforced at the application level:

1. **Role Selection at Signup**: Every user must choose an `account_type` during signup. It cannot be null or omitted.

2. **1-1 Relationship**: Each user has exactly one role entity:
   - `account_type = 'artist'` ⇒ exactly one row in `artists` table
   - `account_type = 'studio'` ⇒ exactly one row in `studios` table
   - `account_type = 'model'` ⇒ exactly one row in `models` table

3. **No Multiple Roles**: A user cannot have multiple role entities. The foreign key constraint (`UNIQUE`) enforces this at the database level.

4. **Transaction Safety**: User and role creation happen in a single database transaction. If role creation fails, the user creation is rolled back.

## API Endpoints

### POST /api/v1/auth/signup

Creates a new user account with the specified role.

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "password123",
  "username": "username",
  "account_type": "artist"  // or "studio" or "model"
}
```

**Response (201 Created):**
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

**Error Responses:**
- `400 Bad Request`: Invalid `account_type`, duplicate email, or duplicate username
- `500 Internal Server Error`: Database or server error

### GET /api/v1/users/me

Returns the current authenticated user's information.

**Note**: This endpoint is currently a stub. In production, it should:
- Extract user from JWT token
- Verify authentication
- Return the authenticated user's data

**Response (200 OK):**
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

## Database Reset (Development Only)

⚠️ **WARNING**: The reset script will **DELETE ALL DATA** in the database. Only use in development!

### Reset Script Location

`infra/db/reset_dev_schema.sql`

### How to Reset

From the repository root, using PowerShell:

```powershell
# Set password environment variable
$env:PGPASSWORD = "InkqDev2025!"

# Run the reset script
psql "host=localhost port=5432 dbname=inkq user=inkq" -f infra/db/reset_dev_schema.sql
```

The script will:
1. Drop the `public` schema (and all its contents)
2. Recreate the `public` schema
3. Grant necessary permissions

### After Reset

After resetting the database, you must run migrations to recreate the tables:

```bash
cd backend
alembic upgrade head
```

## Migrations

Database migrations are managed using Alembic.

### Create a New Migration

```bash
cd backend
alembic revision --autogenerate -m "Description of changes"
```

### Apply Migrations

```bash
cd backend
alembic upgrade head
```

### Rollback Migration

```bash
cd backend
alembic downgrade -1
```

## Configuration

The backend reads database connection from the `INKQ_PG_URL` environment variable in the root `.env` file:

```env
INKQ_PG_URL=postgres://inkq:InkqDev2025!@localhost:5432/inkq
```

## Testing

Run tests with pytest:

```bash
cd backend
pytest
```

Test coverage includes:
- Signup as artist, studio, model
- Invalid account_type rejection
- Duplicate email/username handling
- Role invariant verification

## Implementation Details

### Signup Flow

1. Validate `account_type` (must be "artist", "studio", or "model")
2. Hash password using bcrypt
3. Begin database transaction
4. Create `User` record with `onboarding_completed = False`
5. Flush to get `user.id` without committing
6. Create corresponding role entity (Artist/Studio/Model) with `user_id`
7. Commit transaction

If any step fails, the transaction is rolled back and an error is returned.

### Role Access

Access role-specific data through SQLAlchemy relationships:

```python
user = db.query(User).filter(User.id == user_id).first()

if user.account_type == AccountType.ARTIST:
    artist = user.artist  # Direct access to Artist entity
    # artist.display_name, etc.
```

## Future Enhancements

- JWT-based authentication for `/users/me` endpoint
- Role-specific profile endpoints
- Onboarding completion workflow
- Additional role-specific fields as needed

