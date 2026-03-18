import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    host: "0.0.0.0",
    allowedHosts: true,
    proxy: {
      "/auth": { target: "http://backend:8000", changeOrigin: true },
      "/artists": { target: "http://backend:8000", changeOrigin: true },
      "/recommendations": { target: "http://backend:8000", changeOrigin: true },
      "/health": { target: "http://backend:8000", changeOrigin: true },
    },
  },
});
