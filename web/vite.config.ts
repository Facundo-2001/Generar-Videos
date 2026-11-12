import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// El backend (api.py) corre en :8000. En desarrollo proxeamos /api hacia alla,
// asi el front usa rutas relativas y el mismo build sirve cuando FastAPI
// entrega web/dist directamente.
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/api": {
        target: "http://127.0.0.1:8000",
        changeOrigin: true,
      },
    },
  },
});
