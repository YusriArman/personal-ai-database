import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

// The UI talks only to the local API. Nothing is fetched from the internet:
// no font CDN, no analytics, no remote scripts.
export default defineConfig({
  plugins: [react()],
  server: { port: 5173, proxy: { "/api": "http://127.0.0.1:8000" } },
});
