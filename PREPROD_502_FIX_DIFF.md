# Unified Diff: Preprod 502 Fix

## File: `.github/workflows/build-and-push.yml`

```diff
--- a/.github/workflows/build-and-push.yml
+++ b/.github/workflows/build-and-push.yml
@@ -45,6 +45,9 @@ jobs:
           tags: |
             ghcr.io/${{ github.repository_owner }}/inkq-${{ matrix.service }}:preprod
             ghcr.io/${{ github.repository_owner }}/inkq-${{ matrix.service }}:${{ github.sha }}
+          build-args: |
+            ${{ matrix.service == 'frontend' && 'PUBLIC_API_BASE_URL=https://inkq-preprod.dmitrybond.tech/api' || '' }}
+            ${{ matrix.service == 'frontend' && 'ASTRO_OUTPUT_MODE=server' || '' }}
           cache-from: type=registry,ref=ghcr.io/${{ github.repository_owner }}/inkq-${{ matrix.service }}:preprod
           cache-to: type=inline
```

## Summary
Added `build-args` section to the frontend build step to explicitly set:
- `ASTRO_OUTPUT_MODE=server` (ensures SSR build with `dist/server/entry.mjs`)
- `PUBLIC_API_BASE_URL=https://inkq-preprod.dmitrybond.tech/api` (maintains API base URL configuration)

The build-args are conditionally set only for the frontend service using GitHub Actions expressions, so backend builds are unaffected.
