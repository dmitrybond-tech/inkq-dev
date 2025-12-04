# Authentication Sessions

This document describes the session-based authentication system implemented for InkQ.

## Overview

InkQ uses server-side sessions with opaque tokens stored in PostgreSQL. The frontend stores the session token in an HTTP-only cookie, and all authenticated requests include the token in the `Authorization: Bearer <token>` header.

## Session Model

Sessions are stored in the `sessions` table with the following structure:

- `id` (String, Primary Key): Opaque token (generated with `secrets.token_urlsafe(32)`)
- `user_id` (Integer, Foreign Key): Reference to `users.id`
- `created_at` (DateTime): When the session was created
- `expires_at` (DateTime): When the session expires (default: 7 days from creation)
- `last_seen_at` (DateTime): Last time the session was used (updated on each `/auth/me` call)
- `ip_address` (String, nullable): IP address of the client that created the session
- `user_agent` (String, nullable): User agent string from the client

## Cookie Configuration

The session cookie (`inkq_session`) is configured with:

- `httpOnly: true` - Prevents JavaScript access (XSS protection)
- `secure: true` (production only) - Only sent over HTTPS
- `sameSite: 'lax'` - CSRF protection
- `path: '/'` - Available site-wide
- `maxAge: 7 days` - Matches backend session TTL

## Authentication Flow

### Sign In

1. User submits login (email or username) and password to `/api/v1/auth/signin` (Astro API route)
2. Astro API route calls backend `POST /api/v1/auth/signin`
3. Backend verifies credentials and creates a new session
4. Backend returns `{ access_token, user }`
5. Astro API route sets `inkq_session` cookie with the `access_token`
6. User is redirected based on `onboarding_completed`:
   - `false` → `/{lang}/onboarding/{account_type}`
   - `true` → `/{lang}/dashboard/{account_type}`

### Sign Up

1. User submits signup form to `/api/v1/auth/signup` (Astro API route)
2. Astro API route calls backend `POST /api/v1/auth/signup`
3. Backend creates user and role
4. Astro API route automatically signs in the user (calls signin endpoint)
5. Cookie is set and user is redirected (same logic as signin)

### Authenticated Requests

1. Middleware reads `inkq_session` cookie
2. If present, middleware calls `GET /api/v1/auth/me` with `Authorization: Bearer <token>`
3. Backend validates token, checks expiration, updates `last_seen_at`
4. Backend returns user data
5. Middleware stores user in `context.locals.user` for use in pages

### Sign Out

1. User submits signout request to `/api/v1/auth/signout` (Astro API route)
2. Astro API route calls backend `POST /api/v1/auth/signout` with token
3. Backend deletes the session from database
4. Astro API route clears the `inkq_session` cookie
5. User is redirected to `/{lang}/signin`

## Middleware Routing

The Astro middleware (`src/middleware.ts`) handles:

### Public Paths (No Auth Required)

- `/`, `/en`, `/ru`
- `/{lang}/signin`, `/{lang}/signup`

If an authenticated user visits signin/signup, they are redirected to their dashboard/onboarding.

### Protected Paths (Auth Required)

- `/{lang}/dashboard/**`
- `/{lang}/onboarding/**`

Unauthenticated users are redirected to `/{lang}/signin?reason=auth_required`.

### Onboarding Redirects

- If `onboarding_completed === false` and user visits dashboard → redirect to `/{lang}/onboarding/{account_type}`
- If `onboarding_completed === true` and user visits onboarding → allow access (user can revisit wizard)

### Role Enforcement

- If dashboard URL has a role prefix (e.g., `/en/dashboard/artist`) but user's `account_type` doesn't match → redirect to `/{lang}/dashboard/{user.account_type}`

### Skipped Paths

The middleware skips:
- `/api/**` - Astro API routes
- `/assets/**` - Static assets
- `/favicon.*` - Favicon files
- `/_astro/**` - Astro internal files
- `/node_modules/**` - Node modules

## Backend Endpoints

### POST /api/v1/auth/signin

**Request:**
```json
{
  "login": "user@example.com",  // or username
  "password": "password123"
}
```

**Response (200 OK):**
```json
{
  "access_token": "opaque-token-string",
  "user": {
    "id": 1,
    "email": "user@example.com",
    "username": "username",
    "account_type": "artist",
    "onboarding_completed": false,
    "created_at": "2025-01-01T00:00:00",
    "updated_at": "2025-01-01T00:00:00"
  }
}
```

**Errors:**
- `400 Bad Request`: Malformed request body
- `401 Unauthorized`: Invalid credentials (`detail: "invalid_credentials"`)

### GET /api/v1/auth/me

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response (200 OK):**
```json
{
  "id": 1,
  "email": "user@example.com",
  "username": "username",
  "account_type": "artist",
  "onboarding_completed": false,
  "created_at": "2025-01-01T00:00:00",
  "updated_at": "2025-01-01T00:00:00"
}
```

**Errors:**
- `401 Unauthorized`: Missing, invalid, or expired token

### POST /api/v1/auth/signout

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response (204 No Content):** Empty body

**Errors:**
- `401 Unauthorized`: Missing or invalid token (optional; may return 204 for idempotency)

## Frontend API Routes

All browser requests go through Astro API routes (`src/pages/api/v1/auth/*`), which:

1. Proxy requests to the backend using `INKQ_API_URL`
2. Handle cookie management (set/clear `inkq_session`)
3. Map backend errors to user-friendly messages
4. Handle redirects based on onboarding status

## Environment Variables

### Backend

- `INKQ_PG_URL` - PostgreSQL connection string (already configured)

### Frontend

- `INKQ_API_URL` - Base URL for FastAPI backend (e.g., `http://localhost:8000` in dev)

Add to `.env` in the repository root:
```env
INKQ_API_URL=http://localhost:8000
```

## Security Considerations

1. **Opaque Tokens**: Session tokens are random strings, not JWTs. They must be validated against the database.
2. **HTTP-Only Cookies**: Prevents XSS attacks from stealing tokens via JavaScript.
3. **Secure Flag**: In production, cookies are only sent over HTTPS.
4. **SameSite Lax**: Provides CSRF protection while allowing normal navigation.
5. **Session Expiration**: Sessions expire after 7 days. Expired sessions are automatically deleted on validation attempts.
6. **Last Seen Tracking**: `last_seen_at` is updated on each authenticated request for session activity monitoring.

## Database Migration

The sessions table is created via Alembic migration:

```bash
cd backend
alembic upgrade head
```

Migration file: `backend/alembic/versions/88ac1744563a_add_sessions_table.py`

