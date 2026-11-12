import Constants from "expo-constants";
import { getBaseUrl } from "./storage";

let cachedBaseUrl: string | null = null;

export function defaultBaseUrl(): string {
  const hostUri = Constants.expoConfig?.hostUri;
  const host = hostUri?.split(":")[0];
  return host ? `http://${host}:5000` : "http://192.168.1.25:5000";
}

export async function resolveBaseUrl(): Promise<string> {
  if (cachedBaseUrl) return cachedBaseUrl;
  const stored = await getBaseUrl();
  cachedBaseUrl = stored || defaultBaseUrl();
  return cachedBaseUrl;
}

export function clearBaseUrlCache(): void {
  cachedBaseUrl = null;
}

export class ApiError extends Error {
  status: number;
  constructor(message: string, status: number) {
    super(message);
    this.status = status;
  }
}

async function handleResponse<T>(res: Response): Promise<T> {
  const text = await res.text();
  let data: any = {};
  if (text) {
    try {
      data = JSON.parse(text);
    } catch {
      data = {};
    }
  }
  if (!res.ok) {
    throw new ApiError(data.error || `Request failed (${res.status})`, res.status);
  }
  return data as T;
}

const REQUEST_TIMEOUT_MS = 8000;

async function fetchWithTimeout(url: string, options: RequestInit): Promise<Response> {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);
  try {
    return await fetch(url, { ...options, signal: controller.signal });
  } catch (e: any) {
    if (e?.name === "AbortError") {
      throw new ApiError(
        "Server did not respond. Make sure Flask is running on your PC and the server address is your PC's LAN IP.",
        0
      );
    }
    throw new ApiError("Could not reach the server. Check your Wi-Fi connection.", 0);
  } finally {
    clearTimeout(timer);
  }
}

export async function apiGet<T>(path: string): Promise<T> {
  const base = await resolveBaseUrl();
  const res = await fetchWithTimeout(`${base}${path}`, {
    method: "GET",
    credentials: "include",
  });
  return handleResponse<T>(res);
}

export async function apiPost<T>(path: string, body: object): Promise<T> {
  const base = await resolveBaseUrl();
  const res = await fetchWithTimeout(`${base}${path}`, {
    method: "POST",
    credentials: "include",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  return handleResponse<T>(res);
}

export async function apiUpload<T>(
  path: string,
  form: FormData
): Promise<T> {
  const base = await resolveBaseUrl();
  const res = await fetchWithTimeout(`${base}${path}`, {
    method: "POST",
    credentials: "include",
    body: form,
  });
  return handleResponse<T>(res);
}
