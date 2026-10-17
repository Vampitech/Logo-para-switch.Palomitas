# Logo para Switch — Palomitas

Generador de parches IPS para reemplazar el logo de Nintendo Switch mostrado al iniciar **Atmosphère** en consolas modificadas.

Esta es una modernización del proyecto original de **D3fau4 y Kronos2308**. Conserva la misma función central, pero incorpora una interfaz PySide6, una estructura modular, validaciones más estrictas y exportación a una carpeta elegida por el usuario.

## Requisitos

- Python 3.10 o superior
- Una imagen PNG de **308 x 350 píxeles**, preferiblemente RGBA
- Atmosphère compatible con la versión de firmware seleccionada

## Instalación

```bash
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
.venv\Scripts\activate     # Windows

pip install -e .[dev]
```

## Uso

```bash
python -m switch_logo
```

1. Selecciona tu PNG personalizado.
2. Verifica la vista previa.
3. Elige el firmware o **Todos**.
4. Selecciona la carpeta de salida.
5. Pulsa **Generar parches**.

La aplicación creará:

```text
<carpeta-elegida>/atmosphere/exefs_patches/logo/<build-id>.ips
```

Copia la carpeta `atmosphere` generada a la raíz de la tarjeta SD, respetando la estructura existente.

## Compatibilidad

El catálogo incluye las versiones presentes en el proyecto original, desde 1.x.x hasta 22.x.x.

La compatibilidad con **23.0.x** está marcada como pendiente: requiere confirmar el Build ID y el offset reales antes de habilitarla. Añadir una entrada sin esos datos verificados puede producir un parche inválido.

Para añadir una versión confirmada, edita `data/firmwares.json`:

```json
{
  "version": "23.0.x",
  "build_id": "BUILD_ID_EN_MAYUSCULAS",
  "offset": 1234567
}
```

## Desarrollo

```bash
pytest
```

## Créditos y licencia

Proyecto original por **D3fau4** y **Kronos2308**. Esta modernización mantiene la licencia **GPL-3.0-or-later**.
