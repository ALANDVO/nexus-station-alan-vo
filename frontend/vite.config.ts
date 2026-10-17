import { defineConfig } from "vite";

export default defineConfig({
  server: {
    port: 5173,
    host: "127.0.0.1",
  },
  esbuild: {
    jsx: "automatic",
  },
  test: {
    environment: "jsdom",
    globals: true,
    setupFiles: "./src/setupTests.ts",
    css: true,
  },
});