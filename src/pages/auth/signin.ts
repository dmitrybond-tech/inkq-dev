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

  try {
    // Parse form data or JSON
    const contentType = request.headers.get('content-type') || '';
    let body: { login?: string; email?: string; password?: string };

    if (contentType.includes('application/json')) {
      body = await request.json();
    } else {
      const formData = await request.formData();
      body = {
        login: (formData.get('login') ?? formData.get('email')) as string | null | undefined,
        email: formData.get('email') as string | null | undefined,
        password: formData.get('password') as string | null | undefined,
      };
    }

    const loginValue = (body.login ?? body.email ?? '').toString().trim();
    const passwordValue = (body.password ?? '').toString().trim();

    if (!import.meta.env.PROD) {
      const hasLogin = !!loginValue;
      const hasPassword = !!passwordValue;
      console.info(
        `[dev][signin] content-type="${contentType}", parsed login present=${hasLogin}, password present=${hasPassword}`
      );
    }

    // Defensive validation: required fields must be present
    if (!loginValue || !passwordValue) {
      if (!import.meta.env.PROD) {
        console.warn('[signin] missing login/email or password in request body');
      }

      // Extract language from Referer header or default to 'en'
      const referer = request.headers.get('referer') || '';
      const langMatch = referer.match(/\/(en|ru)\//);
      const lang = langMatch ? langMatch[1] : 'en';

      const redirectUrl = new URL(`/${lang}/signin`, url.origin);
      redirectUrl.searchParams.set('error', 'Login and password are required');

      return Response.redirect(redirectUrl, 302);
    }

    const backendUrl = resolveBackendUrl('/api/v1/auth/signin', url);

    const resp = await fetch(backendUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        login: loginValue,
        password: passwordValue,
      }),
    });

    const text = await resp.text();
    let data: any = null;
    try {
      data = text ? JSON.parse(text) : null;
    } catch {
      // Non-JSON response, keep data as null
    }

    if (!import.meta.env.PROD) {
      console.info(
        '[dev][signin] backend response',
        JSON.stringify({
          url: backendUrl,
          status: resp.status,
          // Truncate text to avoid noisy logs; do not log credentials or tokens
          textPreview: text.slice(0, 200),
        })
      );
    }

    if (!resp.ok) {
      // Extract language from Referer header or default to 'en'
      const referer = request.headers.get('referer') || '';
      const langMatch = referer.match(/\/(en|ru)\//);
      const lang = langMatch ? langMatch[1] : 'en';

      let detail = 'Server error';

      if (resp.status === 401) {
        detail = 'Invalid login or password';
      } else if (resp.status === 422) {
        const d = data && typeof data === 'object' ? (data as any) : null;
        if (d?.detail) {
          if (typeof d.detail === 'string') {
            detail = d.detail;
          } else {
            detail = 'Validation error';
          }
        } else {
          detail = 'Validation error';
        }
      }

      const redirectUrl = new URL(`/${lang}/signin`, url.origin);
      redirectUrl.searchParams.set('error', detail);
      return Response.redirect(redirectUrl, 302);
    }

    if (!data || !data.access_token || !data.user) {
      if (!import.meta.env.PROD) {
        console.error('[dev][signin] missing access_token or user in backend response');
      }

      // Extract language from Referer header or default to 'en'
      const referer = request.headers.get('referer') || '';
      const langMatch = referer.match(/\/(en|ru)\//);
      const lang = langMatch ? langMatch[1] : 'en';

      const redirectUrl = new URL(`/${lang}/signin`, url.origin);
      redirectUrl.searchParams.set('error', 'Server error');
      return Response.redirect(redirectUrl, 302);
    }

    // Set cookie
    const cookieName = 'inkq_session';
    const isProduction = import.meta.env.PROD;
    const maxAge = 7 * 24 * 60 * 60; // 7 days in seconds

    cookies.set(cookieName, data.access_token, {
      httpOnly: true,
      secure: isProduction,
      sameSite: 'lax',
      path: '/',
      maxAge: maxAge,
    });

    if (!import.meta.env.PROD) {
      console.info('[dev][signin] cookie set: yes');
    }

    // Extract language from Referer header or default to 'en'
    const referer = request.headers.get('referer') || '';
    const langMatch = referer.match(/\/(en|ru)\//);
    const lang = langMatch ? langMatch[1] : 'en';

    // Determine redirect target
    let redirectPath: string;
    if (!data.user.onboarding_completed) {
      redirectPath = `/${lang}/onboarding/${data.user.account_type}`;
    } else {
      redirectPath = `/${lang}/dashboard/${data.user.account_type}`;
    }

    // Return redirect response
    return Response.redirect(new URL(redirectPath, url.origin), 302);
  } catch (error: any) {
    if (!import.meta.env.PROD) {
      console.error('[dev][signin] unexpected error', {
        message: error?.message,
      });
    }

    // Extract language from Referer header or default to 'en'
    const referer = request.headers.get('referer') || '';
    const langMatch = referer.match(/\/(en|ru)\//);
    const lang = langMatch ? langMatch[1] : 'en';

    // Redirect back to signin with error
    const redirectUrl = new URL(`/${lang}/signin`, url.origin);
    redirectUrl.searchParams.set('error', 'Server error');
    
    return Response.redirect(redirectUrl, 302);
  }
};

