/** O ícone de 16 px de uma ação ou de um chip, da folha `icones` pelo mapa de ações do `art.json`
 * (`bubbles.icons.actions`), o mesmo dos balões. Os chips o usam em 1x; o menu do clique direito,
 * em 2x (briefing-tela-4.md, §2). Sem ícone, uma bolinha vazada. */
import type { ArtManifest } from "../art/manifest.ts";
import { el } from "../dom.ts";

/** O quadro do ícone na folha, [coluna, linha], ou nada. */
export function iconFrame(art: ArtManifest | undefined, name: string | undefined): readonly [number, number] | undefined {
  const icons = art?.bubbles?.icons;
  if (name === undefined || icons === undefined) {
    return undefined;
  }
  const frame = icons.frames[icons.actions?.[name] ?? name];
  return frame === undefined ? undefined : [frame[0], frame[1]];
}

/** O ícone desenhado: um `span` com a folha de fundo, na escala dada; sem ícone, a classe `empty`. */
export function actionIcon(art: ArtManifest | undefined, name: string | undefined, scale: 1 | 2 = 1): HTMLElement {
  const span = el("span", { className: `retro-ic${scale === 2 ? " x2" : ""}` });
  const frame = iconFrame(art, name);
  const icons = art?.bubbles?.icons;
  const sheet = icons === undefined ? undefined : art?.sheets?.[icons.sheet];
  if (frame === undefined || sheet === undefined) {
    span.classList.add("empty");
    return span;
  }
  const inner = el("span", { className: "retro-ic-cell" });
  inner.style.backgroundImage = `url(${sheet.image})`;
  inner.style.backgroundPosition = `-${String(frame[0] * 16)}px -${String(frame[1] * 16)}px`;
  span.append(inner);
  return span;
}
