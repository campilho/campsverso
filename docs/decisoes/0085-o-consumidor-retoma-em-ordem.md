# ADR-0085 — O consumidor durável retoma em ordem

**Status:** aceita · **Data:** 2026-11-21 · **Marco:** M25
**Complementa:** ADR-0017 (os consumidores duráveis com confirmação explícita); ADR-0024 (o NATS local); ADR-0083 (o escritório vivo sob o supervisor)

## Contexto

Cada serviço lê os streams com um consumidor durável e confirma cada lote depois do handler. Quando o processo cai no meio de um lote, o que ele recebeu e não confirmou fica "em voo" no JetStream. O consumidor que retoma recebe primeiro o que é novo; o lote em voo só volta depois do `ack_wait` (30 s), fora de ordem.

O gateway e a percepção guardam uma marca d'água: um evento com `seq` até o último aplicado é tido como já visto. O lote que volta atrasado tem `seq` menor que os eventos novos já aplicados, e é descartado. Quando o processo caiu antes de gravar o lote, o evento se perde de vez.

No `make check` de 20/nov, o `test_gateway_visoes_comandos_e_a6` falhou em 3 de 4 rodadas completas: depois do `kill -9`, o Camps aparecia noutro lugar, ou com 3 sementes em vez de 2. O bug vem do M4. O consumidor de lotes menores do fim do M24 (b28dab7) deixou o gateway mais tempo dentro do lote e da gravação, e a janela cresceu. É também o caminho mais provável do A6 da percepção que falhou em 22/out, com duas fotos com o mesmo `seq`, investigado no M16 sem achar o caminho no código.

No M25, o supervisor do escritório vivo vai derrubar e subir os processos a cada troca de versão. A queda no meio de um lote deixa de ser rara.

## Decisão

1. **Ao retomar um consumidor durável, o adaptador do NATS o rebobina até o primeiro evento não confirmado,** antes de pedir o próximo lote. O lote em voo volta na hora e em ordem, antes do que é novo. O processo que volta recebe tudo como se não tivesse caído, e o que ele já tinha gravado sai pela marca d'água, como uma reentrega comum.
2. **O caminho é o `CONSUMER.RESET` do JetStream** (nats-server 2.14), com `seq` = último confirmado + 1. Ele não apaga o consumidor nem muda a configuração. A sonda de 21/nov o conferiu: com e sem filtro de assunto, ele reentrega em ordem; sem nada em voo, não muda nada; um consumidor que não existe não responde.
3. **Só rebobina quem tem algo em voo** (`num_ack_pending` > 0). O pedido tem prazo de 2 s. Sem permissão, num servidor antigo ou com erro, o consumidor segue como antes, com o aviso `nats.rewind_failed`; quando rebobina, o aviso é `nats.rewound`, com o número de eventos em voo.
4. **Cada usuário do NATS pode rebobinar os consumidores dos streams que já consulta** (`$JS.API.CONSUMER.RESET.<STREAM>.*`, ao lado do `CONSUMER.INFO`). Rebobinar só reentrega: nada se apaga, e ninguém passa a ler o que não lia (princípio 5). O kernel e o arquivador já tinham `$JS.API.>`.
5. **Fica de fora a alternativa de apagar e recriar o consumidor** a partir do último confirmado. Ela pede a permissão de apagar, que ninguém além do operador tem hoje, e perde a configuração no meio do caminho.

## Consequências

- **O gateway, a percepção, o kernel, a guarda e o publicador** voltam de um `kill -9` sem perder evento e sem receber nenhum fora de ordem.
- **O `caught_up` deixa de esperar o `ack_wait`** depois de uma queda: ele esperava `num_ack_pending` zerar, e o que estava em voo de um processo morto só zerava em 30 s.
- **Um consumidor de outro serviço pode ser rebobinado por engano.** Isso só reentrega, e todos os serviços já tratam a reentrega.
- **O projeto passa a depender do nats-server 2.14** para esta garantia, fixado no `make tools`. Num servidor antigo, o aviso mostra que ela não vale.
- **Dois processos com o mesmo durável ao mesmo tempo** receberiam o lote em voo do outro. Isso já era proibido: cada consumidor é de um processo só.
