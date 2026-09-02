import { defineConfig, type ViteDevServer } from "vite";
import react from "@vitejs/plugin-react-swc";
import path from "path";
import type { IncomingMessage, ServerResponse } from "http";
import { componentTagger } from "lovable-tagger";

// https://vitejs.dev/config/
const base = "/ai-interview/";

export default defineConfig(({ mode }) => ({
  envDir: path.resolve(__dirname, ".."),
  base,
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
  plugins: [
    {
      name: "redirect-dev-base-path",
      configureServer(server: ViteDevServer) {
        const baseNoSlash = base.replace(/\/$/, "");
        server.middlewares.use((req: IncomingMessage, res: ServerResponse, next: () => void) => {
          const url = req.url || "/";

          // "/ai-interview" (no trailing slash) → "/ai-interview/" so the base
          // path resolves the same with or without the slash.
          if (url === baseNoSlash) {
            res.statusCode = 302;
            res.setHeader("Location", base);
            res.end();
            return;
          }

          if (!url.startsWith("/app")) {
            next();
            return;
          }

          res.statusCode = 302;
          res.setHeader("Location", `${baseNoSlash}${url}`);
          res.end();
        });
      },
    },
    react(),
    mode === "development" && componentTagger(),
  ].filter(Boolean),
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
}));
