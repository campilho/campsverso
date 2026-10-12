import { defineConfig } from "vite";

// O gateway (make run ou make sandbox) atende o WebSocket e o mapa do cartucho (ADR-0050).
const gateway = `http://127.0.0.1:${process.env.CAMPSVERSO_GATEWAY_PORT ?? "8765"}`;

export default defineConfig({
  server: {
    host: "127.0.0.1",
    port: 5173,
    proxy: {
      "/ws": { target: gateway, ws: true },
      "/content": { target: gateway },
    },
  },
});
