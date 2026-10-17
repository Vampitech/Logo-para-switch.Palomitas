from dataclasses import dataclass
from pathlib import Path

from PIL import Image

LOGO_SIZE = (308, 350)


class ImageError(ValueError):
    pass


@dataclass(frozen=True)
class LogoImage:
    path: Path
    image: Image.Image

    @property
    def raw(self) -> bytes:
        return self.image.tobytes()


def load_logo(path: str | Path) -> LogoImage:
    file_path = Path(path)
    if not file_path.is_file():
        raise ImageError("Selecciona un archivo PNG válido.")

    try:
        image = Image.open(file_path)
        image.load()
    except Exception as exc:
        raise ImageError("No se pudo abrir la imagen.") from exc

    if image.size != LOGO_SIZE:
        raise ImageError(
            f"La imagen debe medir {LOGO_SIZE[0]}x{LOGO_SIZE[1]} píxeles; "
            f"la seleccionada mide {image.size[0]}x{image.size[1]}."
        )

    return LogoImage(path=file_path, image=image.convert("RGBA"))
