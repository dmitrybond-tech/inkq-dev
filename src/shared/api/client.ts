/**
 * Shared HTTP client for calling the backend API.
 */
import { getApiUrl } from '../config';

export interface ApiError {
  detail: string;
}

/**
 * Call the backend API with JSON request/response.
 * 
 * @param path - API path (e.g., '/api/v1/auth/signin')
 * @param options - Fetch options (method, body, headers, etc.)
 * @returns Response object
 * @throws Error if the request fails
 */
export async function callBackendJson(
  path: string,
  options: RequestInit = {}
): Promise<Response> {
  const apiUrl = getApiUrl();
  const url = `${apiUrl}${path}`;
  
  const defaultHeaders: HeadersInit = {
    'Content-Type': 'application/json',
  };
  
  // Merge headers
  const headers = {
    ...defaultHeaders,
    ...(options.headers || {}),
  };
  
  const response = await fetch(url, {
    ...options,
    headers,
  });
  
  return response;
}

/**
 * Call the backend API and parse JSON response.
 * 
 * @param path - API path
 * @param options - Fetch options
 * @returns Parsed JSON response
 * @throws Error if the request fails or response is not JSON
 */
export async function callBackendJsonParse<T = any>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const response = await callBackendJson(path, options);
  
  if (!response.ok) {
    let errorDetail = 'Request failed';
    try {
      const errorData = await response.json();
      errorDetail = errorData.detail || errorDetail;
    } catch {
      // If response is not JSON, use status text
      errorDetail = response.statusText || errorDetail;
    }
    throw new Error(errorDetail);
  }
  
  return response.json();
}

/**
 * Call the backend API with FormData (for file uploads).
 * Includes credentials (cookies) for authentication.
 * 
 * @param path - API path
 * @param formData - FormData object
 * @param options - Additional fetch options
 * @returns Response object
 */
export async function callBackendFormData(
  path: string,
  formData: FormData,
  options: RequestInit = {}
): Promise<Response> {
  const apiUrl = getApiUrl();
  const url = `${apiUrl}${path}`;
  
  const response = await fetch(url, {
    ...options,
    method: options.method || 'POST',
    body: formData,
    credentials: 'include', // Include cookies for authentication
  });
  
  return response;
}

