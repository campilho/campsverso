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
      "packages/contracts-ts/src/**", // GERADO a partir de contracts/
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
  { files: ["**/*.js", "**/*.cjs"], extends: [tseslint.configs.disableTypeChecked] },
  { files: ["**/*.cjs"], languageOptions: { sourceType: "commonjs" } },
);
