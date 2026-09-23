import { defineConfig } from "vite";
import { resolve } from "path";

export default defineConfig({
  build: {
    outDir: resolve(__dirname, "../custom_components/kubernetes/frontend"),
    emptyOutDir: true,
    lib: {
      entry: resolve(__dirname, "src/kubernetes-panel.ts"),
      formats: ["es"],
      fileName: () => "kubernetes-panel.js",
    },
    sourcemap: false,
    rolldownOptions: {
      output: {
        minify: {
          compress: true,
          mangle: true,
          codegen: { removeWhitespace: true },
        },
      },
    },
  },
});
