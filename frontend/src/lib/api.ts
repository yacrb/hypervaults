import { clearStoredToken, getStoredToken } from "./auth";

const rawBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || "/api";
const API_BASE_URL = rawBaseUrl.replace(/\/$/, "");

export type AuthResponse = {
  access_token: string;
  token_type: "bearer";
  expires_in_seconds: number;
};

export type User = {
  id: string;
  email: string;
  role: string;
  created_at: string;
};

export type VaultFile = {
  id: string;
  original_filename: string;
  size_bytes: number;
  content_type: string;
  created_at: string;
};

type ApiErrorBody = {
  detail?: string | { msg?: string }[];
};

async function request<T>(path: string, init: RequestInit = {}, includeAuth = true): Promise<T> {
  const headers = new Headers(init.headers);
  if (!(init.body instanceof FormData) && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }

  const token = getStoredToken();
  if (includeAuth && token) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers
  });

  if (response.status === 401 && includeAuth) {
    clearStoredToken();
  }

  if (!response.ok) {
    let message = "Request failed";
    try {
      const body = (await response.json()) as ApiErrorBody;
      if (typeof body.detail === "string") {
        message = body.detail;
      } else if (Array.isArray(body.detail) && body.detail[0]?.msg) {
        message = body.detail[0].msg;
      }
    } catch {
      message = response.statusText || message;
    }
    throw new Error(message);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return (await response.json()) as T;
}

export function signup(email: string, password: string, turnstileToken: string): Promise<AuthResponse> {
  return request<AuthResponse>(
    "/auth/signup",
    {
      method: "POST",
      body: JSON.stringify({ email, password, turnstile_token: turnstileToken })
    },
    false
  );
}

export function login(email: string, password: string, turnstileToken: string): Promise<AuthResponse> {
  return request<AuthResponse>(
    "/auth/login",
    {
      method: "POST",
      body: JSON.stringify({ email, password, turnstile_token: turnstileToken })
    },
    false
  );
}

export function getMe(): Promise<User> {
  return request<User>("/auth/me");
}

export function listFiles(): Promise<VaultFile[]> {
  return request<VaultFile[]>("/files");
}

export function uploadFile(file: File): Promise<VaultFile> {
  const formData = new FormData();
  formData.append("file", file);
  return request<VaultFile>("/files/upload", {
    method: "POST",
    body: formData
  });
}

export function requestDownloadUrl(fileId: string): Promise<{ download_url: string; expires_in_seconds: number }> {
  return request<{ download_url: string; expires_in_seconds: number }>(`/files/${fileId}/download`);
}

export function deleteFile(fileId: string): Promise<void> {
  return request<void>(`/files/${fileId}`, {
    method: "DELETE"
  });
}
