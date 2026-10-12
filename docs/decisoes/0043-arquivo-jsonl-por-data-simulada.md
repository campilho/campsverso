# ADR-0043 — Arquivo JSONL por data simulada

**Status:** aceita · **Data:** 2026-10-11 · **Marco:** M2
**Altera:** plano do M2 §2 (`dia-0001.jsonl`)

## Contexto

O plano do M2 previa um JSONL por mundo e por dia simulado, com nome `dia-0001.jsonl`. Ao implementar, apareceu um problema: o arquivador não conhece o calendário do cartucho, ou seja, a hora em que o dia vira (06:00 na fazenda). Ele só vê envelopes.

## Decisão

1. **Um arquivo por mundo e por data simulada** (aprovado pelo usuário): `data/archive/<mundo>/<AAAA-MM-DD>.jsonl`.
   - A data vem do `simtime` do envelope, no fuso do mundo, e o arquivo vira à meia-noite simulada.
   - Vale para qualquer cartucho. Uma noite de sono fica dividida entre dois arquivos.
2. **Comandos** não têm `simtime`: vão para a data simulada mais recente daquele mundo.
3. **Só acrescentar, e confirmar depois de gravar:**
   - o arquivador grava o lote, sincroniza no disco (`fsync`) e só então confirma no JetStream;
   - uma entrega repetida (gravada, mas não confirmada antes de uma queda) é descartada pelo `id`. Ele lembra os ids dos dois dias mais recentes de cada mundo.
4. **Linha cortada pela queda:** ao abrir, uma última linha sem `\n` é removida. Ela nunca foi confirmada, então volta a ser entregue. Não se perde nada.
5. **Compressão** (decisão 4 do plano):
   - dias com mais de `archive.compress_after_days` (7) dias simulados de diferença para o mais recente viram `.jsonl.gz`;
   - o original só sai depois que o `.gz` está gravado;
   - uma mensagem atrasada para um dia já comprimido entra como um novo membro gzip no fim do arquivo, sem reescrever o que já estava lá.

## Consequências

- `make replay DAY=N` (M3) precisa ler os dois arquivos que cobrem o dia agrícola N. É só ler por faixa de `tick`.
- A ordem das linhas num arquivo não é a de `seq`: cada stream tem o seu consumidor. Quem precisar da ordem ordena por `(source, seq)`.
