from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from .images import LogoImage
from .ips import build_patch, rebase_patch, serialize_records


class FirmwareError(ValueError):
    pass


@dataclass(frozen=True)
class FirmwareTarget:
    version: str
    build_id: str
    offset: int

    @property
    def filename(self) -> str:
        return f"{self.build_id}.ips"


def load_targets(path: str | Path) -> list[FirmwareTarget]:
    file_path = Path(path)
    if not file_path.is_file():
        raise FirmwareError("No se encontró el catálogo de firmwares.")

    try:
        raw = json.loads(file_path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise FirmwareError("El catálogo de firmwares no es un JSON válido.") from exc

    targets: list[FirmwareTarget] = []
    for item in raw:
        try:
            target = FirmwareTarget(
                version=str(item["version"]),
                build_id=str(item["build_id"]).upper(),
                offset=int(item["offset"]),
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise FirmwareError(f"Entrada de firmware inválida: {item}") from exc

        if len(target.build_id) != 64 or not all(
            character in "0123456789ABCDEF" for character in target.build_id
        ):
            raise FirmwareError(f"Build ID inválido para {target.version}.")
        if target.offset < 0:
            raise FirmwareError(f"Offset inválido para {target.version}.")
        targets.append(target)

    if not targets:
        raise FirmwareError("El catálogo de firmwares está vacío.")
    return targets


def generate_patch(
    base_logo: LogoImage,
    custom_logo: LogoImage,
    target: FirmwareTarget,
) -> bytes:
    base_records = build_patch(base_logo.raw, custom_logo.raw)
    rebased = rebase_patch(base_records, target.offset)
    return serialize_records(rebased)
