"""Os scripts do escritório (ADR-0078): a decisão de cada um a partir de uma foto."""

from typing import Any

from campsverso_office_script import DevScript, GuardScript, ManagerScript, staff


def _ticket(number: int, estado: str, dono: str | None = None, trabalho: int = 0) -> dict[str, Any]:
    return {
        "entity_id": f"pedido-{number:03d}",
        "kind": "ticket",
        "container_id": "quadro",
        "attributes": {
            "numero": number,
            "titulo": f"Pedido {number}",
            "estado": estado,
            "dono": dono,
            "tamanho": "P",
            "trabalho": trabalho,
            "comentario": None,
        },
    }


def _view(
    me: str = "camps",
    at: tuple[int, int] = (9, 3),
    hhmm: str = "10:00",
    tickets: list[dict[str, Any]] | None = None,
    heard: list[dict[str, Any]] | None = None,
    manager_in: bool = True,
) -> dict[str, Any]:
    entities: list[dict[str, Any]] = [
        {"entity_id": "quadro", "kind": "board", "position": {"x": 9, "y": 2}, "attributes": {}},
        {
            "entity_id": "mesa",
            "kind": "desk",
            "position": {"x": 5, "y": 6},
            "attributes": {"dono": "camps"},
        },
        {"entity_id": "cadeira", "kind": "chair", "position": {"x": 5, "y": 7}, "attributes": {}},
        {
            "entity_id": "camps",
            "kind": "avatar",
            "position": {"x": at[0], "y": at[1]},
            "attributes": {"papel": "dev"},
        },
        {
            "entity_id": "gerente",
            "kind": "avatar",
            **({"position": {"x": 9, "y": 4}} if manager_in else {}),
            "attributes": {"papel": "gerente"},
        },
        *(tickets or []),
    ]
    view: dict[str, Any] = {
        "clock": {"tick": 0, "sim_time": f"2026-11-16T{hhmm}:00-03:00", "day": 1, "phase": "manha"},
        "weather": {"condition": "desconhecido", "day": 1},
        "self": {
            "entity_id": me,
            "position": {"x": at[0], "y": at[1]},
            "needs": {},
            "asleep": False,
        },
        "containers": [],
        "entities": entities,
    }
    if heard:
        view["heard"] = heard
    return view


def _dev() -> DevScript:
    script = DevScript.load()
    script.greeted = 1  # o bom-dia já foi
    return script


def test_o_dev_responde_a_quem_falou_com_ele_antes_de_tudo() -> None:
    heard = [{"tick": 5, "avatar_id": "gerente", "text": "Tudo certo?", "listener_id": "camps"}]
    proposal = _dev().decide(_view(heard=heard, tickets=[_ticket(1, "a_fazer")]))
    assert proposal["action"] == "say"
    assert proposal["params"] == {"text": "Anotado.", "to": "gerente"}


def test_o_dev_pega_o_pedido_mais_antigo_no_quadro() -> None:
    view = _view(tickets=[_ticket(2, "a_fazer"), _ticket(1, "a_fazer")])
    proposal = _dev().decide(view)
    assert proposal == {
        "action": "take_ticket",
        "params": {"target": "pedido-001"},
        "intent": "pegar o pedido 1",
    }
    far = _dev().decide(_view(at=(5, 7), tickets=[_ticket(1, "a_fazer")]))
    assert far["action"] == "move"
    assert far["params"] == {"near": "quadro"}


def test_o_dev_avisa_trabalha_em_blocos_e_entrega() -> None:
    dev = _dev()
    doing = [_ticket(1, "fazendo", "camps")]
    assert dev.decide(_view(at=(5, 7), tickets=doing))["action"] == "say"  # avisa que pegou
    work = dev.decide(_view(at=(5, 7), tickets=doing))
    assert work["action"] == "work"
    assert work["params"] == {"seconds": 60}
    walk = dev.decide(_view(at=(9, 3), tickets=doing))
    assert walk["action"] == "move"
    assert walk["params"] == {"target": {"x": 5, "y": 7}}
    done = [_ticket(1, "fazendo", "camps", trabalho=900)]
    assert dev.decide(_view(at=(5, 7), tickets=done))["action"] == "deliver"


def test_o_dev_avisa_que_vai_almocar_uma_vez_nos_minutos_antes() -> None:
    dev = _dev()
    doing = [_ticket(1, "fazendo", "camps")]
    dev.announced.add("pedido-001")
    assert dev.decide(_view(at=(5, 7), hhmm="11:57", tickets=doing))["action"] == "work"
    notice = dev.decide(_view(at=(5, 7), hhmm="11:58", tickets=doing))
    assert notice["action"] == "say"
    assert notice["params"] == {"text": "Vou almoçar. Volto à uma.", "to": "gerente"}
    assert dev.decide(_view(at=(5, 7), hhmm="11:59", tickets=doing))["action"] == "work"
    alone = _dev().decide(_view(at=(5, 7), hhmm="11:59", manager_in=False))
    assert alone["params"] == {"text": "Vou almoçar. Volto à uma."}  # sem o gerente, para a sala


def test_sem_pedido_o_dev_espera_na_mesa() -> None:
    proposal = _dev().decide(_view(at=(5, 7)))
    assert proposal["action"] == "wait"
    assert proposal["params"] == {"seconds": 60}


def test_o_vigia_faz_a_ronda_no_comeco_da_hora_e_senta_no_resto() -> None:
    guard = staff("vigia")
    assert isinstance(guard, GuardScript)
    rounds = guard.decide(_view(me="vigia", at=(11, 12), hhmm="22:02"))
    assert rounds["action"] == "move"
    assert rounds["intent"] == "fazer a ronda"
    seated = guard.decide(_view(me="vigia", at=(11, 12), hhmm="22:30"))
    assert seated["action"] == "wait"


def test_o_gerente_script_escreve_o_que_venceu_e_devolve_um_de_cada_tres() -> None:
    manager = staff("gerente")
    assert isinstance(manager, ManagerScript)
    manager.greeted = 1
    write = manager.decide(_view(me="gerente", at=(9, 3), hhmm="09:31"))
    assert write["action"] == "write_ticket"
    assert write["params"]["title"] == "Ferramenta de busca no código (dia 1)"
    third = [_ticket(3, "entregue", "camps")]
    returned = manager.decide(_view(me="gerente", at=(9, 3), hhmm="09:00", tickets=third))
    assert returned["action"] == "return_ticket"
    first = [_ticket(1, "entregue", "camps")]
    accepted = manager.decide(_view(me="gerente", at=(9, 3), hhmm="09:00", tickets=first))
    assert accepted["action"] == "accept_ticket"


def test_o_gerente_script_nao_escreve_no_dia_em_que_o_dev_nao_veio() -> None:
    """No feriado e no fim de semana o dev não vem, e os pedidos ficariam para o dia útil seguinte
    (o soak de 5 dias do M23 caiu no 20/11)."""
    manager = staff("gerente")
    assert isinstance(manager, ManagerScript)
    manager.greeted = 1
    holiday = _view(me="gerente", at=(9, 3), hhmm="09:31")
    for item in holiday["entities"]:
        if item["entity_id"] == "camps":
            del item["position"]
    assert manager.decide(holiday)["action"] == "wait"
    assert manager.decide(_view(me="gerente", at=(9, 3), hhmm="09:31"))["action"] == "write_ticket"
