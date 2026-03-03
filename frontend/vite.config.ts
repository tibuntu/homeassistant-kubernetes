import { defineConfig } from "vite";
import { resolve } from "path";

export default defineConfig({
  build: {
    outDir: resolve(__dirname, "../custom_components/kubernetes/frontend"),
    emptyOutDir: true,
    lib: {
      entry: resolve(__dirname, "src/kubernetes-panel.ts"),
      name: "KubernetesPanel",
      formats: ["iife"],
      fileName: () => "kubernetes-panel.js",
    },
    rollupOptions: {
      output: {
        inlineDynamicImports: true,
      },
    },
    sourcemap: false,
    minify: "esbuild",
  },
});
