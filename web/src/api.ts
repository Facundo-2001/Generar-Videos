// En local el front y el backend viven en el mismo origen (api.py sirve el
// build), asi que alcanza con rutas relativas. En produccion el front esta en
// Vercel y el backend en otro host: ahi hay que definir VITE_API_URL.
const API_BASE = (import.meta.env.VITE_API_URL ?? "").replace(/\/$/, "");

const TOKEN_KEY = "generar-videos:token";

export function getToken(): string {
  try {
    return localStorage.getItem(TOKEN_KEY) ?? "";
  } catch {
    return "";
  }
}

export function setToken(token: string): void {
  try {
    if (token) localStorage.setItem(TOKEN_KEY, token);
    else localStorage.removeItem(TOKEN_KEY);
  } catch {
    /* modo incognito o storage bloqueado: seguimos sin recordar la clave */
  }
}

/** Convierte una ruta del backend en una URL absoluta usable desde el navegador. */
export function apiUrl(path: string, conToken = false): string {
  const url = `${API_BASE}${path}`;
  const token = getToken();
  if (!conToken || !token) return url;
  return `${url}${url.includes("?") ? "&" : "?"}token=${encodeURIComponent(token)}`;
}

export class AuthError extends Error {}

export type ProviderOption = {
  id: string;
  label: string;
  cost: "gratis" | "pago";
  requires: string | null;
  note: string | null;
};

export type ProvidersResponse = {
  providers: {
    visuals: ProviderOption[];
    voice: ProviderOption[];
    music: ProviderOption[];
    sfx: ProviderOption[];
  };
  configured_keys: Record<string, boolean>;
};

export type JobEvent = {
  stage: string;
  message: string;
  at: string;
};

export type JobStatus = {
  id: string;
  state: "running" | "done" | "error";
  stage: string;
  events: JobEvent[];
  project_id: string | null;
  script_text: string | null;
  scene_count: number;
  render_progress: number | null;
  video_url: string | null;
  error: string | null;
};

export type SceneInput = {
  description: string;
  duration_s: number;
  sfx_prompt?: string | null;
  overlay_text?: string | null;
};

export type JobRequest = {
  mode: "prueba" | "real";
  topic: string;
  script_source: "ia" | "yo";
  script?: string | null;
  scenes: SceneInput[];
  visuals: string;
  voice: string;
  energetic_voice: boolean;
  music: string;
  music_mood: string;
  sfx: string;
  closing_text?: string | null;
  render: boolean;
};

async function request(path: string, init: RequestInit = {}) {
  const token = getToken();
  const response = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: {
      ...(init.headers ?? {}),
      ...(token ? { "X-App-Token": token } : {}),
    },
  });

  if (response.status === 401) {
    throw new AuthError("Clave de acceso invalida o faltante");
  }
  if (!response.ok) {
    const body = await response.text();
    throw new Error(`${response.status}: ${body.slice(0, 300)}`);
  }
  return response.json();
}

export async function fetchHealth(): Promise<{ ok: boolean; auth_required: boolean }> {
  return request("/api/health");
}

export async function fetchProviders(): Promise<ProvidersResponse> {
  return request("/api/providers");
}

export async function createJob(req: JobRequest): Promise<{ job_id: string }> {
  return request("/api/jobs", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(req),
  });
}

export async function fetchJob(jobId: string): Promise<JobStatus> {
  return request(`/api/jobs/${jobId}`);
}
