#!/usr/bin/env python3
"""Busca automáticamente el Build ID y offset del logo de arranque en una firmware Switch.

Uso:
    python tools/find_logo_offset.py RUTA_FIRMWARE \
        --hactool ./hactool \
        --keys ./prod.keys \
        --logo ./logo.png

El script recorre todos los .nca, identifica el contenido del Title ID
010000000000002d, extrae su ExeFS, descomprime main, busca el logo RGBA
original y muestra el Build ID junto con el offset.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

from PIL import Image

TARGET_TITLE_ID = "010000000000002D"
SKIPPED_CONTENT_TYPES = {
    "Meta",
    "Control",
    "HtmlDocument",
    "LegalInformation",
    "DeltaFragment",
}


def run(command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )


def inspect_nca(hactool: Path, keys: Path, nca: Path) -> tuple[str | None, str | None, str]:
    result = run([
        str(hactool),
        "-t", "nca",
        "-k", str(keys),
        "-i", str(nca),
    ])

    title_ids = re.findall(r"Title ID:\s*([0-9A-Fa-f]{16})", result.stdout)
    content_types = re.findall(r"Content Type:\s*([A-Za-z]+)", result.stdout)

    title_id = title_ids[-1].upper() if title_ids else None
    content_type = content_types[-1] if content_types else None
    return title_id, content_type, result.stdout


def extract_exefs(
    hactool: Path,
    keys: Path,
    nca: Path,
    destination: Path,
) -> bool:
    destination.mkdir(parents=True, exist_ok=True)
    result = run([
        str(hactool),
        "-t", "nca",
        "-k", str(keys),
        "-x", str(nca),
        f"--exefsdir={destination}",
    ])
    return (destination / "main").is_file()


def decompress_main(hactool: Path, main: Path, destination: Path) -> Path | None:
    uncompressed = destination / "main_unc"
    result = run([
        str(hactool),
        "-t", "nso",
        str(main),
        f"--uncompressed={uncompressed}",
    ])
    return uncompressed if uncompressed.is_file() else None


def get_build_id(hactool: Path, nso: Path) -> str | None:
    result = run([
        str(hactool),
        "-t", "nso",
        "-i", str(nso),
    ])
    match = re.search(r"Build Id:\s*([0-9A-Fa-f]{64})", result.stdout)
    return match.group(1).upper() if match else None


def find_offsets(binary: bytes, logo_bytes: bytes) -> dict:
    exact = binary.find(logo_bytes)
    partial: list[int] = []

    if exact == -1:
        fragment = logo_bytes[:4096]
        position = 0
        while True:
            found = binary.find(fragment, position)
            if found == -1:
                break
            partial.append(found)
            position = found + 1

    return {
        "exact_offset": exact if exact != -1 else None,
        "partial_offsets": partial[:20],
    }


def save_found_logo(binary: bytes, offset: int, destination: Path) -> Path:
    size = 308 * 350 * 4
    block = binary[offset:offset + size]
    image = Image.frombytes("RGBA", (308, 350), block)
    destination.parent.mkdir(parents=True, exist_ok=True)
    image.save(destination)
    return destination


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Escanea los NCA de una firmware y obtiene el Build ID y offset del logo."
    )
    parser.add_argument("firmware_dir", help="Carpeta con los archivos .nca y .cnmt")
    parser.add_argument("--hactool", default="hactool", help="Ruta al ejecutable hactool")
    parser.add_argument("--keys", default="prod.keys", help="Ruta al archivo prod.keys")
    parser.add_argument("--logo", default="logo.png", help="Ruta al logo.png original de 308x350")
    parser.add_argument("--output", default="offsets.json", help="Archivo JSON de resultados")
    parser.add_argument(
        "--save-logo",
        action="store_true",
        help="Guarda logo_encontrado.png cuando hay una coincidencia exacta",
    )
    args = parser.parse_args()

    firmware_dir = Path(args.firmware_dir)
    hactool = Path(args.hactool)
    keys = Path(args.keys)
    logo_path = Path(args.logo)
    output_path = Path(args.output)

    if not firmware_dir.is_dir():
        raise SystemExit(f"No existe la carpeta de firmware: {firmware_dir}")
    if not keys.is_file():
        raise SystemExit(f"No existe prod.keys: {keys}")
    if not logo_path.is_file():
        raise SystemExit(f"No existe el logo base: {logo_path}")
    if shutil.which(str(hactool)) is None and not hactool.is_file():
        raise SystemExit(f"No se encontró hactool: {hactool}")

    logo = Image.open(logo_path).convert("RGBA")
    if logo.size != (308, 350):
        raise SystemExit(
            f"El logo base debe medir 308x350; el actual mide {logo.size[0]}x{logo.size[1]}."
        )

    logo_bytes = logo.tobytes()
    nca_files = sorted(firmware_dir.rglob("*.nca"))

    if not nca_files:
        raise SystemExit(f"No se encontraron archivos .nca en: {firmware_dir}")

    results: list[dict] = []
    found: list[dict] = []

    with tempfile.TemporaryDirectory(prefix="switch-logo-") as temporary:
        temp_root = Path(temporary)

        for nca in nca_files:
            title_id, content_type, raw_info = inspect_nca(hactool, keys, nca)
            print(
                f"{nca.name}: "
                f"TitleID={title_id or 'N/D'} | "
                f"Type={content_type or 'N/D'}"
            )

            if title_id != TARGET_TITLE_ID:
                continue
            if content_type in SKIPPED_CONTENT_TYPES:
                continue

            print("  Candidato encontrado. Extrayendo ExeFS...")
            exefs_dir = temp_root / nca.stem / "exefs"

            if not extract_exefs(hactool, keys, nca, exefs_dir):
                print("  No se pudo extraer main.")
                continue

            main = exefs_dir / "main"
            uncompressed = decompress_main(hactool, main, exefs_dir)

            if not uncompressed:
                print("  No se pudo descomprimir main.")
                continue

            build_id = get_build_id(hactool, main)
            binary = uncompressed.read_bytes()
            offsets = find_offsets(binary, logo_bytes)

            result = {
                "nca": str(nca),
                "title_id": title_id,
                "content_type": content_type,
                "build_id": build_id,
                **offsets,
            }
            results.append(result)

            if offsets["exact_offset"] is not None:
                offset = offsets["exact_offset"]
                found.append(result)

                print("  LOGO ENCONTRADO")
                print(f"  Build ID: {build_id}")
                print(f"  Offset:   {offset}")
                print(f"  Entrada JSON:")
                print(
                    json.dumps(
                        {
                            "version": "23.0.1",
                            "build_id": build_id,
                            "offset": offset,
                        },
                        indent=2,
                    )
                )

                if args.save_logo:
                    saved = save_found_logo(
                        binary,
                        offset,
                        Path("logo_encontrado.png"),
                    )
                    print(f"  Logo extraído: {saved}")

            elif offsets["partial_offsets"]:
                print(
                    "  No hay coincidencia exacta. "
                    f"Coincidencias parciales: {offsets['partial_offsets']}"
                )
                print(
                    "  Esto puede indicar que el logo cambió en esta firmware."
                )
            else:
                print("  No se encontró el logo original en este módulo.")

    output_path.write_text(
        json.dumps(results, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    print(f"\nResultados completos guardados en: {output_path}")

    if found:
        print("\nEntrada lista para data/firmwares.json:")
        print(
            json.dumps(
                {
                    "version": "23.0.1",
                    "build_id": found[0]["build_id"],
                    "offset": found[0]["exact_offset"],
                },
                indent=2,
            )
        )
    else:
        print("\nNo se encontró una coincidencia exacta del logo original.")


if __name__ == "__main__":
    main()
