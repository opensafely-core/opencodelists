import { defineConfig } from "vite";
import react from "@vitejs/plugin-react-swc";

export default defineConfig({
  base: "/static/",
  build: {
    manifest: true,
    rollupOptions: {
      input: {
        base: "assets/src/scripts/base.js",
        builder: "assets/src/scripts/builder/index.jsx",
        codelist: "assets/src/scripts/codelist.js",
        tree: "assets/src/scripts/tree/index.jsx",
      },
    },
    outDir: "assets/dist",
    emptyOutDir: false,
  },
  server: {
    origin: "http://localhost:5173",
  },
  clearScreen: false,
  plugins: [react()],
});
