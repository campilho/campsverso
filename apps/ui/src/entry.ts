/** A entrada da tela: a página da arena (`?view=arena`, ADR-0068) ou a do mundo (jogador e operador). */
const arena = new URLSearchParams(location.search).get("view") === "arena";
void (arena ? import("./arena.ts") : import("./main.ts"));
