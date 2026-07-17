import { defineConfig } from "vite";
import react from "@vitejs/plugin-react-swc";
import path from "path";
import { componentTagger } from "lovable-tagger";

// https://vitejs.dev/config/
const base = "/ai-interview/";

export default defineConfig(({ mode }) => ({
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
      configureServer(server) {
        server.middlewares.use((req, res, next) => {
          if (!req.url?.startsWith("/app")) {
            next();
            return;
          }

          res.statusCode = 302;
          res.setHeader("Location", `${base.replace(/\/$/, "")}${req.url}`);
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
