/** Merge patch (RFC 7386): como o `update` do gateway muda o estado (ADR-0050). */

export type Json = string | number | boolean | null | Json[] | { [key: string]: Json };

function isObject(value: unknown): value is Record<string, Json> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

export function applyMergePatch(target: unknown, patch: unknown): Json {
  if (!isObject(patch)) {
    return patch as Json;
  }
  const result: Record<string, Json> = isObject(target) ? { ...target } : {};
  for (const [key, value] of Object.entries(patch)) {
    if (value === null) {
      // eslint-disable-next-line @typescript-eslint/no-dynamic-delete -- é a semântica do RFC 7386
      delete result[key];
    } else {
      result[key] = applyMergePatch(result[key], value);
    }
  }
  return result;
}
