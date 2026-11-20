# ADR-0084 — Os comandos do cartucho

**Status:** aceita · **Data:** 2026-11-20 · **Marco:** M25
**Complementa:** ADR-0083 (o PR do dev, decisão 5); ADR-0025 (o modelo de mundo genérico); ADR-0037 (os comandos de controle valem já); ADR-0046 (os comandos fora do contrato são recusados)

## Contexto

O M25 traz para dentro do mundo o que acontece no GitHub: o PR do dev aberto, o CI, o merge, o PR fechado. O kernel é o único escritor da verdade (princípio 2), e tudo o que muda o mundo precisa ficar no diário para o replay. Então o vigia do GitHub manda ao kernel um comando, e não escreve nada.

Até aqui, só havia dois caminhos para um comando:
- a proposta de ação de um avatar (`cmd.action.propose`), que o cartucho valida e completa;
- os comandos de controle do kernel (o relógio, a posse, as regras), numa tabela fixa.

Um relato do GitHub não é a ação de um avatar, e o kernel não pode conhecer o escritório (princípio 8).

## Decisão

1. **Um cartucho pode declarar comandos** (`WorldBuilder.add_command`), cada um com um tipo e um `apply` (`CommandSpec`, em `libs/cartridge-api`). O `apply` recebe o comando (`CommandContext`: o id, os dados e a visão do mundo) e as operações do mundo, as mesmas dos sistemas.
2. **O tipo é do domínio do cartucho:** `campsverso.cmd.<cartucho ou biblioteca da cadeia>.<nome>.v<N>`, declarado em `contracts/` como comando. O kernel confere as duas coisas ao montar o mundo e recusa o que não confere.
3. **O kernel encaminha pelo tipo, na hora em que o comando chega,** como um comando de controle (ADR-0037). Os fatos levam o comando como causa e a correlação dele. Uma recusa vira `world.command.rejected`, e o cartucho confere antes de mudar.
4. **O diário guarda o comando** como guarda qualquer outro, e o replay o refaz no mesmo ponto, sem perguntar nada a fora do mundo.
5. **O primeiro comando é o do escritório:** `campsverso.cmd.office.pull_request.report.v1`, do produtor novo `codehost`, com o PR aberto, mudado, mesclado ou fechado (ADR-0083).
6. **Quem pode mandar** é questão de permissão no NATS, como para os outros comandos (princípio 5), e não do kernel.

## Consequências

- **O kernel segue sem conhecer nenhum mundo:** ele só encaminha um tipo que o cartucho declarou.
- **Outros efeitos externos usam o mesmo caminho:** o telefone do M29 e o resultado de uma ferramenta de fora.
- **Um cartucho ganha um jeito novo de mudar o mundo fora das ações.** Ele continua só pelas primitivas, e cada comando tem contrato próprio.
- **A versão do kernel muda,** e um mundo com incrementais da versão anterior precisa parar com elegância antes de subir nesta (como em toda mudança no kernel).
