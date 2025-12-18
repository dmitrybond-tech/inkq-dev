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
 * Resolve current user from session cookie
 */
async function resolveUser(token: string): Promise<User | null> {
  try {
    const apiUrl = getApiUrl();
    const response = await fetch(`${apiUrl}/api/v1/auth/me`, {
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    });

    if (!import.meta.env.PROD) {
      console.info(`[dev][middleware] /api/v1/auth/me status: ${response.status}`);
    }

    if (response.ok) {
      return await response.json();
    }
    return null;
  } catch (error) {
    console.error('Error resolving user:', error);
    return null;
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

  if (!import.meta.env.PROD) {
    console.info(`[dev][middleware] cookie "${cookieName}" present: ${token ? 'yes' : 'no'}`);
  }

  // Resolve user if token exists
  let user: User | null = null;
  if (token) {
    user = await resolveUser(token);

    // If token is invalid, clear the cookie
    if (!user) {
      cookies.delete(cookieName, { path: '/' });
    } else {
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
      return redirect(redirectPath, 302);
    }
    // Otherwise allow access
    return next();
  }

  // Handle protected paths
  if (isProtectedPath(pathname)) {
    // If not authenticated, redirect to signin
    if (!user) {
      return redirect(`/${lang}/signin?reason=auth_required`, 302);
    }

    // Handle onboarding paths
    if (pathname.startsWith(`/${lang}/onboarding`)) {
      // Option A: Allow access even if onboarding is completed (user can revisit)
      // This is the MVP approach - we allow it
      return next();
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
          return redirect(`/${lang}/dashboard/${user.account_type}`, 302);
        }
      }

      return next();
    }
  }

  // Default: allow access
  return next();
};

