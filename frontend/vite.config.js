import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Dev: React runs on :5173 and forwards /api calls to Flask on :5000.
// Build: output goes to backend/static so Flask can serve the whole app on :5000.
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: { "/api": "http://localhost:5000" },
  },
  build: {
    outDir: "../backend/static",
    emptyOutDir: true,
  },
});
