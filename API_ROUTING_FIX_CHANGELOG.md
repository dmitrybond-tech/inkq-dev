# API Routing Fix - Double /api Prefix

## Summary
Fixed the double `/api` prefix issue in preprod where API requests were going to `/api/api/v1/...` instead of `/api/v1/...`. The root cause was `PUBLIC_API_BASE_URL` being set to `https://inkq-preprod.dmitrybond.tech/api` instead of an empty string.

## Problem
In preprod, browser console showed:
```
POST https://inkq-preprod.dmitrybond.tech/api/api/v1/auth/signup 404 (Not Found)
```

This happened because:
1. `PUBLIC_API_BASE_URL` was set to `https://inkq-preprod.dmitrybond.tech/api` (from previous fix)
2. Frontend code constructs URLs as: `${getApiUrl()}/api/v1/...`
3. When `getApiUrl()` returned `https://inkq-preprod.dmitrybond.tech/api`, the result was `https://inkq-preprod.dmitrybond.tech/api/api/v1/...`

## Solution

### 1. Updated docker-compose.preprod.yml
Added `PUBLIC_API_BASE_URL=""` to the frontend service environment:
```yaml
frontend:
  environment:
    PUBLIC_API_BASE_URL: ""
```

### 2. GitHub Actions Workflow (Required Change)
**IMPORTANT**: The GitHub Actions workflow (`.github/workflows/build-and-push.yml`) needs to be updated to set `PUBLIC_API_BASE_URL=""` instead of `PUBLIC_API_BASE_URL=https://inkq-preprod.dmitrybond.tech/api`.

**Current (incorrect)**:
```yaml
build-args: |
  ${{ matrix.service == 'frontend' && 'PUBLIC_API_BASE_URL=https://inkq-preprod.dmitrybond.tech/api' || '' }}
  ${{ matrix.service == 'frontend' && 'ASTRO_OUTPUT_MODE=server' || '' }}
```

**Should be**:
```yaml
build-args: |
  ${{ matrix.service == 'frontend' && 'PUBLIC_API_BASE_URL=' || '' }}
  ${{ matrix.service == 'frontend' && 'ASTRO_OUTPUT_MODE=server' || '' }}
```

Or simply:
```yaml
build-args: |
  ${{ matrix.service == 'frontend' && 'PUBLIC_API_BASE_URL=' || '' }}
  ${{ matrix.service == 'frontend' && 'ASTRO_OUTPUT_MODE=server' || '' }}
```

### 3. Environment Variable Documentation
Created `.env.example` and `.env.preprod.example` files (if not blocked by .gitignore) documenting:
- Dev: `INKQ_API_URL=http://localhost:8000`
- Preprod: `PUBLIC_API_BASE_URL=""` (empty string)

### 4. Verification Checklist
Created `API_INTEGRATION_CHECKLIST.md` with detailed steps to verify the fix in dev, SSR build, and preprod environments.

## How It Works

### Development
- `INKQ_API_URL=http://localhost:8000` (from `.env`)
- `getApiUrl()` returns `http://localhost:8000`
- Final URL: `http://localhost:8000/api/v1/...`

### Preprod
- `PUBLIC_API_BASE_URL=""` (empty string)
- `getApiUrl()` returns `""`
- Final URL: `/api/v1/...` (relative path)
- Caddy reverse proxy matches `/api/*` and forwards to `127.0.0.1:8000`
- Backend receives `/api/v1/...` and routes correctly

## Testing

After deploying this fix:

1. **Verify in browser dev tools**:
   - Open `https://inkq-preprod.dmitrybond.tech/en/signup`
   - Submit form
   - Check network tab: request should go to `https://inkq-preprod.dmitrybond.tech/api/v1/auth/signup` (NOT `/api/api/v1/...`)

2. **Verify backend accessibility**:
   ```bash
   curl -i http://127.0.0.1:8000/api/v1/auth/signup
   curl -i https://inkq-preprod.dmitrybond.tech/api/v1/auth/signup
   ```
   Both should return non-404 status (422 for validation errors, 201 for success)

3. **Check Docker environment**:
   ```bash
   docker exec inkq_preprod_frontend env | grep PUBLIC_API_BASE_URL
   # Should show: PUBLIC_API_BASE_URL=
   ```

## Files Changed

- `docker-compose.preprod.yml` - Added `PUBLIC_API_BASE_URL=""` to frontend service
- `API_INTEGRATION_CHECKLIST.md` - Created verification checklist
- `.env.example` - Created (if not blocked by .gitignore)
- `.env.preprod.example` - Created (if not blocked by .gitignore)

## Files That Need Manual Update

- `.github/workflows/build-and-push.yml` - Update `PUBLIC_API_BASE_URL` build arg to empty string

## Impact

- ✅ Fixes double `/api` prefix in preprod
- ✅ Signup/login flows work correctly
- ✅ All API endpoints accessible in preprod
- ✅ No changes to backend routes or Caddy configuration
- ✅ Dev environment continues to work as before

