import { defineConfig } from "vite";

export default defineConfig({
  test: {
    globals: true,
    environment: "jsdom",
    setupFiles: "./assets/src/scripts/__tests__/setup.js",
  },
});
