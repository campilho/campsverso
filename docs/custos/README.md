# Custos de desenvolvimento

GERADO por `make sessoes` a partir de `sessoes.csv`, `plano.csv` e `creditos.csv`:
não editar à mão.

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
| M15 | 4 | 37 | 121 | 119 | 38,6 | 994 |
| M16 | 7 | 151 | 477 | 428 | 280,5 | 2.662 |
| M17 | 3 | 84 | 333 | 249 | 140,7 | 534 |
| M18 | 2 | 98 | 229 | 277 | 161,6 | 847 |
| M19 | 16 | 254 | 651 | 735 | 300,9 | 1.616 |
| M20 | 32 | 237 | 670 | 607 | 398,4 | 2.299 |

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
| 2026-10-23 | fim do M16 (noite; a Morada do Sol no Opus; semana da Fable a 88%) | 12 | 57 |
| 2026-10-24 | fim do M17 (madrugada; ver e assistir no Opus; semana da Fable a 88%) | 27 | 59 |
| 2026-10-24 | fim do M18 (tarde; a economia no Opus; semana da Fable a 88%) | 21 | 62 |
| 2026-10-25 | fim do M19 (noite; os controladores e a medição no Opus; semana nova; Fable a 0%) | 10 | 8 |
| 2026-10-26 | fim do M20 (tarde; os ajudantes no Opus; Fable a 0%) | 16 | 17 |

## Créditos de API

As recargas e os saldos das contas que as corridas usam, anotados à mão em
`creditos.csv`: o valor em dólar, o cobrado no cartão em real e o saldo depois. O crédito
do plano vem com a assinatura e não passa no cartão.

| data | provedor | movimento | usd | brl | saldo_usd | nota |
|---|---|---|---|---|---|---|
| 2026-10-18 | Anthropic | plano | 100.00 |  | 100.00 | crédito do plano Max, resgatado na Console; vence em 10/11/2026 |
| 2026-10-22 | Anthropic | saldo |  |  | 56.39 |  |
| 2026-10-29 | OpenRouter | compra | 50.00 |  | 50.00 | a primeira carga, para as outras famílias |
| 2026-11-02 | Anthropic | saldo |  |  | 28.76 | só o que restava do crédito do plano |
| 2026-11-02 | Anthropic | compra | 30.00 |  | 58.73 | para o ano do Opus |
| 2026-11-02 | Anthropic | saldo |  |  | 23.48 |  |
| 2026-11-02 | OpenRouter | saldo |  |  | 39.39 |  |
| 2026-11-02 | OpenRouter | compra | 50.00 |  | 85.31 | para o ano do Astra; o limite semanal da chave subiu de 50 para 100 |
| 2026-11-03 | OpenRouter | saldo |  |  | 57.77 | depois do ano do Astra |
| 2026-11-03 | Anthropic | compra | 100.00 |  | 118.00 | para o ano do Fable |

| Provedor | Entrou (US$) | No cartão (R$) | Último saldo (US$) | Gasto (US$) |
|---|---|---|---|---|
| Anthropic | 230,00 | 0,00 (faltam 2) | 118,00 | 112,00 |
| OpenRouter | 100,00 | 0,00 (faltam 2) | 57,77 | 42,23 |
