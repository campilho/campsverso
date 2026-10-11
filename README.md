# Campsverso

Plataforma de simulação orientada a eventos para agentes autônomos que vivem em mundos 2D. Os avatares podem ser controlados por humanos, por scripts e, a partir da v0.2, por LLMs.

Cada mundo é um **cartucho** (fazenda, estúdio, vilarejo…) rodando sobre um **kernel** genérico. O kernel conhece a "física" de um mundo simulado: tempo, espaço, entidades, itens, necessidades, ações e regras. Isso inclui **regras ocultas**, que os agentes precisam descobrir observando o mundo.

Projeto pessoal de aprendizado, construído em público com a ajuda do Claude Code e documentado passo a passo.

## Status

**v0.1 "Fazenda do Camps"**, em construção: marco M0 (fundação). Um avatar, nenhum LLM; controladores humano, script e replay. Detalhes no [escopo da v0.1](docs/arquitetura/escopo-v0.1.md).

## Documentação

- [Arquitetura](docs/arquitetura/): escopo, bíblia do mundo, contratos de eventos, gestão do tempo, catálogo de eventos e pesquisa de componentes. A ordem de leitura está no escopo.
- [Decisões (ADRs)](docs/decisoes/README.md)
- [Diário de bordo](docs/diario/)

## Licença

[MIT](LICENSE)
