/// <reference types="vitest" />
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
        "codelists-version": "assets/src/scripts/codelists-version.js",
      },
    },
    outDir: "assets/dist",
    emptyOutDir: true,
  },
  server: {
    origin: "http://localhost:5173",
  },
  clearScreen: false,
  plugins: [react()],
  test: {
    coverage: {
      provider: "v8",
      lines: 90,
      functions: 90,
      branches: 90,
      statements: -10,
    },
    environment: "jsdom",
    globals: true,
    root: "./assets/src/scripts",
  },
});
