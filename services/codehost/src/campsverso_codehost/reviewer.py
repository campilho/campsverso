"""O revisor de outra família (ADR-0083, decisão 4; plano do M25, §2).

Um modelo que não é Claude lê o pedido, as regras do repositório e o diff da entrega, e escreve a
revisão que vai como comentário no PR. Fica fora do mundo, como o juiz da arena (ADR-0070): não é
robô nem avatar, não dá ordens ao dev e só aconselha o gerente, que decide mesclando ou devolvendo
o pedido no quadro. O comentário não chega ao dev.

É uma chamada só, sem ferramentas: o modelo responde em Markdown, e a primeira linha traz o
veredito (`mesclar`, `conferir` ou `devolver`). Sem ferramentas, a tradução da OpenRouter não tem
onde tropeçar (o Gemini desistiu no M21 numa chamada com ferramentas). Os modelos vêm em ordem: o
plano A revisa; se a chamada falhar, o mesmo pedido vai ao plano B, e o comentário diz quem
revisou e quem falhou.

As regras do repositório são as seções do `CLAUDE.md` que valem para um diff (os princípios, as
convenções e o "nunca faça") e a lista da constituição, o que o dev nunca muda. A lista de
palavras proibidas nunca vai ao modelo: ela é privada. A revisão do publicador já a conferiu no
diff, e o serviço a confere de novo no comentário antes de publicá-lo.
"""

import re
from collections.abc import Callable, Sequence
from dataclasses import dataclass

from campsverso_ports import Effort, ModelCallError, ModelPort, ModelRequest, request_sha256

VERDICTS = {
    "mesclar": "pode mesclar",
    "conferir": "confira antes de mesclar",
    "devolver": "devolva ao dev",
}
SEVERITIES = ("grave", "média", "leve")
GUIDE_SECTIONS = ("Princípios inegociáveis", "Convenções", "Nunca faça")
MAX_DIFF_CHARS = 150_000  # uns 40 mil tokens; o resto do diff fica de fora, com um aviso
MAX_TOKENS = 12_000  # o raciocínio e a revisão
EFFORT: Effort = "medium"

_VERDICT_LINE = re.compile(r"^\W*veredito\W*:?\W*(mesclar|conferir|devolver)\b", re.IGNORECASE)
_FINDING_LINE = re.compile(r"^\s*\d+\.\s+\W*(grave|m[ée]dia|leve)\b", re.IGNORECASE)

INSTRUCTIONS = """\
Você é o revisor de código do Campsverso, uma plataforma de simulação em Python e TypeScript. \
Você é de outra família de modelos: quem escreveu a entrega foi o dev do escritório, um modelo \
Claude, para um pedido do gerente, e ela virou um PR. Leia o pedido, as regras do repositório e o \
diff, e escreva a revisão que vai como comentário no PR, em português do Brasil. Você só \
aconselha: quem decide é o gerente.

O que procurar, nesta ordem:
1. O que quebra: erro de lógica, caso esquecido, condição invertida, limite errado, data ou \
número que não confere com o comentário ao lado.
2. Testes afrouxados ou apagados: uma asserção mais fraca, um teste pulado, um número de \
referência trocado para o teste passar.
3. A constituição: o dev nunca muda os caminhos da lista. Qualquer mudança neles é grave, mesmo \
com uma boa justificativa.
4. As regras do repositório: o determinismo (o relógio de parede, o `random` global), um SDK \
importado fora da raiz de composição, um contrato mudado sem o schema.
5. O pedido: a entrega faz o que o aceite pede?

Só aponte o que você mostra no diff, com o arquivo e a linha do lado novo. Não invente: se a \
entrega está boa, o veredito é mesclar, sem achados. Estilo e preferência não são achados. Não \
peça o que o diff não pode mostrar (o resto do repositório, o CI) como se fosse um defeito.

Responda em Markdown, sem cercas de código em volta, neste formato:
- a primeira linha é exatamente uma destas: `Veredito: mesclar`, `Veredito: conferir` ou \
`Veredito: devolver` (devolver quando houver um achado grave; conferir quando só houver achados \
médios ou leves, ou uma dúvida que o gerente deve olhar);
- depois, um parágrafo curto com o resumo;
- depois, se houver, os achados numa lista numerada, um por item, assim: \
`1. **grave** · caminho/do/arquivo.py:42 · o que está errado. Por que importa.` \
(a gravidade é grave, média ou leve)."""


@dataclass(frozen=True, slots=True)
class ReviewInput:
    """O que o revisor lê de uma entrega: o pedido do quadro e o diff."""

    number: int
    title: str
    description: str
    acceptance: str
    diff: str
    head: str


@dataclass(frozen=True, slots=True)
class Review:
    """A revisão de um modelo: o veredito, o texto do comentário e o que custou."""

    model: str
    verdict: str | None  # mesclar, conferir, devolver; None quando a primeira linha não diz
    text: str  # a revisão sem a linha do veredito
    findings: int
    cost_usd: float | None
    replayed: bool
    served_by: str | None
    prompt_sha256: str
    failed: tuple[tuple[str, str], ...] = ()  # quem falhou antes: (modelo, tipo do erro)
    raw: str = ""  # a resposta inteira, como veio (a calibração a guarda)


def guide_from(claude_md: str, sections: Sequence[str] = GUIDE_SECTIONS) -> str:
    """As seções do `CLAUDE.md` que valem para um diff; sem elas, o arquivo inteiro."""
    found: list[str] = []
    keep = False
    for line in claude_md.splitlines():
        if line.startswith("## "):
            keep = line[3:].strip() in sections
        if keep:
            found.append(line)
    return "\n".join(found).strip() or claude_md.strip()


def review_request(
    model: str,
    item: ReviewInput,
    guide: str,
    constitution: Sequence[str],
    *,
    effort: Effort = EFFORT,
    max_tokens: int = MAX_TOKENS,
) -> ModelRequest:
    """O pedido ao revisor: as instruções no sistema; o pedido, as regras e o diff na mensagem."""
    diff = item.diff
    cut = ""
    if len(diff) > MAX_DIFF_CHARS:
        cut = (
            f"\n\n(O diff tem {len(item.diff)} caracteres; aqui vão só os primeiros "
            f"{MAX_DIFF_CHARS}. Diga na revisão que o resto ficou de fora.)"
        )
        diff = diff[:MAX_DIFF_CHARS]
    lines = [f"# O pedido {item.number}: {item.title}", ""]
    if item.description:
        lines += [item.description, ""]
    if item.acceptance:
        lines += [f"**Aceite:** {item.acceptance}", ""]
    lines += ["# As regras do repositório", "", guide, ""]
    lines += ["# A constituição: os caminhos que o dev nunca muda (prefixos)", ""]
    lines += [f"- `{path}`" for path in constitution]
    lines += ["", "# O diff da entrega", "", "```diff", diff.rstrip("\n"), "```" + cut]
    return ModelRequest(
        model=model,
        messages=[{"role": "user", "content": [{"type": "text", "text": "\n".join(lines)}]}],
        system=INSTRUCTIONS,
        max_tokens=max_tokens,
        effort=effort,
        purpose="review",
    )


def findings_of(body: str) -> list[tuple[str, str]]:
    """Os achados da lista numerada: a gravidade (grave, média, leve) e a linha inteira."""
    found: list[tuple[str, str]] = []
    for line in body.splitlines():
        match = _FINDING_LINE.match(line)
        if match is not None:
            severity = match.group(1).lower().replace("media", "média")
            found.append((severity, line.strip()))
    return found


def parse(text: str) -> tuple[str | None, str, int]:
    """O veredito da primeira linha que o diz (entre as cinco primeiras), o texto sem ela e
    quantos achados a lista numerada tem."""
    lines = text.strip().splitlines()
    verdict: str | None = None
    for index, line in enumerate(lines[:5]):
        found = _VERDICT_LINE.match(line)
        if found is not None:
            verdict = found.group(1).lower()
            del lines[index]
            break
    body = "\n".join(lines).strip()
    return verdict, body, len(findings_of(body))


class Reviewer:
    """Revisa uma entrega com o primeiro modelo da lista que responder."""

    def __init__(
        self,
        ports: Callable[[str], ModelPort],
        models: Sequence[str],
        guide: str,
        constitution: Sequence[str],
        *,
        effort: Effort = EFFORT,
        max_tokens: int = MAX_TOKENS,
    ) -> None:
        if not models:
            raise ValueError("o revisor precisa de pelo menos um modelo")
        self._ports = ports
        self.models = tuple(models)
        self._guide = guide
        self._constitution = tuple(constitution)
        self._effort: Effort = effort
        self._max_tokens = max_tokens

    def request(self, model: str, item: ReviewInput) -> ModelRequest:
        return review_request(
            model,
            item,
            self._guide,
            self._constitution,
            effort=self._effort,
            max_tokens=self._max_tokens,
        )

    async def review(self, item: ReviewInput) -> Review | None:
        """A revisão do primeiro que responder; None quando todos falham."""
        failed: list[tuple[str, str]] = []
        for model in self.models:
            request = self.request(model, item)
            try:
                response = await self._ports(model).complete(request)
            except ModelCallError as error:
                failed.append((model, error.kind))
                continue
            text = response.text()
            if response.stop_reason == "refusal" or not text.strip():
                failed.append((model, "empty" if not text.strip() else "refusal"))
                continue
            verdict, body, findings = parse(text)
            return Review(
                model=model,
                verdict=verdict,
                text=body,
                findings=findings,
                cost_usd=response.usage.cost_usd,
                replayed=response.replayed,
                served_by=response.served_by,
                prompt_sha256=request_sha256(request),
                failed=tuple(failed),
                raw=text,
            )
        return None


def _money(value: float) -> str:
    return f"US$ {value:.3f}".replace(".", ",")


def comment_body(review: Review, item: ReviewInput) -> str:
    """O comentário do PR: o veredito, a revisão e quem revisou, com o custo."""
    label = VERDICTS.get(review.verdict or "", "sem veredito na primeira linha")
    route = f", servido por {review.served_by}" if review.served_by else ""
    notes = [f"Revisado por `{review.model}` pela OpenRouter{route}, sobre `{item.head[:8]}`"]
    for model, kind in review.failed:
        notes.append(f"antes, `{model}` falhou ({kind})")
    if review.replayed:
        notes.append("resposta reproduzida da fita, sem custo")
    elif review.cost_usd is not None:
        notes.append(_money(review.cost_usd))
    footer = (
        "; ".join(notes)
        + ". O revisor é de outra família e só aconselha: quem decide é o gerente, mesclando ou "
        "devolvendo o pedido no quadro (ADR-0083)."
    )
    return "\n".join(
        [
            f"### Revisão do pedido {item.number}: {label}",
            "",
            review.text or "(a revisão veio sem texto além do veredito)",
            "",
            "---",
            "",
            f"<sub>{footer}</sub>",
        ]
    )
