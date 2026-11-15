# ADR-0078 — Decisões do plano do M23 (o escritório)

**Status:** aceita · **Data:** 2026-11-14 · **Marco:** M23
**Complementa:** `docs/planos/m23-o-escritorio.md`; ADR-0077 (o plano macro da v0.4); ADR-0057 (o tick adiantado e o andar); ADR-0072 (vários avatares)

## Contexto

O M23 é o primeiro marco da v0.4: o cartucho do escritório, em tempo real e na vista de cima com arte LPC, com o dev-script, o gerente que o humano assume e o vigia.

O levantamento do código achou quatro coisas:
- o tick é do cartucho, e o kernel já sabe saltar o relógio;
- nada impede um humano de assumir qualquer avatar;
- não existe fala;
- o pulo do avatar na tela vem de sete mecanismos. O principal é o teto de 12 tiles por segundo no desenho: acelerado, o desenho fica para trás e salta para o destino quando o trajeto acaba.

O plano foi aprovado em 14/nov como recomendado. O usuário pediu que se avaliasse quebrar o marco em dois, porque ficou grande.

## Decisão

1. **O tick do escritório** sai de uma medida entre 1, 2 e 5 s. A aposta é 2 s.
2. **A âncora:**
   - o arquivo do mundo tem um início fixo;
   - ao subir, a pilha salta até agora, e o salto fica gravado no diário de entradas para o replay;
   - o tick adiantado fica no máximo um tick à frente do relógio real;
   - o relógio real é lido só na raiz de composição.
3. **As durações do escritório** são declaradas em segundos e minutos, e o kernel as converte. A espera também é em segundos. A fazenda não muda.
4. **O snapshot** passa a ser contado em minutos simulados, por mundo: a cada 60.
5. **O expediente:**
   - de segunda a sexta, das 09:00 às 18:00;
   - o almoço fora, das 12:00 às 13:00;
   - os feriados nacionais;
   - o vigia fica sempre que o dev não está.
6. **Sem necessidades no M23.** A energia e o café entram com a mente.
7. **Os controladores aceitos por avatar.**
   - Cada avatar declara os tipos que podem controlá-lo, e o kernel recusa `possess` fora da lista (`controller_not_allowed`).
   - O dev não aceita `human`.
   - O gateway lê a cadeira do jogador no mundo e confere o avatar pedido.
8. **O gerente** entra quando é assumido e sai pela porta com o "Sair". Se a tela fechar, sai na hora.
9. **A fala:**
   - é a ação `say` do kernel;
   - publica o evento `campsverso.avatar.spoke.v1`;
   - é ouvida na mesma sala;
   - tem até 280 caracteres.
10. **O pedido** é uma entidade do gênero `office`, sem a economia, com os eventos `office.ticket.*`. O tamanho (P, M, G) serve só ao script.
11. **O dev-script** fala frases prontas e simula o trabalho: 15 minutos num pedido P, 1 hora num M e 3 horas num G.
12. **A sala** tem uns 20 × 14 tiles, com o corredor, sem câmera rolando, e com o lugar da segunda mesa demarcado.
13. **A arte:**
    - os pacotes "LPC Revised: The Office", "LPC Wooden Furniture" e "LPC House Interior and Decorations";
    - três personagens do gerador LPC;
    - o download de cada arquivo pede o ok do usuário, com o tamanho;
    - as camadas da fazenda ganham o `only_for`.
14. **O movimento:**
    - o desenho segue o tempo do trajeto;
    - a correção do kernel vira uma emenda curta e suave;
    - o trajeto é identificado pela ação;
    - há um teste para cada mecanismo, escrito antes do conserto.
15. **A tela do gerente:**
    - a fala;
    - o formulário do quadro;
    - aceitar e devolver;
    - o "Sair";
    - as métricas dos pedidos no painel;
    - os textos novos em `locale`.
16. **A bíblia do escritório** e o `make escritorio`, com o mundo persistente.
17. **O gerente-script** e o soak de 5 dias, com os invariantes do plano (§9).

**A entrega vem em duas partes, sem mudar a numeração dos marcos.**
- **Parte 1, as bases,** que a fazenda já aproveita:
  - o andar sem pulo;
  - o tempo real no kernel: as durações em segundos, a âncora e o salto, e o snapshot por tempo;
  - os controladores aceitos por avatar;
  - a fala.
- **Parte 2, o escritório:**
  - o gênero e o cenário;
  - a medida do tick, já com o mundo de verdade;
  - os scripts, a arte, a tela;
  - a partida do usuário como gerente.

Entre as duas, o usuário confere o andar na fazenda e dá o ok do push.

## Consequências

- O escritório tem um relógio próprio, e a fazenda continua com o tick de um minuto e os mesmos números.
- A regra "nenhum humano assume o dev" (ADR-0077) passa a ser garantida pelo kernel.
- O contrato ganha a fala e os eventos do pedido, sem mudança incompatível.
- O resultado da medida do tick entra aqui, num adendo, na parte 2.

## Adendo (15/nov): a medida do tick e o que a parte 2 achou

**O tick fica em 2 s.** Um dia simulado do escritório, em memória, com o dev-script, o vigia e o gerente-script:

| Tick | Ticks por dia | Segundos por dia simulado | Entregas no dia |
|---|---|---|---|
| 1 s | 86.400 | 19,1 | 4 |
| 2 s | 43.200 | 16,7 | 4 |
| 5 s | 17.280 | 14,2 | 4 |

O custo está nas decisões dos scripts, e não nos ticks: o tick pouco pesa no soak. Os 2 s ficam por três motivos:
- um clique espera no máximo 2 s, e o primeiro responde na hora, pelo tick adiantado;
- as taxas das necessidades, quando a energia e o café chegarem, rendem números inteiros em múltiplos de 15 por hora (com 1 s, só em múltiplos de 30);
- o soak com os processos e o NATS leva uns 43 s por dia simulado.

**O salto caía no meio do minuto.** Com um tick menor que o minuto, o tick de agora pode cair no meio dele. O `ticks_until` do calendário supunha o contrário, e um salto chegava às 01:00:02 em vez das 01:00:00. Por isso o expediente das 09:00 nunca disparava durante um salto, nem no relógio ancorado do escritório vivo. A conta passou a descontar os segundos já passados no minuto; com o tick de um minuto da fazenda, ela não muda.

**Quem fala com o dev espera o fim do bloco.** A percepção entrega as falas que o avatar ouviu (o campo `heard` da foto), e o dev-script trabalha em blocos de um minuto, respondendo entre um e outro. Interromper o trabalho na hora em que alguém fala pediria um motivo novo de decisão: ampliar o enum do `avatar.decision_requested.v1` é incompatível, e fica para o M24, quando a mente chega e uma decisão a mais passa a custar.
