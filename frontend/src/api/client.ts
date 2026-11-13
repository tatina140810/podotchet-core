const TOKEN_KEY = "pc_token";

export class ApiError extends Error {
  constructor(public status: number, public detail: unknown) {
    super(typeof detail === "string" ? detail : `HTTP ${status}`);
  }
  get code(): string | undefined {
    return typeof this.detail === "object" && this.detail ? (this.detail as { code?: string }).code : undefined;
  }
}

export const token = {
  get: (): string | null => {
    try {
      return localStorage.getItem(TOKEN_KEY);
    } catch {
      return null;
    }
  },
  set: (v: string | null) => {
    try {
      if (v) localStorage.setItem(TOKEN_KEY, v);
      else localStorage.removeItem(TOKEN_KEY);
    } catch {
      /* ignore */
    }
  },
};

async function raw(path: string, init: RequestInit = {}): Promise<Response> {
  const headers = new Headers(init.headers);
  const tk = token.get();
  if (tk) headers.set("Authorization", `Bearer ${tk}`);
  if (init.body && typeof init.body === "string") headers.set("Content-Type", "application/json");
  const res = await fetch(path, { ...init, headers });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    if (res.status === 401) token.set(null);
    throw new ApiError(res.status, body.detail ?? body);
  }
  return res;
}

export async function api<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await raw(path, init);
  return res.status === 204 ? (undefined as T) : res.json();
}

export async function download(path: string, filename: string): Promise<void> {
  const blob = await (await raw(path)).blob();
  const url = URL.createObjectURL(blob);
  const a = Object.assign(document.createElement("a"), { href: url, download: filename });
  a.click();
  URL.revokeObjectURL(url);
}

export async function login(email: string, password: string): Promise<void> {
  const form = new URLSearchParams({ username: email, password });
  const res = await fetch("/api/auth/login", { method: "POST", body: form });
  if (!res.ok) throw new ApiError(res.status, "login");
  token.set((await res.json()).access_token);
}
