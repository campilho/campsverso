import js from "@eslint/js";
import { defineConfig } from "eslint/config";
import globals from "globals";
import tseslint from "typescript-eslint";

export default defineConfig(
  {
    ignores: [
      "**/node_modules/**",
      "**/dist/**",
      "**/.venv/**",
      ".claude/**", // local de cada máquina: os worktrees das tarefas do Claude Code
      "packages/contracts-ts/src/**", // GERADO a partir de contracts/
      "docs/design/escritorio/**", // protótipo do Claude Design para o navegador, referência e não código do projeto
    ],
  },
  js.configs.recommended,
  tseslint.configs.strictTypeChecked,
  {
    languageOptions: {
      globals: { ...globals.node },
      parserOptions: { projectService: true, tsconfigRootDir: import.meta.dirname },
    },
  },
  { files: ["apps/ui/src/**/*.ts"], languageOptions: { globals: { ...globals.browser } } },
  { files: ["**/*.js", "**/*.cjs"], extends: [tseslint.configs.disableTypeChecked] },
  { files: ["**/*.cjs"], languageOptions: { sourceType: "commonjs" } },
);
