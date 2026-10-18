"""Configuração do ambiente (`config/env/*.yaml`) e dos mundos (`config/worlds/*.yaml`).

Só as raízes de composição (main.py) e os testes leem estes arquivos; os serviços recebem valores.
"""

import re
from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Literal, cast

import yaml

from campsverso_adapters.bus_nats import StreamSpec
from campsverso_adapters.model_metered import ModelPrices

_DURATION = re.compile(r"^(\d+)([smhd])$")
_SIZE = re.compile(r"^(\d+)(B|KiB|MiB|GiB|TiB)$")
_SECONDS = {"s": 1, "m": 60, "h": 3600, "d": 86400}
_BYTES = {"B": 1, "KiB": 1 << 10, "MiB": 1 << 20, "GiB": 1 << 30, "TiB": 1 << 40}


def duration_seconds(value: str) -> int:
    match = _DURATION.match(value)
    if match is None:
        raise ValueError(f"duração inválida: {value!r} (use 30d, 12h, 90m ou 45s)")
    return int(match[1]) * _SECONDS[match[2]]


def size_bytes(value: str) -> int:
    match = _SIZE.match(value)
    if match is None:
        raise ValueError(f"tamanho inválido: {value!r} (use 512MiB, 1GiB...)")
    return int(match[1]) * _BYTES[match[2]]


@dataclass(frozen=True, slots=True)
class NatsSettings:
    url: str
    duplicate_window_seconds: int
    streams: tuple[StreamSpec, ...]


@dataclass(frozen=True, slots=True)
class GatewaySettings:
    host: str = "127.0.0.1"  # só local na v0.1, sem login (ADR-0050)
    port: int = 8765
    maps: dict[str, Path] = field(default_factory=dict[str, Path])  # id do mapa -> arquivo Tiled
    ui_dir: Path | None = None  # UI compilada; sem ela, a UI roda pelo Vite (make ui)
    art: tuple[tuple[str, Path], ...] = ()  # camadas de arte, do gênero ao cenário (ADR-0053)


@dataclass(frozen=True, slots=True)
class PerceptionSettings:
    deltas_for: tuple[str, ...] = ("llm",)  # tipos de controlador que recebem deltas (ADR-0056)
    snapshot_every: int = 20  # uma foto a cada N deltas


@dataclass(frozen=True, slots=True)
class EnvSettings:
    data_dir: Path
    archive_dir: Path
    validate_events: bool
    nats: NatsSettings
    snapshot_every_ticks: int
    snapshot_keep_full: int
    archive_compress_after_days: int
    gateway: GatewaySettings = field(default_factory=GatewaySettings)
    pulse_seconds: float = 1.0  # pulso do kernel (ADR-0051); 0 desliga
    perception: PerceptionSettings = field(default_factory=PerceptionSettings)
    models: Mapping[str, ModelPrices] = field(default_factory=dict[str, ModelPrices])  # ADR-0058


type ClockMode = Literal["continuous", "max"]


@dataclass(frozen=True, slots=True)
class WorldSettings:
    worldid: str
    cartridge: str
    seed: int
    start: datetime
    mode: ClockMode
    scale: float | None  # None: a escala padrão do cartucho
    paused: bool
    rules_file: Path | None  # None: o arquivo de regras do cartucho
    controllers: dict[str, tuple[str, str]]  # avatar -> (tipo, id) no começo; vazio: o do cartucho


def _read(path: Path) -> Mapping[str, Any]:
    return cast(Mapping[str, Any], yaml.safe_load(path.read_text(encoding="utf-8")))


def load_env(path: Path, root: Path | None = None) -> EnvSettings:
    """Caminhos relativos valem a partir de `root` (padrão: o diretório atual)."""
    doc = _read(path)
    base = root or Path.cwd()
    nats = cast(Mapping[str, Any], doc["nats"])
    streams = cast(Mapping[str, Mapping[str, Any]], nats["streams"])
    snapshots = cast(Mapping[str, Any], doc["snapshots"])
    archive = cast(Mapping[str, Any], doc["archive"])
    gateway = cast(Mapping[str, Any], doc.get("gateway") or {})
    kernel = cast(Mapping[str, Any], doc.get("kernel") or {})
    perception = cast(Mapping[str, Any], doc.get("perception") or {})
    models = cast(Mapping[str, Mapping[str, Any]], doc.get("models") or {})
    maps = cast(Mapping[str, str], gateway.get("maps") or {})
    art = cast(list[Mapping[str, str]], gateway.get("art") or [])
    return EnvSettings(
        data_dir=base / str(doc["data_dir"]),
        archive_dir=base / str(archive["dir"]),
        validate_events=bool(doc.get("validate_events", True)),
        nats=NatsSettings(
            url=str(nats["url"]),
            duplicate_window_seconds=duration_seconds(str(nats["duplicate_window"])),
            streams=tuple(
                StreamSpec(
                    name=name,
                    subjects=tuple(str(s) for s in spec["subjects"]),
                    max_age_seconds=duration_seconds(str(spec["max_age"])),
                    max_bytes=size_bytes(str(spec["max_bytes"])),
                )
                for name, spec in streams.items()
            ),
        ),
        snapshot_every_ticks=int(snapshots["full_every_ticks"]),
        snapshot_keep_full=int(snapshots["keep_full"]),
        archive_compress_after_days=int(archive["compress_after_days"]),
        gateway=GatewaySettings(
            host=str(gateway.get("host", "127.0.0.1")),
            port=int(gateway.get("port", 8765)),
            maps={str(k): base / str(v) for k, v in maps.items()},
            ui_dir=base / str(gateway["ui_dir"]) if gateway.get("ui_dir") else None,
            art=tuple((str(layer["name"]), base / str(layer["dir"])) for layer in art),
        ),
        pulse_seconds=float(kernel.get("pulse_seconds", 1.0)),
        perception=PerceptionSettings(
            deltas_for=tuple(str(t) for t in perception.get("deltas_for", ["llm"])),
            snapshot_every=int(perception.get("snapshot_every", 20)),
        ),
        models={
            str(name): ModelPrices(
                input_per_mtok=float(p["input_per_mtok"]),
                output_per_mtok=float(p["output_per_mtok"]),
                cache_read_per_mtok=float(p["cache_read_per_mtok"]),
                cache_write_per_mtok=float(p["cache_write_per_mtok"]),
            )
            for name, p in models.items()
        },
    )


def load_world(path: Path, root: Path | None = None) -> WorldSettings:
    doc = _read(path)
    clock = cast(Mapping[str, Any], doc.get("clock") or {})
    rules = doc.get("rules_file")
    mode = clock.get("mode", "continuous")
    if mode not in ("continuous", "max"):
        raise ValueError(f"modo de relógio inválido: {mode!r}")
    start = datetime.fromisoformat(str(doc["start"]))
    if start.tzinfo is None:
        raise ValueError("start precisa de fuso horário (ex.: 2026-10-10T06:00:00-03:00)")
    return WorldSettings(
        worldid=str(doc["worldid"]),
        cartridge=str(doc["cartridge"]),
        seed=int(doc["seed"]),
        start=start,
        mode=mode,
        scale=None if clock.get("scale") is None else float(clock["scale"]),
        paused=bool(clock.get("paused", False)),
        rules_file=None if rules is None else (root or Path.cwd()) / str(rules),
        controllers={
            str(avatar): (str(ref["type"]), str(ref["id"]))
            for avatar, ref in cast(
                Mapping[str, Mapping[str, Any]], doc.get("controllers") or {}
            ).items()
        },
    )
