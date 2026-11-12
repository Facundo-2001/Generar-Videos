/// <reference types="vite/client" />

interface ImportMetaEnv {
  /** URL publica del backend (api.py). Vacio = mismo origen. */
  readonly VITE_API_URL?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
