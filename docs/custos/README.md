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
| M2 | 4 | 65 | 159 | 292 | 59,5 | 502 |
| M3 | 2 | 46 | 120 | 198 | 77,9 | 250 |
| M4 | 3 | 67 | 253 | 296 | 90,5 | 526 |
| M5 | 2 | 33 | 115 | 136 | 79,7 | 198 |
| M6 | 6 | 76 | 325 | 334 | 124,6 | 1.327 |
| M7 | 6 | 28 | 98 | 91 | 68,2 | 857 |
| M8 | 16 | 82 | 110 | 365 | 50,3 | 872 |
| M9 | 4 | 34 | 35 | 147 | 28,8 | 891 |
| M10+M11 | 17 | 120 | 165 | 528 | 104,1 | 1.676 |
| M12 | 13 | 54 | 98 | 213 | 26,8 | 628 |
| M13 | 7 | 158 | 246 | 477 | 123,8 | 776 |
| M14 | 18 | 50 | 195 | 230 | 101,1 | 1.705 |
| M15 | 4 | 34 | 115 | 114 | 37,1 | 989 |

## Uso do plano Max

Anotado ao fechar cada marco, como o app mostra: a janela de 5 horas e a semana.

| data | momento | janela_5h_pct | semana_pct |
|---|---|---|---|
| 2026-10-12 | depois do M4 (revisão do relógio) | 14 | 8 |
| 2026-10-12 | fim do M5 (implementação) | 24 | 9 |
| 2026-10-12 | fim do M6 | 18 | 12 |
| 2026-10-12 | fim do M7 (v0.1.0) | 24 | 12 |
| 2026-10-17 | fim do M8 | 49 | 2 |
| 2026-10-18 | fim do M9 (sem a chamada real) | 36 | 6 |
| 2026-10-19 | fim do M10 e do M11 (janela de 5 h reiniciada antes da leitura) | 15 | 22 |
| 2026-10-19 | fim do M12 (noite |  depois da arena e do plano do M13) | 20 | 29 |
| 2026-10-20 | M13 em curso (fazenda 2: kernel |  gênero |  cenário |  script 2 |  mente |  fita; madrugada) | 83 | 37 |
| 2026-10-20 | M13 em curso (manhã: premissas revistas |  métricas da bíblia 2 §13 |  e2e nos dois mundos |  tela da Boa Vista; semana da Fable a 80%) | 34 | 43 |
| 2026-10-20 | fim do M13 (meio-dia; semana da Fable a 81%) | 36 | 43 |
| 2026-10-20 | fim do M14 (noite; a rodada e a arte numa sessão no Opus; semana da Fable a 88%) | 30 | 48 |
| 2026-10-21 | fim do M15 (noite; o fechamento da v0.2 no Opus; semana da Fable a 88%) | 5 | 51 |
