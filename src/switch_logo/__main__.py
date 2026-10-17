from pathlib import Path

from PySide6.QtWidgets import QApplication

from .ui.main_window import MainWindow


def main() -> int:
    app = QApplication([])
    app.setApplicationName("Logo para Switch — Palomitas")
    window = MainWindow(Path(__file__).resolve().parents[2])
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
