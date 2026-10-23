# ADR-0067 — Decisões do plano do M16 (a Fazenda Morada do Sol)

**Status:** aceita · **Data:** 2026-10-22 · **Marco:** M16
**Complementa:** `docs/planos/m16-morada-do-sol.md`; ADR-0025 (o modelo de mundo); ADR-0056 (a percepção); ADR-0060 (a memória); ADR-0066
**Altera:** ADR-0066, decisão 2: a Morada do Sol estende a Boa Vista, não o gênero direto (a intenção, um cenário novo com as fazendas anteriores intactas, continua)

## Decisão

1. **O cartucho `farm_morada_do_sol` e o mundo `farm-morada-do-sol-01`** estendem a Boa Vista. As fazendas 1 e 2 ficam guardadas como estão.
2. **O mapa tem 64 × 40 tiles,** com a casa a oeste, o rio e a várzea a leste, o morro e a lagoa ao norte e a clareira ao sul. O tamanho se ajusta depois de jogar.
3. **O raio da percepção da Morada do Sol é de 12 tiles.** A névoa na tela vem no M17.
4. **A câmera** segue o Camps, arrastar olha o resto, e o operador tem o mapa inteiro.
5. **A primitiva `WorldOps.despawn`** fica no kernel e no `cartridge-api`, com o evento `world.entity.despawned.v1`. O kernel recusa remover um avatar, um contêiner com itens ou o alvo de uma ação em andamento.
6. **Os canteiros não têm teto** (só um técnico, de 400) e só se cavam na grama. O canteiro vazio volta a ser grama depois de 3 dias, e o id é sequencial.
7. **O calendário é genérico, no kernel, e cada cartucho declara o seu ano.** A data e a estação vão em campos opcionais do relógio, e o evento `world.clock.season_changed.v1` marca a troca. Só a Morada do Sol declara um ano.
8. **O ano tem 28 dias simulados,** 7 por estação, e começa na primavera, em 22 de setembro, no hemisfério sul. A 72×, isso dá umas 9 horas e 20 minutos de jogo.
9. **A afinidade de cada cultura com cada estação** tem três níveis: boa, fraca ou parada. Fora da estação a planta não morre.
10. **Quatro culturas novas** (milho, melancia, mandioca, couve) vêm do pacote LPC que já temos, no calendário de plantio do plano.
11. **As regras ocultas são três:** R-001 (a várzea), R-002 (os corvos e o espantalho) e R-003 (a fadiga do solo). As verdades da Boa Vista continuam valendo. A saturação do preço não é regra oculta: é a economia do M18.
12. **A grama muda de cor com a estação,** e o espantalho segue o estilo LPC. O download de arte está autorizado se precisar.
13. **O fazendeiro-script 2 adaptado** fica mais sofisticado, com regras condicionais e sem nenhuma regra oculta.
14. **A lembrança do que se viu:**
    - a percepção separa `out_of_view` de `gone`;
    - a `MemoryPort` guarda o último estado visto de cada entidade;
    - o bloco de abertura lista o que está fora de vista.

## Consequências

- **Contratos:** dois eventos novos (`world.entity.despawned.v1` e `world.clock.season_changed.v1`) e campos opcionais (`date` e `season` no relógio, `out_of_view` no delta). O `make compat` confere que tudo é compatível.
- **A `MemoryPort` ganha a tabela de lugares lembrados.** É a primeira peça do caderno de campo do M19.
- **A tela passa a ter câmera.** O clique converte pelo mundo, e o teste do Playwright deixa de clicar em pixel fixo.
