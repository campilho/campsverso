/** Os nomes que quem joga lê, por língua (ADR-0075).
 *
 * Os ids ficam como estão: estão no histórico, nas fitas e no vocabulário das mentes. O que a tela
 * mostra no lugar deles vem de um arquivo por camada de cartucho, `locale/<língua>.json`, que o
 * gateway serve ao lado da arte; a camada de cima cobre a de baixo, como na arte. Por ora a tela
 * lê só os nomes das coisas e dos atributos; os textos dela mesma ainda moram no código.
 */

type Fetch = (url: string) => Promise<Response>;

export const LANGUAGE = "pt-BR";

export interface Locale {
  /** O nome de um item, de um tipo (`kind`) ou de uma entidade, pelo id. */
  readonly names?: Readonly<Record<string, string>>;
  /** O nome de um atributo que a tela mostra (`charges` vira "cargas"). */
  readonly attributes?: Readonly<Record<string, string>>;
  /** O rótulo de uma ação em andamento, para a barra sobre o avatar (`work` vira "Trabalhando",
   * `videogame` vira "Jogando videogame"); vale mais que o rótulo do menu (ADR-0078, ADR-0082). */
  readonly actions?: Readonly<Record<string, string>>;
  /** As escolhas que a tela oferece (ADR-0089): na prancheta, `hands` (quem programa) e `models`,
   * do id ao nome, na ordem em que aparecem. O kernel confere a escolha; aqui só se mostra. */
  readonly choices?: Readonly<Record<string, Readonly<Record<string, string>>>>;
}

let names: Record<string, string> = {};
let attributes: Record<string, string> = {};
let actions: Record<string, string> = {};
let choices: Record<string, Readonly<Record<string, string>>> = {};

/** Junta os arquivos das camadas, na ordem do índice da arte. */
export function setLocale(layers: readonly Locale[]): void {
  names = Object.assign({}, ...layers.map((l) => l.names ?? {})) as Record<string, string>;
  attributes = Object.assign({}, ...layers.map((l) => l.attributes ?? {})) as Record<string, string>;
  actions = Object.assign({}, ...layers.map((l) => l.actions ?? {})) as Record<string, string>;
  // Cada lista inteira: a camada de cima troca a lista, e não junta as opções.
  choices = Object.assign({}, ...layers.map((l) => l.choices ?? {})) as Record<string, Readonly<Record<string, string>>>;
}

/** As opções de uma escolha, `[id, nome]`, na ordem do arquivo; sem a lista, nenhuma. */
export function choicesOf(kind: string): (readonly [string, string])[] {
  return Object.entries(choices[kind] ?? {});
}

/** O nome de uma opção; sem ele, o próprio id. */
export function choiceName(kind: string, id: string): string {
  return choices[kind]?.[id] ?? id;
}

/** O rótulo de uma ação pelo arquivo da língua, se a camada o declarou. */
export function actionName(id: string): string | undefined {
  return actions[id];
}

/** Lê o arquivo da língua de cada camada; uma camada sem ele não muda nada. */
export async function loadLocale(layers: readonly string[], get: Fetch = (url) => fetch(url)): Promise<void> {
  const found: Locale[] = [];
  for (const layer of layers) {
    const response = await get(`/content/locale/${encodeURIComponent(layer)}/${LANGUAGE}.json`);
    if (response.ok) {
      found.push((await response.json()) as Locale);
    }
  }
  setLocale(found);
}

/** O nome de uma coisa pelo id; sem tradução, o id com espaços no lugar dos `_`. */
export function localName(id: string): string {
  return names[id] ?? id.replace(/_/g, " ");
}

/** O nome de um atributo; sem tradução, o próprio. */
export function attributeName(key: string): string {
  return attributes[key] ?? key;
}
