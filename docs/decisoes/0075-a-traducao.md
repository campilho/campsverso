# ADR-0075 — A tradução: ids estáveis e os nomes de cada língua num arquivo por camada

**Status:** aceita · **Data:** 2026-11-01 · **Marco:** M21
**Complementa:** ADR-0031 (os cartuchos em camadas); ADR-0053 (a arte em camadas); a convenção de idioma do `CLAUDE.md`

## Contexto

Jogando a primeira semana do mapa d, o usuário viu "spade" e "watering-can (charges 10, capacity 10)" no baú e no inventário. O resto da tela está em português. A pergunta dele: o projeto não deveria ter um arquivo de localização, com o código e os arquivos de controle em strings de controle, um arquivo em português agora e um em inglês depois, que qualquer um pudesse traduzir?

Hoje os ids de conteúdo são em português por convenção (`semente_rabanete`, `adubo`), com quatro exceções da v0.1 e da Boa Vista: `spade`, `plow`, `watering_can` e `watering_can_large`. A tela mostra o id quando a entidade não tem `display_name`.

## Decisão

1. **Os ids não mudam.** Os ids de itens, tipos, entidades, ações e eventos são as strings de controle. Eles estão no arquivo de cada mundo, nas fitas, no vocabulário das mentes e nas comparações entre rodadas, e trocar um id quebraria tudo isso. Os quatro em inglês ficam como estão.
2. **Cada camada de cartucho tem os nomes de cada língua num arquivo, `locale/<língua>.json`,** ao lado da `art/`: `names` dá o nome de um item, de um tipo ou de uma entidade pelo id, e `attributes` dá o nome de um atributo que a tela mostra (`charges` vira "cargas").
   - O gateway serve o arquivo em `/content/locale/<camada>/<língua>.json`.
   - A tela junta os arquivos na ordem das camadas da arte: a camada de cima cobre a de baixo.
   - Sem tradução, a tela mostra o id com espaços no lugar dos `_`.
3. **O primeiro arquivo é o `cartridges/farm/locale/pt-BR.json`,** com as quatro ferramentas e os três atributos que aparecem no inventário. A língua da tela é fixa em pt-BR por enquanto.
4. **Os textos da própria tela continuam no código.** Passar todos para um arquivo por língua, e depois escrever o inglês, é tarefa da v0.4 (`futuro.md`).
5. **O que as mentes leem fica fora:** o manual, as ferramentas e as notas. Traduzir o que um modelo lê muda o experimento; uma mente em outra língua seria um braço da arena, com plano próprio.

## Consequências

- **Para traduzir o jogo para outra língua,** basta escrever um `locale/<língua>.json` por camada, sem mexer em código; os textos da tela entram quando a extração da v0.4 terminar.
- **Nada muda para as mentes nem para o histórico:** os eventos, as fitas e os arquivos dos mundos continuam com os mesmos ids.
- **A tela ganha uma dependência de conteúdo a mais:** sem o arquivo, ela volta a mostrar os ids, e nada quebra.
