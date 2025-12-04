# Changelog - Feature 1: Accounts & Roles Implementation

## Summary

Implemented Feature 1: Accounts & Roles in the InkQ monorepo backend. This includes a complete FastAPI backend with user authentication, role-based accounts (Artist/Studio/Model), and database schema management.

## Changes

### Backend Infrastructure

1. **Created backend directory structure**
   - `backend/app/` - Main application package
   - `backend/app/models/` - SQLAlchemy models
   - `backend/app/schemas/` - Pydantic schemas
   - `backend/app/routes/` - API route handlers
   - `backend/app/db/` - Database configuration
   - `backend/alembic/` - Database migrations
   - `backend/tests/` - Test suite

2. **Database Configuration** (`backend/app/config.py`)
   - Reads `INKQ_PG_URL` from root `.env` file
   - Configurable settings for API, security, and database

3. **Database Setup** (`backend/app/db/base.py`)
   - SQLAlchemy engine and session factory
   - Database dependency injection for FastAPI routes

### Models

4. **User Model** (`backend/app/models/user.py`)
   - Fields: id, email (unique), password_hash, username (unique), account_type (enum), onboarding_completed, timestamps
   - AccountType enum: ARTIST, STUDIO, MODEL
   - 1-1 relationships to Artist, Studio, Model

5. **Role Models**
   - `backend/app/models/artist.py` - Artist role with user_id FK
   - `backend/app/models/studio.py` - Studio role with user_id FK
   - `backend/app/models/model.py` - Model role with user_id FK
   - All have unique user_id constraint enforcing 1-1 relationship

### API Routes

6. **Authentication Routes** (`backend/app/routes/auth.py`)
   - `POST /api/v1/auth/signup` - Create user with role in single transaction
   - Validates account_type (artist/studio/model)
   - Password hashing with bcrypt
   - Transaction-safe user + role creation
   - Error handling for duplicates and invalid input

7. **User Routes** (`backend/app/routes/users.py`)
   - `GET /api/v1/users/me` - Get current user (stub, demonstrates role invariants)
   - Enforces role invariant checks

### Schemas

8. **Pydantic Schemas** (`backend/app/schemas/user.py`)
   - `UserCreate` - Signup request schema with account_type validation
   - `UserResponse` - User response schema
   - AccountType literal type for validation

### Database Migrations

9. **Alembic Setup**
   - `backend/alembic.ini` - Alembic configuration
   - `backend/alembic/env.py` - Migration environment with model imports
   - `backend/alembic/script.py.mako` - Migration template
   - Configured to use `INKQ_PG_URL` from settings

### Database Reset

10. **Dev Database Reset Script** (`infra/db/reset_dev_schema.sql`)
    - Safely drops and recreates public schema
    - Development-only, never executed automatically
    - PowerShell command provided for execution

### Testing

11. **Test Suite** (`backend/tests/test_auth.py`)
    - Tests for signup as artist, studio, model
    - Tests for invalid account_type rejection
    - Tests for duplicate email/username handling
    - Tests for role invariant verification
    - Uses pytest with test database

12. **Test Configuration** (`backend/pytest.ini`)
    - Pytest configuration for test discovery

### Documentation

13. **Feature Documentation** (`docs/accounts_roles.md`)
    - Complete schema documentation
    - API endpoint documentation
    - Invariant explanations
    - Database reset instructions
    - Migration guide

14. **Setup Guide** (`SETUP.md`)
    - Quick start instructions
    - Common commands
    - Troubleshooting guide

15. **Backend README** (`backend/README.md`)
    - Backend-specific setup and usage

16. **Migration Guide** (`backend/MIGRATION_GUIDE.md`)
    - Step-by-step migration instructions

### Dependencies

17. **Requirements** (`backend/requirements.txt`)
    - FastAPI, Uvicorn, SQLAlchemy, Alembic
    - psycopg2-binary for PostgreSQL
    - Pydantic v2, pydantic-settings
    - passlib[bcrypt] for password hashing
    - pytest and httpx for testing

### Main Application

18. **FastAPI App** (`backend/app/main.py`)
    - FastAPI application initialization
    - Router registration
    - Health check endpoints

## Files Created

### Backend Core
- `backend/app/__init__.py`
- `backend/app/main.py`
- `backend/app/config.py`
- `backend/app/db/__init__.py`
- `backend/app/db/base.py`

### Models
- `backend/app/models/__init__.py`
- `backend/app/models/user.py`
- `backend/app/models/artist.py`
- `backend/app/models/studio.py`
- `backend/app/models/model.py`

### Schemas
- `backend/app/schemas/__init__.py`
- `backend/app/schemas/user.py`

### Routes
- `backend/app/routes/__init__.py`
- `backend/app/routes/auth.py`
- `backend/app/routes/users.py`

### Migrations
- `backend/alembic.ini`
- `backend/alembic/env.py`
- `backend/alembic/script.py.mako`

### Tests
- `backend/tests/__init__.py`
- `backend/tests/test_auth.py`
- `backend/pytest.ini`

### Infrastructure
- `infra/db/reset_dev_schema.sql`

### Documentation
- `docs/accounts_roles.md`
- `SETUP.md`
- `backend/README.md`
- `backend/MIGRATION_GUIDE.md`
- `CHANGELOG.md` (this file)

### Configuration
- `backend/requirements.txt`

## Database Schema

### Users Table
```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR UNIQUE NOT NULL,
    password_hash VARCHAR NOT NULL,
    username VARCHAR UNIQUE NOT NULL,
    account_type VARCHAR NOT NULL,  -- enum: artist, studio, model
    onboarding_completed BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL
);
```

### Role Tables
```sql
CREATE TABLE artists (
    id SERIAL PRIMARY KEY,
    user_id INTEGER UNIQUE NOT NULL REFERENCES users(id),
    display_name VARCHAR,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL
);

CREATE TABLE studios (
    id SERIAL PRIMARY KEY,
    user_id INTEGER UNIQUE NOT NULL REFERENCES users(id),
    display_name VARCHAR,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL
);

CREATE TABLE models (
    id SERIAL PRIMARY KEY,
    user_id INTEGER UNIQUE NOT NULL REFERENCES users(id),
    display_name VARCHAR,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL
);
```

## API Endpoints

### POST /api/v1/auth/signup
- Creates user with role in single transaction
- Requires: email, password, username, account_type
- Returns: UserResponse with account details

### GET /api/v1/users/me
- Returns current user (stub implementation)
- Demonstrates role invariant checking

## Invariants Enforced

1. ✅ User must have account_type at signup
2. ✅ User + role created in single transaction
3. ✅ 1-1 relationship enforced via UNIQUE FK constraint
4. ✅ account_type = 'artist' ⇒ artist record exists
5. ✅ account_type = 'studio' ⇒ studio record exists
6. ✅ account_type = 'model' ⇒ model record exists

## Next Steps

To use this backend:

1. Create `.env` file in repository root with `INKQ_PG_URL`
2. Install dependencies: `pip install -r backend/requirements.txt`
3. Reset database (if needed): Run `infra/db/reset_dev_schema.sql`
4. Create migration: `cd backend && alembic revision --autogenerate -m "Initial schema"`
5. Apply migration: `cd backend && alembic upgrade head`
6. Start server: `cd backend && uvicorn app.main:app --reload`

## Notes

- Frontend (Astro) files were not modified as per requirements
- No existing backend was replaced - new backend created from scratch
- All database operations are transaction-safe
- Configuration reads from root `.env` file
- Reset script is dev-only and never executed automatically

---

# Changelog - Feature 1.b: Auth Sessions, Astro Middleware, Role-Based Redirects

## Summary

Implemented full login/session flow for InkQ with backend sessions (opaque tokens), HTTP-only cookies, Astro middleware for route protection, and role-based redirects.

## Changes

### Backend - Session Management

1. **Session Model** (`backend/app/models/session.py`)
   - New `sessions` table with opaque token (id), user_id FK, timestamps, expiration, last_seen_at
   - Optional ip_address and user_agent fields
   - Relationship to User model

2. **User Model Update** (`backend/app/models/user.py`)
   - Added `sessions` relationship with cascade delete

3. **Database Migration** (`backend/alembic/versions/88ac1744563a_add_sessions_table.py`)
   - Creates `sessions` table
   - Adds indexes on id and user_id

### Backend - Authentication Endpoints

4. **POST /api/v1/auth/signin** (`backend/app/routes/auth.py`)
   - Accepts login (email or username) and password
   - Verifies password using bcrypt
   - Creates session with 7-day expiration
   - Returns `{ access_token, user }`
   - Handles invalid credentials (401)

5. **GET /api/v1/auth/me** (`backend/app/routes/auth.py`)
   - Reads `Authorization: Bearer <token>` header
   - Validates session token and expiration
   - Updates `last_seen_at` on each request
   - Enforces role invariants
   - Returns user data (401 if invalid/expired)

6. **POST /api/v1/auth/signout** (`backend/app/routes/auth.py`)
   - Deletes session from database
   - Returns 204 No Content (idempotent)

7. **Password Verification** (`backend/app/routes/auth.py`)
   - Added `verify_password()` function using passlib

8. **Schemas** (`backend/app/schemas/user.py`)
   - Added `SignInRequest` schema
   - Added `SignInResponse` schema

9. **User Routes** (`backend/app/routes/users.py`)
   - Removed stub `/users/me` endpoint (moved to `/auth/me`)

### Backend - Tests

10. **Extended Test Suite** (`backend/tests/test_auth.py`)
    - `test_signin_success` - Successful signin creates session
    - `test_signin_with_username` - Signin with username works
    - `test_signin_wrong_password` - Wrong password returns 401
    - `test_signin_invalid_user` - Non-existent user returns 401
    - `test_auth_me_success` - Valid token returns user data
    - `test_auth_me_invalid_token` - Invalid token returns 401
    - `test_auth_me_no_token` - Missing token returns 401
    - `test_signout_success` - Signout deletes session

### Frontend - Configuration

11. **Config Utility** (`src/shared/config.ts`)
    - `getApiUrl()` function reads `INKQ_API_URL` from environment
    - Throws clear error in dev if missing

12. **API Client** (`src/shared/api/client.ts`)
    - `callBackendJson()` - Generic backend fetch helper
    - `callBackendJsonParse()` - Backend fetch with JSON parsing
    - Handles error mapping

### Frontend - API Routes

13. **POST /api/v1/auth/signin** (`src/pages/api/v1/auth/signin.ts`)
    - Proxies to backend signin
    - Sets `inkq_session` HTTP-only cookie
    - Redirects based on onboarding status
    - Handles errors with user-friendly messages

14. **POST /api/v1/auth/signup** (`src/pages/api/v1/auth/signup.ts`)
    - Proxies to backend signup
    - Automatically signs in user after signup
    - Sets cookie and redirects
    - Handles validation errors

15. **POST /api/v1/auth/signout** (`src/pages/api/v1/auth/signout.ts`)
    - Proxies to backend signout
    - Clears `inkq_session` cookie
    - Redirects to signin

### Frontend - Pages

16. **Signin Page** (`src/pages/[lang]/signin.astro`)
    - Updated form to POST to `/api/v1/auth/signin`
    - Changed email field to login (supports email or username)
    - Added error display from query params
    - Added autocomplete attributes

17. **Signup Page** (`src/pages/[lang]/signup.astro`)
    - Updated form to POST to `/api/v1/auth/signup`
    - Added username field
    - Added error display from query params
    - Added validation attributes

### Frontend - Middleware

18. **Auth Middleware** (`src/middleware.ts`)
    - Reads `inkq_session` cookie
    - Calls `/api/v1/auth/me` to resolve user
    - Stores user in `context.locals.user`
    - Protects `/[lang]/dashboard/**` and `/[lang]/onboarding/**`
    - Redirects unauthenticated users to signin
    - Enforces onboarding redirects (incomplete → onboarding)
    - Enforces role prefix matching in dashboard URLs
    - Preserves language prefix in all redirects
    - Skips `/api/**`, static assets, etc.

19. **TypeScript Types** (`src/env.d.ts`)
    - Extended `App.Locals` with `user` type
    - Defines user structure for type safety

### Documentation

20. **Auth Sessions Documentation** (`docs/auth_sessions.md`)
    - Complete session model documentation
    - Cookie configuration details
    - Authentication flow diagrams
    - Middleware routing rules
    - Backend endpoint specifications
    - Security considerations

## Files Created

### Backend
- `backend/app/models/session.py`
- `backend/alembic/versions/88ac1744563a_add_sessions_table.py`

### Frontend
- `src/shared/config.ts`
- `src/shared/api/client.ts`
- `src/pages/api/v1/auth/signin.ts`
- `src/pages/api/v1/auth/signup.ts`
- `src/pages/api/v1/auth/signout.ts`
- `src/middleware.ts`
- `src/env.d.ts`

### Documentation
- `docs/auth_sessions.md`

## Files Modified

### Backend
- `backend/app/models/user.py` - Added sessions relationship
- `backend/app/models/__init__.py` - Added Session import
- `backend/app/routes/auth.py` - Added signin, me, signout endpoints
- `backend/app/routes/users.py` - Removed stub /users/me
- `backend/app/schemas/user.py` - Added SignInRequest and SignInResponse
- `backend/alembic/env.py` - Added Session model import
- `backend/tests/test_auth.py` - Added signin/me/signout tests

### Frontend
- `src/pages/[lang]/signin.astro` - Updated form and error handling
- `src/pages/[lang]/signup.astro` - Updated form and error handling

### Documentation
- `CHANGELOG.md` - Added Feature 1.b section

## Environment Variables

### New Required Variable

- `INKQ_API_URL` - Base URL for FastAPI backend (e.g., `http://localhost:8000`)

Add to `.env` in repository root:
```env
INKQ_API_URL=http://localhost:8000
```

## Database Schema

### Sessions Table
```sql
CREATE TABLE sessions (
    id VARCHAR PRIMARY KEY,  -- Opaque token
    user_id INTEGER NOT NULL REFERENCES users(id),
    created_at TIMESTAMP NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    last_seen_at TIMESTAMP NOT NULL,
    ip_address VARCHAR,
    user_agent VARCHAR
);

CREATE INDEX ix_sessions_id ON sessions(id);
CREATE INDEX ix_sessions_user_id ON sessions(user_id);
```

## API Endpoints

### POST /api/v1/auth/signin
- Accepts: `{ login: string, password: string }`
- Returns: `{ access_token: string, user: UserResponse }`
- Status: 200 OK, 400 Bad Request, 401 Unauthorized

### GET /api/v1/auth/me
- Headers: `Authorization: Bearer <token>`
- Returns: `UserResponse`
- Status: 200 OK, 401 Unauthorized

### POST /api/v1/auth/signout
- Headers: `Authorization: Bearer <token>`
- Returns: 204 No Content
- Status: 204 No Content, 401 Unauthorized

## Cookie Configuration

- Name: `inkq_session`
- httpOnly: `true`
- secure: `true` (production only)
- sameSite: `'lax'`
- path: `'/'`
- maxAge: `7 days` (604800 seconds)

## Middleware Routing Rules

### Public Paths
- `/`, `/en`, `/ru`
- `/{lang}/signin`, `/{lang}/signup`

### Protected Paths
- `/{lang}/dashboard/**` - Requires auth
- `/{lang}/onboarding/**` - Requires auth

### Redirects
- Unauthenticated → `/{lang}/signin?reason=auth_required`
- Incomplete onboarding → `/{lang}/onboarding/{account_type}`
- Wrong role in URL → `/{lang}/dashboard/{user.account_type}`
- Authenticated on signin/signup → dashboard/onboarding

## Testing

### Backend Tests
All new endpoints are covered:
- ✅ Signin with email
- ✅ Signin with username
- ✅ Signin with wrong password
- ✅ Signin with invalid user
- ✅ /auth/me with valid token
- ✅ /auth/me with invalid token
- ✅ /auth/me without token
- ✅ Signout deletes session

### Manual Testing Commands

See PowerShell commands in final report.

## Migration Instructions

1. Run database migration:
   ```powershell
   cd backend
   alembic upgrade head
   ```

2. Add `INKQ_API_URL` to `.env`:
   ```env
   INKQ_API_URL=http://localhost:8000
   ```

3. Restart backend and frontend servers

## Notes

- Sessions use opaque tokens (not JWTs) stored server-side
- Cookie is HTTP-only for XSS protection
- Middleware preserves language prefix in all redirects
- Onboarding redirect logic: incomplete → onboarding, complete → dashboard
- Role enforcement: dashboard URLs must match user's account_type
- All existing signup tests continue to pass

