# ADR-0068 — Decisões do plano do M17 (ver e assistir)

**Status:** aceita · **Data:** 2026-10-23 · **Marco:** M17
**Complementa:** `docs/planos/m17-ver-e-assistir.md`; ADR-0056 (a percepção); ADR-0061 (a arena); ADR-0067
**Substitui:** a ideia do `futuro.md` de assistir uma corrida reexecutando o kernel com `at_tick` no modo contínuo

## Decisão

1. **O raio depende da fase do dia e da luz, na percepção,** com a mesma regra para o humano, o script e o LLM. O cartucho declara tudo em campos opcionais de `perception_config`: `by_phase` (o raio por fase) e `lights` (um item no inventário que garante um raio mínimo). Na Morada do Sol: 12 de dia, 7 no entardecer, 5 de noite e de madrugada, e a lanterna dá 10.
2. **A névoa na visão do jogador é uma nuvem,** não preto:
   - o que nunca foi visto fica coberto pela nuvem;
   - onde o avatar passa, ela abre;
   - quando ele se afasta, o desenho fica sob um cinza semitransparente, congelado como foi visto, até ele voltar ao raio.

   O operador vê tudo e pode trocar para "ver como o Camps".
3. **A lembrança:** o humano vê o desenho congelado e não sabe se algo mudou; o script e o LLM lembram pela memória deles (ADR-0067), sabendo que pode ter mudado. A tela guarda o que viu enquanto está aberta.
4. **Assistir é ler os fatos.** O gateway ganha um modo de assistir, que monta o estado de cada corrida a partir do arquivo de eventos dela, pela projeção comum, sem reexecutar o kernel.
5. **A arena grava o arquivo de eventos por partes,** a cada dia simulado, com um `estado.json`. O tamanho dos arquivos fica sob observação, e uma limpeza pode vir depois.
6. **A grade da arena no canvas 2D,** com 4 a 6 corridas por tela, e a corrida aberta no Phaser.
7. **A reprodução tem velocidade:** pausar, 1 dia por minuto, 1 dia a cada 10 segundos e o máximo.
8. **Os menus do humano:**
   - cavar e fincar pelo clique direito na grama;
   - as ferramentas pelo baú, pelo id;
   - a fila de ações na tela, sem mudar o kernel.
9. **O teclado:** as setas e o WASD andam, o espaço volta a seguir o Camps, o E abre o menu do Camps. Uma explicação dos comandos aparece na tela, pelo menos na primeira vez.
10. **Os rótulos de eventos são dados do cartucho,** e viajam no `session.started`.
11. **A lanterna desenhada no estilo LPC,** se nenhum pacote tiver uma.
12. **O manual da Morada do Sol ganha a noite e a lanterna,** e a fita é regravada se o pedido mudar.

## Consequências

- **Contratos:** campos opcionais em `perception_config` (`by_phase`, `lights`) e no `session.started` (os rótulos). O `make compat` confere.
- **O princípio 7 continua intacto.** Assistir não pede lockstep nem `at_tick`.
- **Duplicação na tela:** a tela calcula o raio da hora com a mesma regra da percepção, para desenhar a névoa. Um teste confere que as duas contas dão o mesmo.
