# Plano: a luz do escritório

Em 21/11, o usuário entrou como o gerente às 22h, e a sala estava toda escura, sem como acender. Ele pediu ao vigia ("@Vigia pode acender a luz da sala?"), e o vigia não respondeu.

**Por quê:**
- A luz da sala é só desenho da tela (o `lights` do `art.json`, ADR-0082): dia das 6h às 18h, as luminárias das 18h às 21h, escuro depois, só com a lanterna do vigia. Não existe luz no mundo.
- O vigia é um script que só faz a ronda: ele não lê o que ouve.

**A escolha do usuário:** um interruptor de verdade no mundo, e o vigia que atende o pedido.

## 1. O que muda

1. **O interruptor:** uma entidade nova do cenário, na parede ao lado da porta, com o atributo visível `acesa`. O estado é do mundo, igual para todos: a tela do gerente, a do operador e a percepção do dev.
2. **O temporizador do prédio:** um sistema do cartucho acende às 18:00 e apaga às 21:00, com as horas nos dados (`office.yaml`). Sem ninguém mexer, a sala fica como hoje.
3. **A ação "acender a luz" ou "apagar a luz"** (`switch_light`): do gerente, do dev e do vigia, ao lado do interruptor. O kernel valida e troca o `acesa`, e o cartucho publica `campsverso.office.light.switched.v1` (quem e para que estado). É um contrato novo, com o schema, os exemplos e o CHANGELOG.
4. **A tela:**
   - de dia, nada muda;
   - à noite, as luminárias valem se a luz estiver acesa, e o escuro, se não;
   - a lanterna do vigia continua;
   - o horário do `art.json` passa a dizer só o dia e a noite;
   - o interruptor ganha um desenho de 32 × 32 no estilo, aceso e apagado, feito em código como as outras peças próprias;
   - o menu do clique direito oferece a ação;
   - a conversa mostra a linha "Gerente acendeu a luz".
5. **O vigia:**
   - quando alguém fala com ele e a fala tem "luz", ele responde ("Já vou.") e vai acender ou apagar, conforme o pedido;
   - na ronda, se a luz estiver acesa e não houver ninguém na sala além dele, ele apaga.
6. **O dev:** não ganha a ferramenta agora; ele vê o interruptor e o estado na percepção. Ensinar a mente a usar a luz fica no `futuro.md`.

## 2. Como conferir

- **Os testes do cartucho:** a ação (o gerente ao lado acende; longe, a recusa; o fato publicado), o temporizador (18:00 e 21:00) e o determinismo.
- **Os testes do script:** o vigia responde e vai acender quando o pedem; na ronda, apaga a sala vazia; não mexe na luz com gente na sala.
- **Os testes da tela:** o modo da luz pela hora e pelo interruptor.
- **O navegador:** à noite, o gerente acende pelo menu, e a sala clareia.
- **O `make check`** e o `make ui-e2e`, e a fita do escritório, se a percepção do dev mudar.

## 3. Custo e ordem

Nada de API, a não ser regravar a fita do escritório (cerca de US$ 0,06), se a foto do dev mudar com o interruptor. É uma parte pequena, como as do M25, que vai ao `main` inteira, com uma ADR curta.
