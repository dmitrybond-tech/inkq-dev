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
    let body: {
      email?: string;
      password?: string;
      username?: string;
      accountType?: string;
      account_type?: string;
    };
    
    if (contentType.includes('application/json')) {
      body = await request.json();
    } else {
      const formData = await request.formData();
      body = {
        email: formData.get('email') as string | null | undefined,
        password: formData.get('password') as string | null | undefined,
        username: formData.get('username') as string | null | undefined,
        accountType: formData.get('accountType') as string | null | undefined,
      };
    }

    const email = (body.email ?? '').toString().trim();
    const password = (body.password ?? '').toString().trim();
    const username = (body.username ?? '').toString().trim();
    const account_type_raw = (body.accountType ?? body.account_type ?? '').toString().trim();

    if (!import.meta.env.PROD) {
      const hasEmail = !!email;
      const hasPassword = !!password;
      const hasUsername = !!username;
      const hasAccountType = !!account_type_raw;
      console.info(
        `[dev][signup] content-type="${contentType}", email present=${hasEmail}, password present=${hasPassword}, username present=${hasUsername}, account_type present=${hasAccountType}`
      );
    }

    // Validate required fields (defensive)
    if (!email || !password || !username || !account_type_raw) {
      // Extract language from Referer header or default to 'en'
      const referer = request.headers.get('referer') || '';
      const langMatch = referer.match(/\/(en|ru)\//);
      const lang = langMatch ? langMatch[1] : 'en';

      const redirectUrl = new URL(`/${lang}/signup`, url.origin);
      redirectUrl.searchParams.set('error', 'All fields are required');

      return Response.redirect(redirectUrl, 302);
    }

    // Normalize account_type
    const account_type = account_type_raw;
    if (!['artist', 'studio', 'model'].includes(account_type)) {
      const referer = request.headers.get('referer') || '';
      const langMatch = referer.match(/\/(en|ru)\//);
      const lang = langMatch ? langMatch[1] : 'en';

      const redirectUrl = new URL(`/${lang}/signup`, url.origin);
      redirectUrl.searchParams.set('error', 'Invalid account type');

      return Response.redirect(redirectUrl, 302);
    }

    const signupUrl = resolveBackendUrl('/api/v1/auth/signup', url);

    const signupResp = await fetch(signupUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        email,
        password,
        username,
        account_type,
      }),
    });

    const signupText = await signupResp.text();
    let signupData: any = null;
    try {
      signupData = signupText ? JSON.parse(signupText) : null;
    } catch {
      // Non-JSON response, keep data as null
    }

    if (!import.meta.env.PROD) {
      console.info(
        '[dev][signup] backend signup response',
        JSON.stringify({
          url: signupUrl,
          status: signupResp.status,
          textPreview: signupText.slice(0, 200),
        })
      );
    }

    if (!signupResp.ok) {
      const referer = request.headers.get('referer') || '';
      const langMatch = referer.match(/\/(en|ru)\//);
      const lang = langMatch ? langMatch[1] : 'en';

      let detail = 'Server error';

      if (signupResp.status === 422) {
        const d = signupData && typeof signupData === 'object' ? (signupData as any) : null;
        if (d?.detail) {
          if (typeof d.detail === 'string') {
            detail = d.detail;
          } else {
            detail = 'Validation error';
          }
        } else {
          detail = 'Validation error';
        }
      } else if (signupResp.status === 409) {
        detail = 'Email or username already exists';
      }

      const redirectUrl = new URL(`/${lang}/signup`, url.origin);
      redirectUrl.searchParams.set('error', detail);
      return Response.redirect(redirectUrl, 302);
    }

    // After successful signup, sign in the user
    const signinUrl = resolveBackendUrl('/api/v1/auth/signin', url);

    const signinResp = await fetch(signinUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        login: email,
        password,
      }),
    });

    const signinText = await signinResp.text();
    let signinData: any = null;
    try {
      signinData = signinText ? JSON.parse(signinText) : null;
    } catch {
      // Non-JSON response, keep data as null
    }

    if (!import.meta.env.PROD) {
      console.info(
        '[dev][signup] backend signin response',
        JSON.stringify({
          url: signinUrl,
          status: signinResp.status,
          textPreview: signinText.slice(0, 200),
        })
      );
    }

    if (!signinResp.ok || !signinData || !signinData.access_token || !signinData.user) {
      const referer = request.headers.get('referer') || '';
      const langMatch = referer.match(/\/(en|ru)\//);
      const lang = langMatch ? langMatch[1] : 'en';

      let detail = 'Server error';

      if (signinResp.status === 401) {
        detail = 'Invalid login or password';
      } else if (signinResp.status === 422) {
        const d = signinData && typeof signinData === 'object' ? (signinData as any) : null;
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

    // Set cookie
    const cookieName = 'inkq_session';
    const isProduction = import.meta.env.PROD;
    const maxAge = 7 * 24 * 60 * 60; // 7 days in seconds

    cookies.set(cookieName, signinData.access_token, {
      httpOnly: true,
      secure: isProduction,
      sameSite: 'lax',
      path: '/',
      maxAge: maxAge,
    });

    // Extract language from Referer header or default to 'en'
    const referer = request.headers.get('referer') || '';
    const langMatch = referer.match(/\/(en|ru)\//);
    const lang = langMatch ? langMatch[1] : 'en';

    // Determine redirect target
    let redirectPath: string;
    if (!signinData.user.onboarding_completed) {
      redirectPath = `/${lang}/onboarding/${signinData.user.account_type}`;
    } else {
      redirectPath = `/${lang}/dashboard/${signinData.user.account_type}`;
    }

    // Return redirect response
    return Response.redirect(new URL(redirectPath, url.origin), 302);
  } catch (error: any) {
    if (!import.meta.env.PROD) {
      console.error('[dev][signup] unexpected error', {
        message: error?.message,
      });
    }

    // Extract language from Referer header or default to 'en'
    const referer = request.headers.get('referer') || '';
    const langMatch = referer.match(/\/(en|ru)\//);
    const lang = langMatch ? langMatch[1] : 'en';

    // Redirect back to signup with error
    const redirectUrl = new URL(`/${lang}/signup`, url.origin);
    redirectUrl.searchParams.set('error', 'Server error');
    
    return Response.redirect(redirectUrl, 302);
  }
};

