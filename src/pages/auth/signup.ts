import type { APIRoute } from 'astro';
import { callBackendJsonParse } from '../../shared/api/client';

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

    // Call backend signup
    const userData = await callBackendJsonParse<{
      id: number;
      email: string;
      username: string;
      account_type: string;
      onboarding_completed: boolean;
    }>('/api/v1/auth/signup', {
      method: 'POST',
      body: JSON.stringify({
        email,
        password,
        username,
        account_type,
      }),
    });

    // After successful signup, sign in the user
    const signinData = await callBackendJsonParse<{
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
        login: email,
        password,
      }),
    });

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
    // Handle errors
    const errorMessage = error.message || 'An error occurred during signup';
    
    // Map common error messages
    let status = 500;
    let detail = 'Server error';
    
    if (errorMessage.includes('already exists')) {
      status = 400;
      detail = 'Email or username already exists';
    } else if (errorMessage.includes('Invalid account_type')) {
      status = 400;
      detail = 'Invalid account type';
    } else if (errorMessage.includes('400') || errorMessage.includes('Bad Request')) {
      status = 400;
      detail = errorMessage;
    } else if (errorMessage.includes('409') || errorMessage.includes('Conflict')) {
      status = 409;
      detail = 'Email or username already exists';
    } else if (errorMessage.includes('422') || errorMessage.includes('Unprocessable')) {
      status = 422;
      detail = 'Validation error';
    }

    // Extract language from Referer header or default to 'en'
    const referer = request.headers.get('referer') || '';
    const langMatch = referer.match(/\/(en|ru)\//);
    const lang = langMatch ? langMatch[1] : 'en';

    // Redirect back to signup with error
    const redirectUrl = new URL(`/${lang}/signup`, url.origin);
    redirectUrl.searchParams.set('error', detail);
    
    return Response.redirect(redirectUrl, 302);
  }
};

