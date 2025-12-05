# Preprod 502 Error Fix - SSR Build Mode

## Summary
Fixed HTTP 502 errors in preprod environment caused by frontend container crashes. The issue was that GitHub Actions was building the frontend image with `ASTRO_OUTPUT_MODE=static`, which produces a static build without `dist/server/entry.mjs`, while the Dockerfile expects an SSR build that includes the server entry point.

## Changes Made

### GitHub Actions Workflow (`.github/workflows/build-and-push.yml`)
- **Added build-args for frontend service**: Set `ASTRO_OUTPUT_MODE=server` and `PUBLIC_API_BASE_URL=https://inkq-preprod.dmitrybond.tech/api` when building the frontend image
- **Conditional build-args**: Build args are only set for the frontend service; backend builds are unaffected

## Root Cause
The frontend Dockerfile was updated to use SSR mode (expecting `dist/server/entry.mjs`), but the GitHub Actions workflow was still building with `ASTRO_OUTPUT_MODE=static`. This mismatch caused the container to crash on startup when trying to execute `node dist/server/entry.mjs`, which doesn't exist in static builds.

## Solution
Updated the GitHub Actions workflow to explicitly set `ASTRO_OUTPUT_MODE=server` for frontend builds, ensuring the build mode matches the runtime expectations. The Dockerfile already defaults to `ASTRO_OUTPUT_MODE=server`, but explicitly setting it in the workflow ensures consistency.

## Impact
- Frontend images built by GitHub Actions will now include `dist/server/entry.mjs`
- Frontend container will start successfully in preprod
- HTTP 502 errors will be resolved
- All frontend routes will respond correctly via Caddy reverse proxy

## Testing
After this change is merged to `main`:
1. GitHub Actions will build the frontend image with SSR mode
2. On VPS, after `docker compose -f docker-compose.preprod.yml pull frontend` and `docker compose -f docker-compose.preprod.yml up -d`, the container should show status `Up`
3. `curl -I http://127.0.0.1:4173/` should return HTTP 200
4. `https://inkq-preprod.dmitrybond.tech/` should open the EN landing page without 502 errors

