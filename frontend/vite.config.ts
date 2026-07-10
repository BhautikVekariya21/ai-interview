import { defineConfig } from "vite";
import react from "@vitejs/plugin-react-swc";
import path from "path";
import { componentTagger } from "lovable-tagger";

// https://vitejs.dev/config/
export default defineConfig(({ mode }) => ({
  base: "/ai-interview/",
  server: {
    host: "::",
    // Keep dev server on a different port from the FastAPI backend (8000)
    // so frontend and backend can run together locally.
    port: 5173,
    hmr: {
      overlay: false,
    },
  },
  build: {
    outDir: "dist",
    emptyOutDir: true,
  },
  plugins: [react(), mode === "development" && componentTagger()].filter(Boolean),
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
}));
