/** Lê a arte dos cartuchos pelo gateway: o índice das camadas e o `art.json` de cada uma (ADR-0053). */
import { EMPTY, mergeManifests, rooted, type ArtManifest } from "./manifest.ts";

type Fetch = (url: string) => Promise<Response>;

export interface LoadedArt {
  readonly manifest: ArtManifest;
  /** Os créditos de cada camada, na ordem do índice (a junção dos manifestos guardaria só o último). */
  readonly credits: readonly { readonly layer: string; readonly url: string }[];
}

async function json(get: Fetch, url: string): Promise<unknown> {
  const response = await get(url);
  return response.ok ? ((await response.json()) as unknown) : undefined;
}

/** Sem gateway ou sem arte, o manifesto fica vazio, e o renderer desenha cores estáveis. */
export async function loadArt(get: Fetch = (url) => fetch(url)): Promise<LoadedArt> {
  const index = (await json(get, "/content/art/index.json")) as { layers?: string[] } | undefined;
  const layers: ArtManifest[] = [];
  const credits: { layer: string; url: string }[] = [];
  for (const layer of index?.layers ?? []) {
    const root = `/content/art/${encodeURIComponent(layer)}`;
    const manifest = (await json(get, `${root}/art.json`)) as ArtManifest | undefined;
    if (manifest?.version === 1) {
      const placed = rooted(manifest, root);
      layers.push(placed);
      if (placed.credits !== undefined) {
        credits.push({ layer, url: placed.credits });
      }
    }
  }
  return { manifest: layers.length === 0 ? EMPTY : mergeManifests(layers), credits };
}
