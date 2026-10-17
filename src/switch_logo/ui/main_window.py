from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from ..core.export import export_patches
from ..core.firmware import FirmwareError, load_targets
from ..core.images import ImageError, load_logo


class MainWindow(QMainWindow):
    def __init__(self, project_root: Path) -> None:
        super().__init__()
        self.project_root = project_root
        self.catalog_path = project_root / "data" / "firmwares.json"
        self.base_logo_path = project_root / "logo.png"
        self.selected_image: Path | None = None
        self.targets = load_targets(self.catalog_path)

        self.setWindowTitle("Logo para Switch — Palomitas")
        self.setMinimumSize(640, 480)
        self.setStyleSheet(
            """
            QMainWindow { background: #10141c; color: #e8edf5; }
            QLabel { color: #e8edf5; }
            QPushButton {
                background: #2f81f7; color: white; border: none;
                border-radius: 8px; padding: 10px 16px; font-weight: 600;
            }
            QPushButton:hover { background: #4c8dff; }
            QPushButton:disabled { background: #3a4353; color: #9aa4b2; }
            QComboBox {
                background: #1b2230; color: #e8edf5; border: 1px solid #303b4d;
                border-radius: 8px; padding: 8px;
            }
            QLabel#preview {
                background: #000000; border: 1px solid #303b4d;
                border-radius: 10px;
            }
            """
        )

        central = QWidget()
        layout = QVBoxLayout(central)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        title = QLabel("Personaliza el logo de arranque")
        title.setStyleSheet("font-size: 22px; font-weight: 700;")
        subtitle = QLabel(
            "Selecciona un PNG de 308 x 350 píxeles y genera los parches IPS para Atmosphère."
        )
        subtitle.setStyleSheet("color: #9aa4b2;")
        layout.addWidget(title)
        layout.addWidget(subtitle)

        self.preview = QLabel("Sin imagen")
        self.preview.setObjectName("preview")
        self.preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview.setFixedSize(240, 280)
        layout.addWidget(self.preview, alignment=Qt.AlignmentFlag.AlignHCenter)

        form = QFormLayout()
        self.firmware_box = QComboBox()
        self.firmware_box.addItem("Todos")
        for target in self.targets:
            self.firmware_box.addItem(target.version)
        form.addRow("Firmware:", self.firmware_box)

        self.output_label = QLabel("Sin carpeta seleccionada")
        self.output_label.setStyleSheet("color: #9aa4b2;")
        output_button = QPushButton("Elegir carpeta de salida")
        output_button.clicked.connect(self.choose_output)
        form.addRow("Destino:", self.output_label)
        form.addRow("", output_button)
        layout.addLayout(form)

        buttons = QHBoxLayout()
        select_button = QPushButton("Seleccionar PNG")
        select_button.clicked.connect(self.choose_image)
        self.generate_button = QPushButton("Generar parches")
        self.generate_button.setEnabled(False)
        self.generate_button.clicked.connect(self.generate)
        buttons.addWidget(select_button)
        buttons.addWidget(self.generate_button)
        layout.addLayout(buttons)

        self.status = QLabel("Listo.")
        self.status.setStyleSheet("color: #9aa4b2;")
        layout.addWidget(self.status)

        self.setCentralWidget(central)
        self.output_dir: Path | None = None

    def choose_image(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Seleccionar logo", "", "Imágenes PNG (*.png)"
        )
        if not path:
            return
        try:
            logo = load_logo(path)
        except ImageError as exc:
            QMessageBox.critical(self, "Imagen inválida", str(exc))
            return

        self.selected_image = Path(path)
        image = QImage(str(self.selected_image))
        self.preview.setPixmap(
            QPixmap.fromImage(image).scaled(
                220,
                260,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
        )
        self.generate_button.setEnabled(self.output_dir is not None)
        self.status.setText(f"Imagen cargada: {self.selected_image.name}")

    def choose_output(self) -> None:
        path = QFileDialog.getExistingDirectory(self, "Seleccionar carpeta de salida")
        if not path:
            return
        self.output_dir = Path(path)
        self.output_label.setText(str(self.output_dir))
        self.generate_button.setEnabled(self.selected_image is not None)

    def generate(self) -> None:
        if not self.selected_image or not self.output_dir:
            return

        selection = self.firmware_box.currentText()
        targets = self.targets if selection == "Todos" else [
            target for target in self.targets if target.version == selection
        ]

        try:
            self.status.setText("Generando parches...")
            base = load_logo(self.base_logo_path)
            custom = load_logo(self.selected_image)
            files = export_patches(self.output_dir, base, custom, targets)
        except (FirmwareError, ImageError, OSError, ValueError) as exc:
            QMessageBox.critical(self, "Error", str(exc))
            self.status.setText("Error al generar los parches.")
            return

        self.status.setText(
            f"Se generaron {len(files)} parche(s) en {self.output_dir / 'atmosphere'}."
        )
        QMessageBox.information(
            self,
            "Proceso completado",
            "Parches generados correctamente. Copia la carpeta atmosphere a la raíz de tu tarjeta SD.",
        )
