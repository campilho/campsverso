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
    at: tuple[int, int] = (3, 2),  # ao lado do quadro, na parede (ADR-0082)
    hhmm: str = "10:00",
    tickets: list[dict[str, Any]] | None = None,
    heard: list[dict[str, Any]] | None = None,
    manager_in: bool = True,
    copa: bool = False,
    day: int = 1,
) -> dict[str, Any]:
    entities: list[dict[str, Any]] = [
        {"entity_id": "quadro", "kind": "board", "position": {"x": 3, "y": 1}, "attributes": {}},
        {
            "entity_id": "mesa",
            "kind": "desk",
            "position": {"x": 4, "y": 4},
            "attributes": {"dono": "camps"},
        },
        {"entity_id": "cadeira", "kind": "chair", "position": {"x": 4, "y": 5}, "attributes": {}},
        {
            "entity_id": "camps",
            "kind": "avatar",
            "position": {"x": at[0], "y": at[1]},
            "attributes": {"papel": "dev"},
        },
        {
            "entity_id": "gerente",
            "kind": "avatar",
            **({"position": {"x": 3, "y": 2}} if manager_in else {}),
            "attributes": {"papel": "gerente"},
        },
        *(tickets or []),
        *(COPA if copa else []),
    ]
    view: dict[str, Any] = {
        "clock": {
            "tick": 0,
            "sim_time": f"2026-11-16T{hhmm}:00-03:00",
            "day": day,
            "phase": "manha",
        },
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


def _thing(entity_id: str, kind: str, x: int, y: int) -> dict[str, Any]:
    return {"entity_id": entity_id, "kind": kind, "position": {"x": x, "y": y}, "attributes": {}}


# A copa e o banheiro na planta nova (ADR-0082): a linha da cozinha na linha 9, as mesinhas com as
# cadeiras de lado na 11, e as portas do banheiro na parede de baixo, para o corredor.
COPA: list[dict[str, Any]] = [
    _thing("lixeira", "trash", 12, 9),
    _thing("maquina-cafe", "coffee_machine", 13, 9),
    _thing("micro-ondas", "microwave", 16, 9),
    _thing("geladeira", "fridge", 17, 9),
    _thing("bebedouro", "water_cooler", 18, 9),
    _thing("mesa-copa-1", "copa_table", 13, 11),
    _thing("cadeira-copa-1", "copa_chair", 12, 11),
    _thing("porta-banheiro", "restroom_door", 2, 13),
    _thing("sofa", "sofa", 16, 5),
]


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
    far = _dev().decide(_view(at=(4, 5), tickets=[_ticket(1, "a_fazer")]))
    assert far["action"] == "move"
    assert far["params"] == {"near": "quadro"}


def test_o_dev_avisa_trabalha_em_blocos_e_entrega() -> None:
    dev = _dev()
    doing = [_ticket(1, "fazendo", "camps")]
    assert dev.decide(_view(at=(4, 5), tickets=doing))["action"] == "say"  # avisa que pegou
    work = dev.decide(_view(at=(4, 5), tickets=doing))
    assert work["action"] == "work"
    assert work["params"] == {"seconds": 60}
    walk = dev.decide(_view(at=(3, 2), tickets=doing))
    assert walk["action"] == "move"
    assert walk["params"] == {"target": {"x": 4, "y": 5}}
    done = [_ticket(1, "fazendo", "camps", trabalho=900)]
    deliver = dev.decide(_view(at=(4, 5), tickets=done))
    assert deliver["action"] == "deliver"
    # A sessão na oficina (ADR-0080): o controlador a roda antes de propor a entrega.
    session = deliver["workshop"]
    assert session["ticket_id"] == "pedido-001"
    assert [step["tool"] for step in session["steps"]] == [
        "ler",
        "escrever",
        "ver_mudancas",
        "pronto",
    ]
    assert session["steps"][1]["args"]["path"] == "docs/oficina/pedido-001.md"


def test_o_dev_avisa_que_vai_almocar_uma_vez_nos_minutos_antes() -> None:
    dev = _dev()
    doing = [_ticket(1, "fazendo", "camps")]
    dev.announced.add("pedido-001")
    assert dev.decide(_view(at=(4, 5), hhmm="11:57", tickets=doing))["action"] == "work"
    notice = dev.decide(_view(at=(4, 5), hhmm="11:58", tickets=doing))
    assert notice["action"] == "say"
    assert notice["params"] == {"text": "Hora do almoço. Vou para a copa.", "to": "gerente"}
    assert dev.decide(_view(at=(4, 5), hhmm="11:59", tickets=doing))["action"] == "work"
    alone = _dev().decide(_view(at=(4, 5), hhmm="11:59", manager_in=False))
    assert alone["params"] == {
        "text": "Hora do almoço. Vou para a copa."
    }  # sem o gerente, para a sala


def test_sem_pedido_o_dev_espera_na_mesa() -> None:
    proposal = _dev().decide(_view(at=(4, 5)))
    assert proposal["action"] == "wait"
    assert proposal["params"] == {"seconds": 60}


def test_o_vigia_faz_a_ronda_no_comeco_da_hora_e_senta_no_resto() -> None:
    guard = staff("vigia")
    assert isinstance(guard, GuardScript)
    rounds = guard.decide(_view(me="vigia", at=(11, 14), hhmm="22:02"))
    assert rounds["action"] == "move"
    assert rounds["intent"] == "fazer a ronda"
    seated = guard.decide(_view(me="vigia", at=(11, 14), hhmm="22:30"))  # o posto, no corredor
    assert seated["action"] == "wait"


def test_o_gerente_script_escreve_o_que_venceu_e_devolve_um_de_cada_tres() -> None:
    manager = staff("gerente")
    assert isinstance(manager, ManagerScript)
    manager.greeted = 1
    write = manager.decide(_view(me="gerente", at=(3, 2), hhmm="09:31"))
    assert write["action"] == "write_ticket"
    assert write["params"]["title"] == "Ferramenta de busca no código (dia 1)"
    third = [_ticket(3, "entregue", "camps")]
    returned = manager.decide(_view(me="gerente", at=(3, 2), hhmm="09:00", tickets=third))
    assert returned["action"] == "return_ticket"
    first = [_ticket(1, "entregue", "camps")]
    accepted = manager.decide(_view(me="gerente", at=(3, 2), hhmm="09:00", tickets=first))
    assert accepted["action"] == "accept_ticket"


def test_o_gerente_script_nao_escreve_no_dia_em_que_o_dev_nao_veio() -> None:
    """No feriado e no fim de semana o dev não vem, e os pedidos ficariam para o dia útil seguinte
    (o soak de 5 dias do M23 caiu no 20/11)."""
    manager = staff("gerente")
    assert isinstance(manager, ManagerScript)
    manager.greeted = 1
    holiday = _view(me="gerente", at=(3, 2), hhmm="09:31")
    for item in holiday["entities"]:
        if item["entity_id"] == "camps":
            del item["position"]
    assert manager.decide(holiday)["action"] == "wait"
    assert manager.decide(_view(me="gerente", at=(3, 2), hhmm="09:31"))["action"] == "write_ticket"


# ------------------------------------------------------------------ a rotina (ADR-0080)


def test_as_pausas_do_dia_saem_de_um_sorteio_que_se_repete() -> None:
    routine = _dev().routine
    assert routine is not None
    plan = routine.plan("camps", 3)
    assert plan == routine.plan("camps", 3)  # o mesmo dia, as mesmas pausas
    assert plan != routine.plan("camps", 4)
    assert sorted({action for _, action in plan}) == ["coffee", "drink", "restroom", "videogame"]
    assert all(9 * 60 + 20 <= minute <= 17 * 60 + 40 for minute, _ in plan)


def test_sem_pedido_a_rotina_vai_ate_a_coisa_e_faz_a_pausa() -> None:
    dev = _dev()
    assert dev.routine is not None
    first, action = dev.routine.plan("camps", 1)[0]
    hhmm = f"{first // 60:02d}:{first % 60:02d}"
    place = {"drink": "bebedouro", "coffee": "maquina-cafe", "restroom": "porta-banheiro"}[action]
    walk = dev.decide(_view(at=(4, 5), hhmm=hhmm, copa=True))
    assert walk["action"] == "move"
    assert walk["params"] == {"near": place}
    assert walk["intent"].startswith("rotina:")
    spot = next(e["position"] for e in COPA if e["entity_id"] == place)
    beside = (spot["x"], spot["y"] + 1)  # ao lado, para a conta do script
    done = dev.decide(_view(at=beside, hhmm=hhmm, copa=True))
    assert done["action"] == action
    again = dev.decide(_view(at=beside, hhmm=hhmm, copa=True))
    assert again["action"] != action  # cada pausa uma vez


def test_na_hora_do_almoco_o_dev_vai_para_a_copa_mesmo_com_pedido() -> None:
    """O almoço em etapas (ADR-0082): a geladeira, o micro-ondas, a mesinha (sentado na cadeira de
    lado) e o lixo; depois, de volta ao pedido."""
    dev = _dev()
    dev.announced.add("pedido-001")
    doing = [_ticket(1, "fazendo", "camps")]

    def step(at: tuple[int, int], hhmm: str = "12:05") -> dict[str, Any]:
        return dev.decide(_view(at=at, hhmm=hhmm, tickets=doing, copa=True))

    assert step((4, 5))["params"] == {"near": "geladeira"}
    fridge = step((17, 10))
    assert (fridge["action"], fridge["intent"]) == ("fridge", "rotina: pegar o almoço na geladeira")
    assert step((17, 10))["action"] == "microwave"  # o micro-ondas fica ao lado, na diagonal
    assert step((17, 10))["params"] == {"target": {"x": 12, "y": 11}}  # a cadeira da copa
    eat = step((12, 11), "12:08")
    assert eat == {"action": "lunch", "params": {}, "intent": "rotina: almoçar na copa"}
    assert step((12, 11), "12:55")["params"] == {"near": "lixeira"}
    assert step((12, 10), "12:55")["action"] == "trash"
    back = step((12, 10), "12:56")
    assert back["params"] == {"target": {"x": 4, "y": 5}}  # de volta ao pedido


def test_a_rotina_joga_videogame_no_sofa_a_tarde() -> None:
    """ADR-0082: uma partida por dia, depois do almoço, do tapete logo abaixo do sofá."""
    dev = _dev()
    assert dev.routine is not None
    games = [m for m, action in dev.routine.plan("camps", 1) if action == "videogame"]
    assert len(games) == 1
    assert 13 * 60 <= games[0] <= 17 * 60 + 40
    dev.routine.done[1] = {
        i for i, (_, a) in enumerate(dev.routine.plan("camps", 1)) if a != "videogame"
    }
    hhmm = f"{games[0] // 60:02d}:{games[0] % 60:02d}"
    walk = dev.decide(_view(at=(4, 5), hhmm=hhmm, copa=True))
    assert walk["params"] == {"target": {"x": 16, "y": 6}}
    play = dev.decide(_view(at=(16, 6), hhmm=hhmm, copa=True))
    assert play["action"] == "videogame"
