import { defineConfig } from "vitest/config";

// O gateway (make run ou make sandbox) atende o WebSocket e o mapa do cartucho (ADR-0050).
const gateway = `http://127.0.0.1:${process.env.CAMPSVERSO_GATEWAY_PORT ?? "8765"}`;

export default defineConfig({
  // Os testes do Vitest ficam junto do código; os do navegador (e2e/), com o Playwright.
  test: { include: ["src/**/*.test.ts"] },
  // O Phaser sozinho tem cerca de 1,2 MB minificado (370 KB comprimido). A tela é servida em
  // 127.0.0.1, então um arquivo só não pesa; o limite fica acima dele para o aviso valer para o resto.
  build: { chunkSizeWarningLimit: 1600 },
  server: {
    host: "127.0.0.1",
    port: 5173,
    proxy: {
      "/ws": { target: gateway, ws: true },
      "/content": { target: gateway },
    },
  },
});
