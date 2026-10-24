/** Teste de fumaça da tela num navegador de verdade (M6; ADR-0053, decisão 8).
 *
 *     make ui-e2e
 *
 * Três servidores próprios, um por projeto, em portas separadas (ADR-0068):
 * - `fazenda`: um sandbox (NATS, kernel, script, gateway) da fazenda 1, com as duas visões;
 * - `morada`: um sandbox da Morada do Sol com o relógio parado, para a névoa e o menu da grama;
 * - `arena`: uma rodada sintética de duas corridas, no gateway no modo de assistir.
 * No CI usa o Chromium que o Playwright baixa; na máquina local, o Chrome já instalado.
 */
import { defineConfig } from "@playwright/test";

const PORT = Number(process.env.CAMPSVERSO_E2E_PORT ?? "8799");
const MORADA = PORT - 1;
const ARENA = PORT - 2;
const WORLD = process.env.MUNDO ?? "farm-camps-01"; // MUNDO=farm-boavista-01 abre a fazenda 2 (ADR-0062)
const ci = process.env.CI !== undefined;
const stamp = String(Date.now());

function server(command: string, port: number): {
  command: string;
  cwd: string;
  url: string;
  timeout: number;
  reuseExistingServer: boolean;
  gracefulShutdown: { signal: "SIGTERM"; timeout: number };
} {
  return {
    command,
    cwd: "../..",
    url: `http://127.0.0.1:${String(port)}/health`,
    timeout: 120_000,
    reuseExistingServer: false,
    gracefulShutdown: { signal: "SIGTERM", timeout: 20_000 },
  };
}

function sandbox(world: string, port: number, paused = false): string {
  const out = `data/sandbox/e2e-${world}-${stamp}`;
  return `uv run --locked python -m campsverso_testkit.sandbox --world config/worlds/${world}.yaml --out ${out} --port ${String(port)}${paused ? " --pausado" : ""}`;
}

export default defineConfig({
  testDir: "e2e",
  outputDir: "test-results",
  timeout: 90_000,
  retries: ci ? 1 : 0,
  reporter: ci ? [["list"], ["html", { open: "never", outputFolder: "playwright-report" }]] : "list",
  use: {
    browserName: "chromium",
    // No CI não há GPU: o Chromium desenha o WebGL por software (SwiftShader).
    ...(ci ? { launchOptions: { args: ["--enable-unsafe-swiftshader"] } } : { channel: "chrome" }),
    viewport: { width: 1300, height: 900 },
    screenshot: "only-on-failure",
    trace: "retain-on-failure",
  },
  projects: [
    { name: "fazenda", testMatch: /smoke\.spec\.ts/, use: { baseURL: `http://127.0.0.1:${String(PORT)}` } },
    { name: "morada", testMatch: /morada\.spec\.ts/, use: { baseURL: `http://127.0.0.1:${String(MORADA)}` } },
    { name: "arena", testMatch: /arena\.spec\.ts/, use: { baseURL: `http://127.0.0.1:${String(ARENA)}` } },
  ],
  webServer: [
    server(sandbox(WORLD, PORT), PORT),
    server(sandbox("farm-morada-do-sol-01", MORADA, true), MORADA),
    server(`uv run --locked python -m campsverso_testkit.assistir --out data/sandbox/e2e-arena-${stamp} --port ${String(ARENA)}`, ARENA),
  ],
});
