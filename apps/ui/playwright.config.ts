/** Teste de fumaça da tela num navegador de verdade (M6; ADR-0053, decisão 8).
 *
 *     make ui-e2e
 *
 * Sobe um sandbox próprio (NATS, kernel, script, gateway) numa porta separada e abre as duas visões.
 * No CI usa o Chromium que o Playwright baixa; na máquina local, o Chrome já instalado.
 */
import { defineConfig } from "@playwright/test";

const PORT = Number(process.env.CAMPSVERSO_E2E_PORT ?? "8799");
const ci = process.env.CI !== undefined;

export default defineConfig({
  testDir: "e2e",
  outputDir: "test-results",
  timeout: 90_000,
  retries: ci ? 1 : 0,
  reporter: ci ? [["list"], ["html", { open: "never", outputFolder: "playwright-report" }]] : "list",
  use: {
    baseURL: `http://127.0.0.1:${String(PORT)}`,
    browserName: "chromium",
    // No CI não há GPU: o Chromium desenha o WebGL por software (SwiftShader).
    ...(ci ? { launchOptions: { args: ["--enable-unsafe-swiftshader"] } } : { channel: "chrome" }),
    viewport: { width: 1300, height: 900 },
    screenshot: "only-on-failure",
    trace: "retain-on-failure",
  },
  webServer: {
    command: `uv run --locked python -m campsverso_testkit.sandbox --out data/sandbox/e2e-${String(Date.now())} --port ${String(PORT)}`,
    cwd: "../..",
    url: `http://127.0.0.1:${String(PORT)}/health`,
    timeout: 120_000,
    reuseExistingServer: false,
    gracefulShutdown: { signal: "SIGTERM", timeout: 20_000 },
  },
});
