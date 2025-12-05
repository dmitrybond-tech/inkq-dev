# SSR Migration Changelog

This document summarizes the changes made to migrate the Astro frontend from static + serve deployment to proper SSR using @astrojs/node adapter.

## Changes

1. **package.json** - Added @astrojs/node dependency and start script
   - Added `@astrojs/node: ^9.5.1` to dependencies (compatible with Astro 5.16.0)
   - Added `start` script: `NODE_ENV=production node dist/server/entry.mjs` for running the SSR server in production

2. **astro.config.mjs** - Configured Node adapter for SSR
   - Imported `@astrojs/node` adapter
   - Added environment-based output mode detection (static vs server)
   - Configured adapter to use `standalone` mode when output is `server`
   - Added server configuration:
     - `host: true` to bind to 0.0.0.0 (required for Docker containers)
     - `port: 4173` in production (configurable via PORT env var), `4321` in development
   - Preserved existing Tailwind integration

3. **Dockerfile** - Updated to build and run SSR server
   - Changed default `ASTRO_OUTPUT_MODE` from `static` to `server`
   - Added `NODE_ENV=production` environment variable
   - Removed all hacky workarounds for static builds:
     - Removed `sed` commands that stripped `prerender = false` from pages
     - Removed Node.js script that modified `getStaticPaths` functions
   - Runtime stage changes:
     - Removed `serve` package installation
     - Added `PORT=4173` environment variable
     - Changed CMD from `serve -s dist -l 4173` to `node dist/server/entry.mjs`
     - Added `package.json` copy to runtime stage (may be needed by the SSR server)

## Impact

- **Local Development**: `npm run dev` continues to work on port 4321 with all routes functional
- **Production Build**: `npm run build` now produces SSR build with `dist/server/entry.mjs` entry point
- **Docker Deployment**: Frontend container now runs Node SSR server instead of static file server
- **Routing**: All dynamic routes (artist/studio/model slugs, dashboards) now work correctly in preprod
- **Landing Pages**: Root `/` and `/[lang]/` landing pages continue to work with `prerender = true`

## Verification

After deployment, verify that:
- `/` → EN landing page (LandingHero)
- `/en/` and `/ru/` → localized landing pages
- `/[lang]/artists`, `/[lang]/studios`, `/[lang]/models` → catalog pages work correctly
- `/[lang]/artist/<slug>`, `/[lang]/studio/<slug>`, `/[lang]/model/<slug>` → dynamic detail pages work as before

