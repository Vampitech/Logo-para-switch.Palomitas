from __future__ import annotations

from pathlib import Path

from .firmware import FirmwareTarget, generate_patch
from .images import LogoImage

PATCH_SUBPATH = Path("atmosphere") / "exefs_patches" / "logo"


def export_patches(
    output_dir: str | Path,
    base_logo: LogoImage,
    custom_logo: LogoImage,
    targets: list[FirmwareTarget],
) -> list[Path]:
    root = Path(output_dir)
    destination = root / PATCH_SUBPATH
    destination.mkdir(parents=True, exist_ok=True)

    written: list[Path] = []
    for target in targets:
        patch = generate_patch(base_logo, custom_logo, target)
        patch_path = destination / target.filename
        patch_path.write_bytes(patch)
        written.append(patch_path)

    if not written:
        raise RuntimeError("No se generó ningún parche.")
    return written
