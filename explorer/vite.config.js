import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: { "@muse-tools": new URL("../tools", import.meta.url).pathname },
  },
});
