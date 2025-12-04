import type { APIRoute } from 'astro';
import { callBackendJson } from '../../../../shared/api/client';

export const POST: APIRoute = async ({ request, cookies, url }) => {
  // Only accept POST
  if (request.method !== 'POST') {
    return new Response(
      JSON.stringify({ detail: 'Method not allowed' }),
      { status: 405, headers: { 'Content-Type': 'application/json' } }
    );
  }

  // Extract language from form data, or fall back to URL parsing
  let lang = 'en';
  try {
    const formData = await request.formData();
    const formLang = formData.get('lang');
    if (formLang && (formLang === 'en' || formLang === 'ru')) {
      lang = formLang as string;
    }
  } catch {
    // If form data parsing fails, try URL parsing
    const pathname = url.pathname;
    const langMatch = pathname.match(/^\/(en|ru)/);
    if (langMatch) {
      lang = langMatch[1];
    }
  }

  // Fallback to URL parsing if form data didn't provide lang
  if (lang === 'en') {
    const pathname = url.pathname;
    const langMatch = pathname.match(/^\/(en|ru)/);
    if (langMatch) {
      lang = langMatch[1];
    }
  }

  try {
    // Get token from cookie
    const cookieName = 'inkq_session';
    const token = cookies.get(cookieName)?.value;

    // If token exists, call backend signout
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
        console.error('Error calling backend signout:', error);
      }
    }

    // Clear cookie
    cookies.delete(cookieName, {
      path: '/',
    });

    // Redirect to localized public page (home)
    const redirectPath = `/${lang}`;
    return Response.redirect(new URL(redirectPath, url.origin), 303);
  } catch (error: any) {
    // Even on error, try to clear cookie and redirect
    const cookieName = 'inkq_session';
    cookies.delete(cookieName, { path: '/' });

    return Response.redirect(new URL(`/${lang}`, url.origin), 303);
  }
};

