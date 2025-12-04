export function getSessionTokenFromCookie(): string | null {
  if (typeof document === 'undefined') return null;

  const cookie = document.cookie
    .split('; ')
    .find((c) => c.startsWith('inkq_session='));

  if (!cookie) return null;

  const [, value] = cookie.split('=');
  if (!value) return null;

  try {
    return decodeURIComponent(value);
  } catch {
    return value;
  }
}

export function buildAuthHeaders(
  extra: Record<string, string> = {},
): Record<string, string> {
  const token = getSessionTokenFromCookie();
  const base: Record<string, string> = { ...extra };

  if (token) {
    base.Authorization = `Bearer ${token}`;
  }

  return base;
}


