/**
 * Frontend configuration utilities.
 * Reads environment variables from Vite/Astro.
 */

/**
 * Get the backend API URL from environment variables.
 * Supports both PUBLIC_API_BASE_URL (for Docker/preprod) and INKQ_API_URL (for dev).
 * In preprod, PUBLIC_API_BASE_URL should be empty string so paths like /api/v1/... work with Caddy reverse proxy.
 * Throws an error in development if not set.
 */
export function getApiUrl(): string {
  // Check for PUBLIC_API_BASE_URL (used in Docker builds)
  // Empty string means use relative paths (for Caddy reverse proxy)
  const publicApiBaseUrl = import.meta.env.PUBLIC_API_BASE_URL;
  if (publicApiBaseUrl !== undefined) {
    return publicApiBaseUrl || ''; // Return empty string if explicitly set to empty
  }
  
  // Fallback to INKQ_API_URL for dev mode
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

