/**
 * Regras de arquitetura do lado TypeScript (princípio 1; escopo §9: a UI nunca decide nada).
 * @type {import('dependency-cruiser').IConfiguration}
 */
module.exports = {
  forbidden: [
    {
      name: "sem-ciclos",
      severity: "error",
      from: {},
      to: { circular: true },
    },
    {
      name: "ui-so-conhece-contratos",
      comment: "A UI conhece o mundo só pelos contratos gerados (princípio 1).",
      severity: "error",
      from: { path: "^apps/" },
      to: { path: "^(packages|tools)/", pathNot: "^packages/contracts-ts/" },
    },
    {
      name: "apps-independentes",
      severity: "error",
      from: { path: "^apps/([^/]+)/" },
      to: { path: "^apps/", pathNot: "^apps/$1/" },
    },
    {
      name: "contratos-sao-folha",
      comment: "O pacote de contratos gerado não depende de nada do repositório.",
      severity: "error",
      from: { path: "^packages/contracts-ts/" },
      to: { path: "^(apps|tools)/" },
    },
    {
      name: "sem-import-nao-resolvido",
      severity: "error",
      from: {},
      to: { couldNotResolve: true },
    },
  ],
  options: {
    doNotFollow: { path: "node_modules" },
    exclude: { path: "(^|/)node_modules/" },
    tsPreCompilationDeps: true,
    tsConfig: { fileName: "tsconfig.base.json" },
    enhancedResolveOptions: {
      exportsFields: ["exports"],
      conditionNames: ["import", "types", "default"],
      extensions: [".ts", ".js", ".json"],
    },
  },
};
