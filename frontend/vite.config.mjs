import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";
import Components from "unplugin-vue-components/vite";
import Icons from "unplugin-icons/vite";
import IconsResolver from "unplugin-icons/resolver";
import path from "path";

export default defineConfig({
  base: "/assets/portal_app/frontend/",
  plugins: [
    vue(),

    Components({
      resolvers: [
        IconsResolver({
          prefix: false,
          enabledCollections: ["lucide"],
        }),
      ],
    }),

    Icons({
      compiler: "vue3",
      autoInstall: true,
      collections: ["lucide"],
      defaultClass: "inline-block",
    }),
  ],

  resolve: {
    alias: {
      "@": path.resolve(__dirname, "src"),
    },
  },

  build: {
    sourcemap: false,
    outDir: "../portal_app/public/frontend",
    emptyOutDir: true,
    chunkSizeWarningLimit: 1000,
    rollupOptions: {
      input: path.resolve(__dirname, "index.html"),
      output: {
        // Entry + css keep fixed names: www/portal_app.html and the desk page
        // hardcode them, and www/portal_app.py cache-busts them with ?v=<build>.
        entryFileNames: "frontend.js",
        assetFileNames: "assets/[name].[ext]",
        // Chunks ARE content-hashed. They are only referenced from inside the
        // entry bundle, which vite rewrites each build, so nothing hardcodes
        // them — and without a hash a lazy-loaded page like Files.js keeps its
        // filename forever and browsers serve the old one after every deploy.
        chunkFileNames: "chunks/[name]-[hash].js",
      },
    },
  },
});
