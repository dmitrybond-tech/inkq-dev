/**
 * Frontend configuration utilities.
 * Reads environment variables from Vite/Astro.
 */

/**
 * Get the backend API URL from environment variables.
 * Throws an error in development if not set.
 */
export function getApiUrl(): string {
  const apiUrl = import.meta.env.INKQ_API_URL;
  
  if (!apiUrl) {
    if (import.meta.env.DEV) {
      throw new Error(
        'INKQ_API_URL is not set. Please add it to your .env file:\n' +
        'INKQ_API_URL=http://localhost:8000'
      );
    }
    // In production, you might want to use a default or throw
    throw new Error('INKQ_API_URL is not configured');
  }
  
  return apiUrl;
}

