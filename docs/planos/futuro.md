# Tarefas futuras

Ideias e pendências que ainda não têm marco. Cada uma vira plano, ou ADR, quando chegar a hora. As mais novas ficam no fim.

| Tarefa | Origem | Quando decidir |
|---|---|---|
| **Enxergar o mapa.** O script e o LLM recebem os tiles num raio N, declarado pelo cartucho, como já recebe quem joga na tela | ADR-0047 | antes do LLM (v0.2) |
| **Salto de tempo no modo máximo.** Hoje ele anda tick a tick; o salto exigiria entrar no diário de entradas | ADR-0047 | se algum soak ficar lento |
| **A necessidade "sono".** Pressão de sono que sobe acordado e só baixa dormindo. Uma noite que acabou tarde deixa o avatar com sono no dia seguinte | ADR-0041, ADR-0049 | quando houver quem vire a noite (LLM ou humano) |
| **Energia ao ficar acordado.** Gastar um pouco por hora acordado, para que ficar parado o dia inteiro tenha custo, como tem para uma pessoa. A tendência é que sim, mas pouco | revisão do M3 (12/out) | depois do M5, jogando |
| **Andar gasta energia?** Talvez sim, para abrir espaço para correr | revisão do M3 (12/out) | depois do M5, jogando |
| **Correr.** Movimento mais rápido que gasta mais energia que andar | revisão do M3 (12/out) | depois de decidir o custo de andar |
| **Fome em 100.** Hoje não tem consequência. A reserva de 3 rabanetes do script não cobre dois dias sem colheita (sem a R-001, a fome encosta em 100) | diário de 12/out | junto com o equilíbrio da energia |
| **Formato de mapa próprio e editor.** Um arquivo JSON ou binário com todos os detalhes do mapa (terreno, camadas, objetos, propriedades), feito num editor externo que seja parte do Campsverso. Até lá, vale o Tiled (`.tmj`) | ADR-0050 | antes de um segundo cenário, ou do vilarejo |
| **Renderer 3D** (three.js ou análogo), sobre o mesmo contrato `realtime` do canvas e do Phaser | ADR-0050 | depois do M6 |
| **Visitantes com login.** Separar as visões jogador e operador por credencial, e não só por conexão | ADR-0022, ADR-0050 | antes de abrir para fora de `127.0.0.1` |
| **Playwright.** Testes automáticos da tela num navegador de verdade | ADR-0050 | no M6 |
| **Ações padrão do mundo.** Ações que todo mundo tem (andar, esperar, talvez dormir), declaradas pelo kernel. Hoje, cada cartucho declara o próprio catálogo | ADR-0051 | quando houver um segundo cartucho |
| **Teclado e arrastar.** Atalhos de teclado para as ações e arrastar no mapa. No M5, só o mouse, com os cliques esquerdo e direito | ADR-0051 | depois do M6 |
