# Auth Routing Fix Changelog

## Overview

Fixed authentication regression in preprod/prod where HTML forms posting to `/api/v1/auth/*` were intercepted by FastAPI reverse proxy, causing Pydantic validation errors and preventing `inkq_session` cookie from being set.

## Changes

### 1. Created New Auth Endpoints

Created new Astro API route endpoints under `/auth/*` (instead of `/api/v1/auth/*`) to bypass the backend reverse proxy:

- **`src/pages/auth/signin.ts`** - Handles signin form submissions
  - Parses form data or JSON from request body
  - Validates login/email and password fields
  - Calls backend `/api/v1/auth/signin` via `callBackendJsonParse`
  - Sets `inkq_session` cookie (httpOnly, sameSite=lax, secure in prod, path=/, maxAge 7d)
  - Redirects to `/{lang}/onboarding/{account_type}` if onboarding incomplete, else `/{lang}/dashboard/{account_type}`
  - Extracts language from Referer header (defaults to 'en')

- **`src/pages/auth/signup.ts`** - Handles signup form submissions
  - Parses email, username, password, accountType from form data or JSON
  - Validates required fields
  - Normalizes account_type (artist|studio|model)
  - Calls backend `/api/v1/auth/signup`, then `/api/v1/auth/signin` for auto-login
  - Sets `inkq_session` cookie and redirects to onboarding/dashboard
  - Extracts language from Referer header (defaults to 'en')

- **`src/pages/auth/signout.ts`** - Handles signout requests
  - Extracts language from Referer header or form data (defaults to 'en')
  - Optionally calls backend `/api/v1/auth/signout` (best-effort, ignores failures)
  - Clears `inkq_session` cookie (empty value, maxAge=0, path=/, sameSite=lax, secure in prod, httpOnly)
  - Redirects to localized home `/{lang}`

### 2. Updated Form Actions

Updated HTML form `action` attributes to use new endpoints:

- **`src/pages/[lang]/signin.astro`**: Changed form action from `/api/v1/auth/signin` to `/auth/signin`
- **`src/pages/[lang]/signup.astro`**: Changed form action from `/api/v1/auth/signup` to `/auth/signup`
- **`src/components/Header.astro`**: Changed signout form action from `/api/v1/auth/signout` to `/auth/signout`

## Technical Details

### Why This Fix Works

- In deployed environments, `/api/v1/*` is routed to FastAPI by reverse proxy, bypassing Astro API routes
- New endpoints under `/auth/*` are not matched by reverse proxy rules, so they are handled by Astro
- Astro endpoints parse form data, convert to JSON, and forward to backend FastAPI
- Cookie setting happens in Astro middleware, which runs before reverse proxy routing

### Backward Compatibility

- Backend `/api/v1/auth/*` endpoints remain unchanged
- Existing `/api/v1/auth/*` Astro routes remain intact (can be deprecated later)
- API clients can still call `/api/v1/auth/*` directly if needed

## Testing

See `AUTH_ROUTING_FIX_TEST_CHECKLIST.md` for detailed test procedures.

## Impact

- ✅ Fixes authentication form submissions in preprod/prod
- ✅ Cookie is now properly set, enabling navbar to show avatar/signout
- ✅ No breaking changes to backend API
- ✅ No new dependencies required
- ✅ Minimal code changes (3 new files, 3 form action updates)

