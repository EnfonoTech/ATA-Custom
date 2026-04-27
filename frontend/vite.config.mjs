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
    outDir: "../portal_app/public/frontend",
    emptyOutDir: true,
    chunkSizeWarningLimit: 1000,
    rollupOptions: {
      input: path.resolve(__dirname, "index.html"),
      output: {
        entryFileNames: "frontend.js",
        chunkFileNames: "chunks/[name].js",
        assetFileNames: "assets/[name].[ext]",
      },
    },
  },
});
