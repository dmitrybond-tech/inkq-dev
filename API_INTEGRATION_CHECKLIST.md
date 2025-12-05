# API Integration Verification Checklist

This document describes how to verify that API routing works correctly between the Astro frontend and FastAPI backend in dev, SSR build, and preprod environments.

## Architecture Overview

- **Backend**: FastAPI on port 8000, mounted at `/api/v1/...`
- **Frontend**: Astro 5.x with Node SSR on port 4173
- **Preprod**: Caddy reverse proxy routes `/api/*` to backend (port 8000), everything else to frontend (port 4173)

## Environment Variables

### Development
- `INKQ_API_URL=http://localhost:8000` (set in `.env`)
- `PUBLIC_API_BASE_URL` should be unset or empty

### Preprod (Docker)
- `PUBLIC_API_BASE_URL=""` (empty string, set in `docker-compose.preprod.yml` or build args)
- Frontend uses relative paths `/api/v1/...` which Caddy proxies to backend

## Verification Steps

### 1. Development (npm run dev)

1. **Start backend**:
   ```bash
   cd backend
   # Start FastAPI on http://localhost:8000
   ```

2. **Start frontend**:
   ```bash
   npm install
   npm run dev
   ```

3. **Verify API URL construction**:
   - Open browser dev tools (Network tab)
   - Navigate to `http://localhost:4321/en/signup`
   - Fill out and submit the signup form
   - Check the network request URL: should be `http://localhost:8000/api/v1/auth/signup` (NOT `/api/api/v1/...`)
   - Verify response status (422 for validation errors, 201 for success, etc.)

4. **Test signin**:
   - Navigate to `http://localhost:4321/en/signin`
   - Submit signin form
   - Check network request: `http://localhost:8000/api/v1/auth/signin`
   - Verify response status

### 2. SSR Build (npm run build && npm run start)

1. **Build frontend**:
   ```bash
   npm run build
   ```

2. **Start SSR server**:
   ```bash
   npm run start
   # Server should start on port 4173 (or PORT env var)
   ```

3. **Verify API URLs**:
   - Open `http://localhost:4173/en/signup`
   - Submit signup form
   - Check network request: should be `http://localhost:8000/api/v1/auth/signup` (if backend is running)
   - Verify no double `/api` prefix

### 3. Preprod (Docker + Caddy)

#### Backend Verification

1. **Test backend directly**:
   ```bash
   # On VPS, test backend container
   curl -i http://127.0.0.1:8000/api/v1/auth/signup
   # Should return 422 (validation error) or 201 (if valid data), NOT 404
   ```

2. **Test through Caddy**:
   ```bash
   curl -i https://inkq-preprod.dmitrybond.tech/api/v1/auth/signup
   # Should return same status as direct backend call, NOT 404
   ```

#### Frontend Verification

1. **Check browser network logs**:
   - Open `https://inkq-preprod.dmitrybond.tech/en/signup`
   - Open browser dev tools (Network tab)
   - Submit signup form
   - Verify request URL: `https://inkq-preprod.dmitrybond.tech/api/v1/auth/signup`
   - **CRITICAL**: Must NOT be `/api/api/v1/auth/signup` (double `/api`)

2. **Verify all API endpoints**:
   - Signup: `/api/v1/auth/signup`
   - Signin: `/api/v1/auth/signin`
   - Signout: `/api/v1/auth/signout`
   - Media uploads: `/api/v1/media/...`
   - Profile endpoints: `/api/v1/artists/me`, `/api/v1/studios/me`, `/api/v1/models/me`
   - Public endpoints: `/api/v1/public/artists`, `/api/v1/public/studios`, `/api/v1/public/models`

3. **Check Docker environment**:
   ```bash
   # Verify frontend container has PUBLIC_API_BASE_URL=""
   docker exec inkq_preprod_frontend env | grep PUBLIC_API_BASE_URL
   # Should show: PUBLIC_API_BASE_URL=
   ```

## Common Issues

### Double `/api` prefix (`/api/api/v1/...`)

**Symptom**: Browser console shows `POST https://inkq-preprod.dmitrybond.tech/api/api/v1/auth/signup 404`

**Cause**: `PUBLIC_API_BASE_URL` is set to a value containing `/api` (e.g., `https://inkq-preprod.dmitrybond.tech/api`)

**Fix**: 
- Set `PUBLIC_API_BASE_URL=""` (empty string) in `docker-compose.preprod.yml`
- Update GitHub Actions workflow to build with `PUBLIC_API_BASE_URL=""` instead of `PUBLIC_API_BASE_URL=https://inkq-preprod.dmitrybond.tech/api`

### 404 errors in preprod

**Symptom**: All API requests return 404

**Possible causes**:
1. Caddy not routing `/api/*` to backend correctly
2. Backend container not running or not accessible on port 8000
3. Backend routes not mounted at `/api/v1/...`

**Fix**: Check Caddy configuration and backend container status

### CORS errors

**Symptom**: Browser console shows CORS errors

**Fix**: Ensure `BACKEND_CORS_ORIGINS` in backend includes the frontend origin

## Expected Behavior Summary

| Environment | getApiUrl() returns | Final API URL pattern |
|------------|---------------------|----------------------|
| Dev | `http://localhost:8000` | `http://localhost:8000/api/v1/...` |
| Preprod | `""` (empty) | `/api/v1/...` (relative, proxied by Caddy) |

## Notes

- The frontend code constructs URLs as: `${getApiUrl()}/api/v1/...`
- When `getApiUrl()` returns empty string, the result is `/api/v1/...` (relative path)
- Caddy reverse proxy matches `/api/*` and forwards to `127.0.0.1:8000` without path rewriting
- Backend FastAPI is mounted at `/api/v1/...`, so the full path matches correctly

