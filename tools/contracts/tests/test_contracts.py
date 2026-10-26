import json
import shutil
from pathlib import Path

from campsverso_tools.contracts import catalog, checks


def test_contratos_do_repositorio_seguem_as_convencoes(contracts: catalog.Contracts) -> None:
    assert checks.check_conventions(contracts) == []


def test_exemplos_do_repositorio_validam_e_cobrem_todos_os_tipos(
    contracts: catalog.Contracts,
) -> None:
    assert checks.check_examples(contracts) == []


def test_catalogo_tem_64_eventos_e_9_comandos(contracts: catalog.Contracts) -> None:
    """Os 38 da v0.1, os dois de sono v2 (ADR-0042), o delta da percepção (ADR-0056), os quatro de
    modelo e orçamento (ADR-0058), os cinco de memória (ADR-0060), a entidade guardada
    (ADR-0062), a entidade removida, a troca de estação e a planta comida (ADR-0067), e a entrada
    e a saída do avatar e os três do contrato de trabalho (ADR-0072)."""
    kinds = [f.kind for f in contracts.by_type.values()]
    assert kinds.count("event") == 64
    assert kinds.count("command") == 9


def test_exemplo_invalido_em_valid_quebra_o_check(contracts_copy: Path) -> None:
    """Critério de aceite do M0: um exemplo inválido quebra o CI."""
    invalid = contracts_copy / "examples" / "invalid" / "04-regra-oculta-como-world.json"
    event = json.loads(invalid.read_text(encoding="utf-8"))["event"]
    target = contracts_copy / "examples" / "valid" / f"{event['type']}--intruso.json"
    target.write_text(json.dumps(event), encoding="utf-8")

    codes = {p.code for p in checks.check_examples(catalog.load(contracts_copy))}

    assert codes == {"valid_example_fails"}


def test_tipo_sem_exemplo_quebra_o_check(contracts_copy: Path) -> None:
    (contracts_copy / "examples" / "valid" / "campsverso.world.clock.paused.v1.json").unlink()

    problems = checks.check_examples(catalog.load(contracts_copy))

    assert [p.code for p in problems] == ["missing_example"]


def test_exemplo_invalido_que_passa_quebra_o_check(contracts_copy: Path) -> None:
    valid = contracts_copy / "examples" / "valid" / "campsverso.world.clock.paused.v1.json"
    document = {
        "expect_error": "payload_schema",
        "event": json.loads(valid.read_text(encoding="utf-8")),
    }
    (contracts_copy / "examples" / "invalid" / "99-passa.json").write_text(
        json.dumps(document), encoding="utf-8"
    )

    problems = checks.check_examples(catalog.load(contracts_copy))

    assert [p.code for p in problems] == ["invalid_example_passes"]


def test_schema_com_campo_camel_case_quebra_as_convencoes(contracts_copy: Path) -> None:
    path = contracts_copy / "events" / "world" / "clock.paused.v1.schema.json"
    schema = json.loads(path.read_text(encoding="utf-8"))
    schema["properties"]["pausedBy"] = {"type": "string"}
    path.write_text(json.dumps(schema), encoding="utf-8")

    codes = {p.code for p in checks.check_conventions(catalog.load(contracts_copy))}

    assert codes == {"field_name"}


def test_comando_com_visibilidade_diferente_de_observer_quebra_as_convencoes(
    contracts_copy: Path,
) -> None:
    path = contracts_copy / "commands" / "clock" / "pause.v1.schema.json"
    schema = json.loads(path.read_text(encoding="utf-8"))
    schema["x-visibility"] = "agent"
    path.write_text(json.dumps(schema), encoding="utf-8")

    codes = {p.code for p in checks.check_conventions(catalog.load(contracts_copy))}

    assert "visibility" in codes


def test_schema_fora_do_lugar_quebra_as_convencoes(contracts_copy: Path) -> None:
    source = contracts_copy / "events" / "world" / "clock.paused.v1.schema.json"
    shutil.move(source, contracts_copy / "events" / "action" / "clock.paused.v1.schema.json")

    codes = {p.code for p in checks.check_conventions(catalog.load(contracts_copy))}

    assert {"schema_id", "type_name"} <= codes
