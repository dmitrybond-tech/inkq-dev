import type { APIRoute } from 'astro';
import { getApiUrl } from '../../shared/config';

export const prerender = false;

function resolveBackendUrl(path: string, url: URL): string {
  const apiBase = getApiUrl();
  if (apiBase) {
    return `${apiBase}${path}`;
  }
  return new URL(path, url.origin).toString();
}

export const POST: APIRoute = async ({ request, cookies, url }) => {
  // Only accept POST
  if (request.method !== 'POST') {
    return new Response(
      JSON.stringify({ detail: 'Method not allowed' }),
      { status: 405, headers: { 'Content-Type': 'application/json' } }
    );
  }

  // Extract language from Referer header or default to 'en'
  const referer = request.headers.get('referer') || '';
  const langMatch = referer.match(/\/(en|ru)\//);
  let lang = langMatch ? langMatch[1] : 'en';

  // Fallback: try to extract from form data if available
  try {
    const formData = await request.formData();
    const formLang = formData.get('lang');
    if (formLang && (formLang === 'en' || formLang === 'ru')) {
      lang = formLang as string;
    }
  } catch {
    // If form data parsing fails, use Referer-based lang
  }

  try {
    // Get token from cookie
    const cookieName = 'inkq_session';
    const token = cookies.get(cookieName)?.value;

    if (!import.meta.env.PROD) {
      console.info(`[dev][signout] cookie present before signout: ${token ? 'yes' : 'no'}`);
    }

    // If token exists, call backend signout (best-effort; ignore failures)
    if (token) {
      try {
        const signoutUrl = resolveBackendUrl('/api/v1/auth/signout', url);
        const resp = await fetch(signoutUrl, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`,
          },
        });
        const text = await resp.text();
        if (!import.meta.env.PROD) {
          console.info(
            '[dev][signout] backend signout response',
            JSON.stringify({
              url: signoutUrl,
              status: resp.status,
              textPreview: text.slice(0, 200),
            })
          );
        }
      } catch (error) {
        // Even if backend call fails, clear the cookie
        if (!import.meta.env.PROD) {
          console.error('Error calling backend signout:', error);
        }
      }
    }

    // Clear cookie
    const isProduction = import.meta.env.PROD;
    cookies.set(cookieName, '', {
      httpOnly: true,
      secure: isProduction,
      sameSite: 'lax',
      path: '/',
      maxAge: 0,
    });

    if (!import.meta.env.PROD) {
      console.info('[dev][signout] cookie cleared: yes');
    }

    // Redirect to localized home
    const redirectPath = `/${lang}`;
    return Response.redirect(new URL(redirectPath, url.origin), 302);
  } catch (error: any) {
    // Even on error, try to clear cookie and redirect
    const cookieName = 'inkq_session';
    const isProduction = import.meta.env.PROD;
    cookies.set(cookieName, '', {
      httpOnly: true,
      secure: isProduction,
      sameSite: 'lax',
      path: '/',
      maxAge: 0,
    });

    return Response.redirect(new URL(`/${lang}`, url.origin), 302);
  }
};

