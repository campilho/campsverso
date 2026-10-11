# ADR-0035 — CI no GitHub Actions

**Status:** aceita · **Data:** 2026-10-11 · **Marco:** M0 (acréscimo)
**Complementa:** `escopo-v0.1.md` §7 (M0 previa só CI local); ADR-0033

## Contexto

O M0 entregou o `make check` local. Com o repositório público no GitHub, vale garantir que o projeto também passa numa máquina limpa, e não só no Mac de desenvolvimento. Isso pega arquivo esquecido fora do commit, lockfile desatualizado ou dependência do macOS. O GitHub Actions é gratuito para repositórios públicos.

## Decisão

- **Workflow `.github/workflows/check.yml`:** a cada push na `main` e a cada pull request, um Ubuntu limpo roda `make setup` e `make check`. É o mesmo ponto de entrada da máquina local.
- **Permissões mínimas** (`contents: read`). As actions de terceiros são fixadas pelo **hash do commit**, com a versão num comentário, porque uma etiqueta de versão pode ser movida por quem controla o repositório da action.
- **Compatibilidade dos contratos** (`make compat`): num push, compara com o topo anterior da branch; num pull request, com a branch de destino.
- **Selo** do resultado no README.

## Consequências

- Todo commit publicado mostra se o projeto está íntegro (✓ ou ✗), e o GitHub avisa por e-mail quando quebra.
- **Opcional, a configurar pelo dono do repositório:** proteger a `main`, exigindo o check verde antes de aceitar mudanças (Settings → Branches).
- Atualizar uma action é trocar o hash e o comentário. Um robô como o Dependabot pode fazer isso no futuro.
