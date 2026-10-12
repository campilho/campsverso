# Custos de desenvolvimento

GERADO por `make sessoes` a partir de `sessoes.csv` e `plano.csv`: não editar à mão.

Tempo e tokens do Claude Code em cada marco (ADR-0051).

- **Minutos ativos** descontam as esperas de mais de 5 minutos entre
  uma chamada e outra (aprovações e pausas).
- **Saída** são os tokens escritos pelo modelo.
- **Cache lido** é o contexto relido a cada chamada: fica em cache e custa bem menos.
- Só números: o texto das conversas nunca entra aqui.

## Por marco

| Marco | Turnos | Min. ativos | Chamadas | Saída (mil) | Cache lido (mi) | Cache escrito (mil) |
|---|---|---|---|---|---|---|
| preparação | 5 | 36 | 56 | 197 | 13,0 | 580 |
| M0 | 2 | 34 | 81 | 183 | 37,5 | 211 |
| M1 | 1 | 35 | 54 | 198 | 38,2 | 222 |
| M2 | 4 | 65 | 10 | 34 | 8,2 | 35 |
| M3 | 2 | 46 | 0 | 0 | 0,0 | 0 |
| M4 | 3 | 67 | 253 | 296 | 90,5 | 526 |
| M5 | 2 | 33 | 115 | 136 | 79,7 | 198 |
| M6 | 6 | 76 | 325 | 334 | 124,6 | 1.327 |
| M7 | 1 | 16 | 62 | 62 | 42,1 | 93 |

## Uso do plano Max

Anotado ao fechar cada marco, como o app mostra: a janela de 5 horas e a semana.

| data | momento | janela_5h_pct | semana_pct |
|---|---|---|---|
| 2026-10-12 | depois do M4 (revisão do relógio) | 14 | 8 |
| 2026-10-12 | fim do M5 (implementação) | 24 | 9 |
| 2026-10-12 | fim do M6 | 18 | 12 |
| 2026-10-12 | fim do M7 (v0.1.0) | 24 | 12 |
