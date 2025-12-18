import type { MiddlewareHandler } from 'astro';
import { getApiUrl } from './shared/config';

// Define user type for locals
interface User {
  id: number;
  email: string;
  username: string;
  account_type: 'artist' | 'studio' | 'model';
  onboarding_completed: boolean;
  avatar_url?: string | null;
  banner_url?: string | null;
  created_at: string;
  updated_at: string;
}

// Paths that don't require authentication
const PUBLIC_PATHS = [
  '/',
  '/en',
  '/ru',
  '/en/signin',
  '/ru/signin',
  '/en/signup',
  '/ru/signup',
];

// Paths that are protected (require authentication)
const PROTECTED_PREFIXES = ['/en/dashboard', '/ru/dashboard', '/en/onboarding', '/ru/onboarding'];

// Paths to skip entirely (API routes, static assets)
const SKIP_PATHS = ['/api/', '/assets/', '/favicon.', '/_astro/', '/node_modules/'];

/**
 * Check if a path should be skipped by middleware
 */
function shouldSkipPath(pathname: string): boolean {
  return SKIP_PATHS.some(skip => pathname.startsWith(skip));
}

/**
 * Check if a path is public (no auth required)
 */
function isPublicPath(pathname: string): boolean {
  return PUBLIC_PATHS.includes(pathname) || pathname === '/';
}

/**
 * Check if a path is protected (auth required)
 */
function isProtectedPath(pathname: string): boolean {
  return PROTECTED_PREFIXES.some(prefix => pathname.startsWith(prefix));
}

/**
 * Extract language from pathname
 */
function extractLang(pathname: string): string {
  const match = pathname.match(/^\/(en|ru)/);
  return match ? match[1] : 'en';
}

/**
 * Resolve backend URL for middleware calls.
 * Mirrors the logic used in the auth/signin API route:
 * - Prefer explicit backend base from `getApiUrl()`
 * - Fallback to same-origin absolute URL when base is empty (preprod/prod behind reverse proxy)
 */
function resolveBackendUrl(path: string, url: URL): string {
  const apiBase = getApiUrl();
  if (apiBase) {
    return `${apiBase}${path}`;
  }
  return new URL(path, url.origin).toString();
}

interface ResolveUserResult {
  user: User | null;
  status: number | null;
  timedOut: boolean;
}

/**
 * Resolve current user from session cookie in an SSR-safe, deterministic way.
 * - Always calls `/api/v1/auth/me` with `Authorization: Bearer <token>`
 * - Uses an AbortController-based timeout to avoid hanging requests
 */
async function resolveUser(token: string, url: URL): Promise<ResolveUserResult> {
  const controller = new AbortController();
  const timeoutMs = 4000;
  const timeoutId = setTimeout(() => controller.abort(), timeoutMs);

  try {
    const meUrl = resolveBackendUrl('/api/v1/auth/me', url);
    const response = await fetch(meUrl, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
      signal: controller.signal,
    });

    if (!import.meta.env.PROD) {
      console.info(
        `[dev][middleware] /api/v1/auth/me`,
        JSON.stringify({
          url: meUrl,
          status: response.status,
        })
      );
    }

    if (response.ok) {
      const user = (await response.json()) as User;
      return { user, status: response.status, timedOut: false };
    }

    return { user: null, status: response.status, timedOut: false };
  } catch (error: any) {
    const timedOut = error?.name === 'AbortError';
    if (!import.meta.env.PROD) {
      console.error(
        '[dev][middleware] error resolving user',
        JSON.stringify({
          message: error?.message,
          name: error?.name,
          timedOut,
        })
      );
    }
    return { user: null, status: null, timedOut };
  } finally {
    clearTimeout(timeoutId);
  }
}

export const onRequest: MiddlewareHandler = async (context, next) => {
  const { url, cookies, redirect } = context;
  const pathname = url.pathname;

  // Skip API routes, static assets, etc.
  if (shouldSkipPath(pathname)) {
    return next();
  }

  const lang = extractLang(pathname);
  const cookieName = 'inkq_session';
  const token = cookies.get(cookieName)?.value;

   // Track auth resolution metadata for loop-breaking logic and dev observability
  const hadCookie = !!token;
  let meStatus: number | null = null;
  let meTimedOut = false;
  let clearedCookie = false;

  if (!import.meta.env.PROD) {
    console.info(
      `[dev][middleware] incoming request`,
      JSON.stringify({
        path: pathname,
        cookieName,
        cookiePresent: hadCookie ? 'yes' : 'no',
      })
    );
  }

  // Resolve user if token exists
  let user: User | null = null;
  if (token) {
    const result = await resolveUser(token, url);
    user = result.user;
    meStatus = result.status;
    meTimedOut = result.timedOut;

    // If backend explicitly says the token is invalid/expired, clear cookie immediately
    if (!user && (meStatus === 401 || meStatus === 403)) {
      cookies.delete(cookieName, { path: '/' });
      clearedCookie = true;
    }

    if (user) {
      // Store user and session token in locals for use in pages
      // Keep existing `locals.user` for current pages and also expose `locals.currentUser` for layout/components.
      context.locals.user = user;
      // Alias required by newer components (e.g. header/nav)
      // so they can check authentication status in a generic way.
      // This does not change behaviour for existing pages.
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      (context.locals as any).currentUser = user;
      context.locals.sessionToken = token;
    }
  }

  // Small helper to annotate responses in development so we can debug auth behaviour
  function withDevAuthHeader(response: Response): Response {
    if (!import.meta.env.PROD) {
      const parts = [
        `path=${pathname}`,
        `cookie=${hadCookie ? 'yes' : 'no'}`,
        `me_status=${meStatus ?? 'none'}`,
        `me_timeout=${meTimedOut ? 'yes' : 'no'}`,
        `cleared=${clearedCookie ? 'yes' : 'no'}`,
      ];
      response.headers.set('X-InkQ-Auth', parts.join('; '));
    }
    return response;
  }

  // Handle public paths
  if (isPublicPath(pathname)) {
    // If user is authenticated and trying to access signin/signup, redirect to dashboard/onboarding
    if (user && (pathname === `/${lang}/signin` || pathname === `/${lang}/signup`)) {
      let redirectPath: string;
      if (!user.onboarding_completed) {
        redirectPath = `/${lang}/onboarding/${user.account_type}`;
      } else {
        redirectPath = `/${lang}/dashboard/${user.account_type}`;
      }
      return withDevAuthHeader(redirect(redirectPath, 302));
    }
    // Otherwise allow access
    const response = await next();
    return withDevAuthHeader(response);
  }

  // Handle protected paths
  if (isProtectedPath(pathname)) {
    // If not authenticated, redirect to signin.
    // Loop-breaker: if we HAD a cookie but /me said 401/403, treat as "session expired"
    if (!user) {
      const urlSearch = new URLSearchParams();
      if (hadCookie && (meStatus === 401 || meStatus === 403)) {
        urlSearch.set('error', 'Session expired');
      } else {
        urlSearch.set('reason', 'auth_required');
      }
      const redirectTarget = `/${lang}/signin?${urlSearch.toString()}`;
      return withDevAuthHeader(redirect(redirectTarget, 302));
    }

    // Handle onboarding paths
    if (pathname.startsWith(`/${lang}/onboarding`)) {
      // Option A: Allow access even if onboarding is completed (user can revisit)
      // This is the MVP approach - we allow it
      const response = await next();
      return withDevAuthHeader(response);
    }

    // Handle dashboard paths
    if (pathname.startsWith(`/${lang}/dashboard`)) {
      // If onboarding not completed, redirect to onboarding
      if (!user.onboarding_completed) {
        return redirect(`/${lang}/onboarding/${user.account_type}`, 302);
      }

      // Enforce role prefix: if URL has a role but it doesn't match user's role, redirect
      const roleMatch = pathname.match(/\/dashboard\/(artist|studio|model)/);
      if (roleMatch) {
        const urlRole = roleMatch[1];
        if (urlRole !== user.account_type) {
          return withDevAuthHeader(redirect(`/${lang}/dashboard/${user.account_type}`, 302));
        }
      }

      const response = await next();
      return withDevAuthHeader(response);
    }
  }

  // Default: allow access
  const response = await next();
  return withDevAuthHeader(response);
};

