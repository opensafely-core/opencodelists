import legacy from "@vitejs/plugin-legacy";
import { defineConfig } from "vite";
import copy from "rollup-plugin-copy";

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
    copy({
      targets: [
        {
          src: "./node_modules/bootstrap/dist/js/bootstrap.bundle.min.*",
          dest: "./assets/dist/vendor",
        },
        {
          src: "./node_modules/bootstrap/dist/css/bootstrap.min.*",
          dest: "./assets/dist/vendor",
        },
        {
          src: "./node_modules/jquery/dist/jquery.slim.min.*",
          dest: "./assets/dist/vendor",
        },
        {
          src: "./node_modules/datatables.net/js/jquery.dataTables.min.js",
          dest: "./assets/dist/vendor",
        },
        {
          src: "./node_modules/datatables.net-bs4/js/dataTables.bootstrap4.min.js",
          dest: "./assets/dist/vendor",
        },
        {
          src: "./node_modules/datatables.net-bs4/css/dataTables.bootstrap4.min.css",
          dest: "./assets/dist/vendor",
        },
      ],
    }),
  ],
  test: {
    globals: true,
    environment: "happy-dom",
    setupFiles: "./assets/src/scripts/__tests__/setup.js",
  },
});
