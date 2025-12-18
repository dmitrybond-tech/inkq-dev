# Unified Diff: Auth Routing Fix

## New Files Created

### src/pages/auth/signin.ts
- New Astro API route endpoint at `/auth/signin`
- Copied logic from `src/pages/api/v1/auth/signin.ts`
- Handles form data and JSON parsing
- Sets `inkq_session` cookie on success
- Redirects to onboarding or dashboard based on user state

### src/pages/auth/signup.ts
- New Astro API route endpoint at `/auth/signup`
- Copied logic from `src/pages/api/v1/auth/signup.ts`
- Validates and normalizes account_type (artist|studio|model)
- Calls backend signup, then auto-signs in user
- Sets `inkq_session` cookie and redirects

### src/pages/auth/signout.ts
- New Astro API route endpoint at `/auth/signout`
- Copied logic from `src/pages/api/v1/auth/signout.ts`
- Extracts language from Referer header
- Clears `inkq_session` cookie (httpOnly, sameSite=lax, secure in prod, maxAge=0)
- Optionally calls backend signout endpoint (best-effort)
- Redirects to localized home page

## Files Modified

### src/pages/[lang]/signin.astro
```diff
-        action="/api/v1/auth/signin"
+        action="/auth/signin"
```

### src/pages/[lang]/signup.astro
```diff
-        action="/api/v1/auth/signup"
+        action="/auth/signup"
```

### src/components/Header.astro
```diff
-              <form method="post" action="/api/v1/auth/signout" class="border-t border-[var(--inkq-border)] mt-1">
+              <form method="post" action="/auth/signout" class="border-t border-[var(--inkq-border)] mt-1">
```

## Summary

- **3 new endpoint files** created under `src/pages/auth/` (not `/api/v1/auth/`)
- **3 form action attributes** updated to use new endpoints
- **No backend changes** - backend `/api/v1/auth/*` endpoints remain unchanged
- **No new dependencies** added
- **Existing `/api/v1/auth/*` Astro routes** remain intact (can be deprecated later)

