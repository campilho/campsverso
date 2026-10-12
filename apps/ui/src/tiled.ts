/** Leitura do mapa Tiled (`.tmj`) do cartucho: só o tipo de cada tile, nada de imagem (ADR-0050). */

export interface TileGrid {
  readonly width: number;
  readonly height: number;
  /** Tipo de cada tile, linha a linha (`grass`, `river`…); "" quando o tile não tem tipo. */
  readonly types: readonly string[];
}

interface TiledTile {
  readonly id: number;
  readonly type?: string;
  readonly class?: string;
}

interface TiledMap {
  readonly width: number;
  readonly height: number;
  readonly layers: readonly { readonly name: string; readonly type: string; readonly data?: readonly number[] }[];
  readonly tilesets: readonly { readonly firstgid: number; readonly tiles?: readonly TiledTile[] }[];
}

export function parseTiledMap(raw: unknown, layer = "terrain"): TileGrid {
  const map = raw as TiledMap;
  const terrain = map.layers.find((l) => l.type === "tilelayer" && l.name === layer);
  if (terrain?.data === undefined) {
    throw new Error(`o mapa não tem a camada de tiles ${layer}`);
  }
  const byGid = new Map<number, string>();
  for (const tileset of map.tilesets) {
    for (const tile of tileset.tiles ?? []) {
      byGid.set(tileset.firstgid + tile.id, tile.type ?? tile.class ?? "");
    }
  }
  return {
    width: map.width,
    height: map.height,
    types: terrain.data.map((gid) => byGid.get(gid) ?? ""),
  };
}

export function tileAt(grid: TileGrid, x: number, y: number): string {
  return grid.types[y * grid.width + x] ?? "";
}
