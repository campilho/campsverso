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


def test_o_dev_so_pega_o_pedido_dele_ou_o_de_ninguem() -> None:
    """ADR-0093, decisão 8: o pedido 1 é de outro dev; o dev-script pega o 2, que é de ninguém."""
    other = {**_ticket(1, "a_fazer")}
    other["attributes"] = {**other["attributes"], "para": "kenji"}
    proposal = _dev().decide(_view(tickets=[other, _ticket(2, "a_fazer")]))
    assert proposal["params"] == {"target": "pedido-002"}
    mine = {**_ticket(1, "a_fazer")}
    mine["attributes"] = {**mine["attributes"], "para": "camps"}
    assert _dev().decide(_view(tickets=[mine]))["params"] == {"target": "pedido-001"}


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


def test_antes_de_entregar_o_dev_chama_o_robo_que_tem_reserva() -> None:
    """O testador na bancada, com os argumentos do registro (`reserva`): o dev-script o chama
    depois de escrever. O robô sem reserva fica na bancada (só a mente sabe o que pedir a ele)."""
    done = [_ticket(1, "fazendo", "camps", trabalho=900)]
    tester = {
        "entity_id": "robo-testador",
        "kind": "robot",
        "position": {"x": 7, "y": 4},
        "attributes": {"nome": "testador", "modulo": "tools.robos.testador", "reserva": "a b"},
    }
    reviewer = {
        "entity_id": "robo-revisor",
        "kind": "robot",
        "position": {"x": 8, "y": 4},
        "attributes": {"nome": "revisor", "modulo": "tools.robos.revisor"},
    }
    view = _view(at=(4, 5), tickets=[*done, reviewer, tester])
    dev = _dev()
    dev.announced.add("pedido-001")
    session = dev.decide(view)["workshop"]
    assert [step["tool"] for step in session["steps"]] == [
        "ler",
        "escrever",
        "chamar_robo",
        "ver_mudancas",
        "pronto",
    ]
    assert session["steps"][2]["args"] == {
        "robo": "robo-testador",
        "modulo": "tools.robos.testador",
        "argumentos": ["a", "b"],
    }


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
    # No ponto da vez, ele fica olhando a sala; antes, voltava à cadeira e ia de novo ao ponto,
    # indo e vindo da porta a cada segundo (o escritório vivo, 21/nov às 11:00).
    looking = guard.decide(_view(me="vigia", at=(9, 12), hhmm="11:00"))
    assert (looking["action"], looking["intent"]) == ("wait", "olhar a sala")
    following = guard.decide(_view(me="vigia", at=(9, 12), hhmm="11:02"))
    assert (following["action"], following["intent"]) == ("move", "fazer a ronda")


SWITCH = {"entity_id": "interruptor", "kind": "light_switch", "position": {"x": 10, "y": 13}}


def _night(
    at: tuple[int, int], hhmm: str, lit: bool, heard: list[dict[str, Any]] | None = None
) -> dict[str, Any]:
    """A foto do vigia à noite, sozinho na sala (sem o dev e sem o gerente), com o interruptor."""
    view = _view(me="vigia", at=at, hhmm=hhmm, heard=heard, manager_in=False)
    view["entities"] = [
        e for e in view["entities"] if e["kind"] != "avatar" or e["entity_id"] == "vigia"
    ]
    view["entities"].append(
        {
            "entity_id": "vigia",
            "kind": "avatar",
            "position": {"x": at[0], "y": at[1]},
            "attributes": {"papel": "vigia"},
        }
    )
    view["entities"].append({**SWITCH, "attributes": {"acesa": lit}})
    return view


def test_o_vigia_atende_o_pedido_da_luz_e_vai_acender_no_interruptor() -> None:
    guard = staff("vigia")
    assert isinstance(guard, GuardScript)
    asked = [
        {
            "avatar_id": "gerente",
            "listener_id": "vigia",
            "text": "@Vigia pode acender a luz da sala?",
        }
    ]
    reply = guard.decide(_night((11, 14), "22:30", lit=False, heard=asked))
    assert (reply["action"], reply["params"]) == (
        "say",
        {"text": "Já vou acender a luz.", "to": "gerente"},
    )
    going = guard.decide(_night((15, 10), "22:30", lit=False))  # na copa: vai ao interruptor
    assert (going["action"], going["params"]) == ("move", {"near": "interruptor"})
    switching = guard.decide(_night((10, 12), "22:30", lit=False))
    assert switching["action"] == "light_on"
    back = guard.decide(_night((10, 12), "22:30", lit=True))
    assert back["intent"] == "voltar para a cadeira"  # acesa: volta ao posto


def test_o_vigia_so_atende_a_luz_quando_falam_com_ele() -> None:
    guard = staff("vigia")
    assert isinstance(guard, GuardScript)
    other = [{"avatar_id": "gerente", "listener_id": "camps", "text": "Acende a luz, Camps?"}]
    assert guard.decide(_night((11, 14), "22:30", lit=False, heard=other))["action"] == "wait"
    named = [{"avatar_id": "gerente", "text": "Vigia, apaga a luz por favor."}]
    reply = guard.decide(_night((11, 14), "22:30", lit=True, heard=named))
    assert reply["params"]["text"] == "Já vou apagar a luz."
    assert guard.wanted is False


def test_na_ronda_o_vigia_apaga_a_sala_vazia_e_com_gente_deixa_acesa() -> None:
    guard = staff("vigia")
    assert isinstance(guard, GuardScript)
    empty = guard.decide(_night((9, 12), "23:00", lit=True))
    assert (empty["action"], empty["params"]) == ("light_off", {})  # ao lado do interruptor
    guard = staff("vigia")
    assert isinstance(guard, GuardScript)
    busy = _night((9, 12), "23:00", lit=True)
    busy["entities"].append(
        {
            "entity_id": "gerente",
            "kind": "avatar",
            "position": {"x": 5, "y": 6},
            "attributes": {"papel": "gerente"},
        }
    )
    assert guard.decide(busy)["action"] != "light_off"


def test_o_gerente_script_escreve_o_que_venceu_e_devolve_um_de_cada_tres() -> None:
    manager = staff("gerente")
    assert isinstance(manager, ManagerScript)
    manager.greeted, manager.greeted_devs = 1, {"camps"}  # o bom-dia de hoje já foi
    write = manager.decide(_view(me="gerente", at=(3, 2), hhmm="09:31"))
    assert write["action"] == "write_ticket"
    assert write["params"]["title"] == "Ferramenta de busca no código (dia 1)"
    third = [_ticket(3, "entregue", "camps")]
    returned = manager.decide(_view(me="gerente", at=(3, 2), hhmm="09:00", tickets=third))
    assert returned["action"] == "return_ticket"
    first = [_ticket(1, "entregue", "camps")]
    accepted = manager.decide(_view(me="gerente", at=(3, 2), hhmm="09:00", tickets=first))
    assert accepted["action"] == "accept_ticket"


def test_o_gerente_script_da_bom_dia_a_cada_dev_uma_vez_por_dia() -> None:
    """ADR-0093: com dois devs na sala, um bom-dia para cada um, na ordem dos ids, e só uma vez."""
    manager = staff("gerente")
    assert isinstance(manager, ManagerScript)
    view = _view(me="gerente", at=(3, 2), hhmm="09:05")
    kenji = {"entity_id": "kenji", "kind": "avatar", "position": {"x": 4, "y": 8}}
    view["entities"].append({**kenji, "attributes": {"papel": "dev"}})
    said = [manager.decide(view) for _ in range(3)]
    assert [(s["action"], s["params"].get("to")) for s in said[:2]] == [
        ("say", "camps"),
        ("say", "kenji"),
    ]
    assert said[2]["action"] != "say"


def test_o_gerente_script_nao_escreve_no_dia_em_que_o_dev_nao_veio() -> None:
    """No feriado e no fim de semana o dev não vem, e os pedidos ficariam para o dia útil seguinte
    (o soak de 5 dias do M23 caiu no 20/11)."""
    manager = staff("gerente")
    assert isinstance(manager, ManagerScript)
    manager.greeted, manager.greeted_devs = 1, {"camps"}  # o bom-dia de hoje já foi
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


def test_o_dev_convocado_nao_faz_as_pausas_que_ficaram_e_a_pausa_velha_fica_para_outro_dia() -> (
    None
):
    """O primeiro pedido do dev convocado (21/nov): ele chegou à noite e fez as pausas do dia que
    tinham ficado para trás, o videogame com elas, antes de olhar o quadro."""
    dev = _dev()
    assert dev.routine is not None
    plan = dev.routine.plan("camps", 1)
    night = _view(at=(4, 5), hhmm="20:30", copa=True)
    summoned = next(e for e in night["entities"] if e["entity_id"] == "camps")
    summoned["attributes"] = {**summoned["attributes"], "convocado_por": "gerente"}
    stay = dev.decide(night)
    assert not stay["intent"].startswith("rotina: ir"), stay  # nada de pausa: espera o pedido
    # Num dia normal, à noite sem convocação, as pausas do dia já passaram da hora: nenhuma vale.
    late = dev.decide(_view(at=(4, 5), hhmm="20:30", copa=True))
    assert not late["intent"].startswith("rotina: ir"), late
    assert dev.routine.done[1] == set(range(len(plan)))  # e ficam para outro dia


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
