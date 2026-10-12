/** Lê a arte dos cartuchos pelo gateway: o índice das camadas e o `art.json` de cada uma (ADR-0053). */
import { EMPTY, mergeManifests, rooted, type ArtManifest } from "./manifest.ts";

type Fetch = (url: string) => Promise<Response>;

async function json(get: Fetch, url: string): Promise<unknown> {
  const response = await get(url);
  return response.ok ? ((await response.json()) as unknown) : undefined;
}

/** Sem gateway ou sem arte, o manifesto fica vazio, e o renderer desenha cores estáveis. */
export async function loadArt(get: Fetch = (url) => fetch(url)): Promise<ArtManifest> {
  const index = (await json(get, "/content/art/index.json")) as { layers?: string[] } | undefined;
  const layers: ArtManifest[] = [];
  for (const layer of index?.layers ?? []) {
    const root = `/content/art/${encodeURIComponent(layer)}`;
    const manifest = (await json(get, `${root}/art.json`)) as ArtManifest | undefined;
    if (manifest?.version === 1) {
      layers.push(rooted(manifest, root));
    }
  }
  return layers.length === 0 ? EMPTY : mergeManifests(layers);
}
