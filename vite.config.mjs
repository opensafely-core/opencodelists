/// <reference types="vitest" />
import tailwindcss from "@tailwindcss/vite";
import react from "@vitejs/plugin-react-swc";
import { defineConfig } from "vite";
import liveReload from "vite-plugin-live-reload";

export default defineConfig(({ mode }) => ({
  base: "/static/",
  build: {
    manifest: true,
    rollupOptions: {
      input: {
        base: "assets/src/scripts/base.js",
        builder: "assets/src/scripts/builder/index.tsx",
        codelist: "assets/src/scripts/codelist.js",
        "codelists-list": "assets/src/scripts/codelists-list.js",
        tree: "assets/src/scripts/tree/index.tsx",
        "codelists-version": "assets/src/scripts/codelists-version.js",
        tw: "assets/src/scripts/tw.js",
        "feedback-form": "assets/src/scripts/feedback-form.js",
      },
    },
    outDir: "assets/dist",
    emptyOutDir: true,
  },
  server: {
    origin: "http://localhost:5173",
  },
  clearScreen: false,
  plugins: [
    mode !== "test"
      ? liveReload(["templates/**/*.html", "assets/src/styles/base.css"], {
          alwaysReload: true,
        })
      : undefined,
    react(),
    tailwindcss(),
  ],
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
    setupFiles: ["__tests__/vitest.setup.js"],
  },
}));
