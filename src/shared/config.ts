/**
 * Frontend configuration utilities.
 * Reads environment variables from Vite/Astro.
 */

/**
 * Get the backend API URL from environment variables.
 * Supports both PUBLIC_API_BASE_URL (for Docker/preprod) and INKQ_API_URL (for dev).
 * In preprod, PUBLIC_API_BASE_URL should be empty string so paths like /api/v1/... work with Caddy reverse proxy.
 * 
 * Logic:
 * - In dev (import.meta.env.DEV === true): returns INKQ_API_URL (e.g., "http://localhost:8000")
 * - In prod/preprod (!import.meta.env.DEV): returns PUBLIC_API_BASE_URL (empty string for relative paths)
 * 
 * IMPORTANT: This function does NOT add any "/api" prefix. The caller must construct URLs as:
 * `${getApiUrl()}/api/v1/...`
 */
export function getApiUrl(): string {
  // In development mode, use INKQ_API_URL
  if (import.meta.env.DEV) {
    const apiUrl = import.meta.env.INKQ_API_URL;
    if (!apiUrl) {
      throw new Error(
        'INKQ_API_URL is not set. Please add it to your .env file:\n' +
        'INKQ_API_URL=http://localhost:8000'
      );
    }
    return apiUrl;
  }
  
  // In production/preprod, use PUBLIC_API_BASE_URL
  // Empty string means use relative paths (for Caddy reverse proxy)
  const publicApiBaseUrl = import.meta.env.PUBLIC_API_BASE_URL;
  // Return empty string if undefined or explicitly set to empty
  return publicApiBaseUrl ?? '';
}

