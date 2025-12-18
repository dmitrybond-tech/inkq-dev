import type { APIRoute } from 'astro';
import { callBackendJson } from '../../shared/api/client';

export const prerender = false;

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
        await callBackendJson('/api/v1/auth/signout', {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
          },
        });
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

