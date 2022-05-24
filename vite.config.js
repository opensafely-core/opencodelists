import legacy from "@vitejs/plugin-legacy";
import { defineConfig } from "vite";

export default defineConfig({
  base: "/static/bundle/",
  build: {
    manifest: true,
    rollupOptions: {
      input: {
        builder: "/assets/src/scripts/builder/index.jsx",
        codelist: "/assets/src/scripts/codelist.js",
        main: "/assets/src/scripts/main.js",
        tree: "/assets/src/scripts/tree/index.jsx",
      },
    },
    outDir: "assets/dist/bundle",
    emptyOutDir: true,
  },
  clearScreen: false,
  plugins: [
    legacy({
      targets: ["last 2 versions, not dead, > 2%"],
    }),
  ],
  test: {
    globals: true,
    environment: "jsdom",
    setupFiles: "./assets/src/scripts/__tests__/setup.js",
  },
});
