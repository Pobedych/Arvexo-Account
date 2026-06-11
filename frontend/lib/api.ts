export const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export type ApiErrorBody = {
  error?: {
    code: string;
    message: string;
  };
};

export type AccountUser = {
  id: string;
  email: string | null;
  name: string | null;
  last_name: string | null;
  phone: string | null;
  avatar_url: string | null;
  role: string;
  connected_providers: string[];
  created_at: string;
};

export type AuthResponse = {
  user: AccountUser;
  access_token: string;
};

export type ProviderStatus = {
  google: boolean;
  yandex: boolean;
  telegram: boolean;
};

let accessToken: string | null = null;

export function setAccessToken(token: string | null) {
  accessToken = token;
}

export function getAccessToken() {
  return accessToken;
}

export async function apiRequest<T>(path: string, init: RequestInit = {}): Promise<T> {
  const headers = new Headers(init.headers);
  if (!headers.has("Content-Type") && init.body) {
    headers.set("Content-Type", "application/json");
  }
  if (accessToken) {
    headers.set("Authorization", `Bearer ${accessToken}`);
  }
  const response = await fetch(`${API_URL}${path}`, {
    ...init,
    headers,
    credentials: "include"
  });
  if (!response.ok) {
    const payload = (await response.json().catch(() => ({}))) as ApiErrorBody;
    throw new Error(payload.error?.message ?? "Не удалось выполнить запрос.");
  }
  return response.json() as Promise<T>;
}

export async function refreshAccessToken() {
  const data = await apiRequest<{ access_token: string }>("/auth/refresh", { method: "POST" });
  setAccessToken(data.access_token);
  return data.access_token;
}
