import type { APIRoute } from 'astro';
import { callBackendJsonParse } from '../../../../shared/api/client';

export const prerender = false;

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

    // Call backend
    const data = await callBackendJsonParse<{
      access_token: string;
      user: {
        id: number;
        email: string;
        username: string;
        account_type: string;
        onboarding_completed: boolean;
      };
    }>('/api/v1/auth/signin', {
      method: 'POST',
      body: JSON.stringify({
        login: loginValue,
        password: passwordValue,
      }),
    });

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
    // Handle errors
    const errorMessage = error.message || 'An error occurred during signin';
    
    // Map common error messages
    let status = 500;
    let detail = 'Server error';
    
    if (errorMessage.includes('invalid_credentials')) {
      status = 401;
      detail = 'Invalid login or password';
    } else if (errorMessage.includes('400') || errorMessage.includes('Bad Request')) {
      status = 400;
      detail = errorMessage;
    } else if (errorMessage.includes('401') || errorMessage.includes('Unauthorized')) {
      status = 401;
      detail = 'Invalid login or password';
    } else if (errorMessage.includes('403') || errorMessage.includes('Forbidden')) {
      status = 403;
      detail = 'Access denied';
    }

    // Extract language from Referer header or default to 'en'
    const referer = request.headers.get('referer') || '';
    const langMatch = referer.match(/\/(en|ru)\//);
    const lang = langMatch ? langMatch[1] : 'en';

    // Redirect back to signin with error
    const redirectUrl = new URL(`/${lang}/signin`, url.origin);
    redirectUrl.searchParams.set('error', detail);
    
    return Response.redirect(redirectUrl, 302);
  }
};

