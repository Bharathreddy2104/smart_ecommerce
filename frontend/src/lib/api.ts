export const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? 'http://127.0.0.1:8000';
const MEDIA_BASE = process.env.NEXT_PUBLIC_DJANGO_MEDIA_URL ?? 'http://127.0.0.1:8001/media';
const INR_FORMATTER = new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR' });

export function formatCurrency(amount: number | string): string {
  return INR_FORMATTER.format(Number(amount));
}

export function mediaUrl(path?: string | null): string | null {
  if (!path) return null;
  if (/^https?:\/\//i.test(path)) return path;
  return `${MEDIA_BASE}/${path.replace(/^\/+/, '')}`;
}

type ApiError = { detail?: string | Record<string, string[]> };

export class ApiRequestError extends Error {
  constructor(message: string, public readonly status: number) {
    super(message);
    this.name = 'ApiRequestError';
  }
}

export async function apiFetch<T>(path: string, options: RequestInit = {}): Promise<T> {
  const headers = new Headers(options.headers);
  if (options.body && !(options.body instanceof FormData) && !headers.has('Content-Type')) {
    headers.set('Content-Type', 'application/json');
  }
  if (typeof window !== 'undefined') {
    const token = localStorage.getItem('smart_ecom_token');
    if (token && !headers.has('Authorization')) {
      headers.set('Authorization', 'Bearer ' + token);
    }
  }

  const response = await fetch(`${API_BASE}${path}`, { ...options, headers });
  const data = await response.json().catch(() => null) as T & ApiError | null;
  if (!response.ok) {
    const detail = data?.detail;
    const message = typeof detail === 'string' ? detail : detail ? JSON.stringify(detail) : 'Request failed.';
    if (response.status === 401 && typeof window !== 'undefined') {
      localStorage.removeItem('smart_ecom_token');
    }
    throw new ApiRequestError(message, response.status);
  }
  return data as T;
}
