from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QFileDialog, QProgressBar, QLabel, QSlider
)
from PyQt6.QtCore import Qt

from widgets.image_display import ImageDisplay
from logic.image_loader import load_grayscale_image
from logic.province_generator import generate_province_map


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Province Map Generator")
        self.resize(900, 900)

        self.original_image = None   # PIL image (L)
        self.province_image = None   # PIL image (RGB)

        # --- Layout ---
        main_layout = QVBoxLayout(self)
        self.setLayout(main_layout)

        # Image display widget
        self.image_display = ImageDisplay()
        main_layout.addWidget(self.image_display, stretch=1)

        # Controls row: buttons
        controls_row = QHBoxLayout()
        main_layout.addLayout(controls_row)

        self.load_btn = QPushButton("Load Image")
        self.load_btn.clicked.connect(self.on_load_image)
        controls_row.addWidget(self.load_btn)

        self.gen_btn = QPushButton("Generate Provinces")
        self.gen_btn.clicked.connect(self.on_generate_provinces)
        controls_row.addWidget(self.gen_btn)

        self.export_btn = QPushButton("Export Image")
        self.export_btn.clicked.connect(self.on_export_image)
        controls_row.addWidget(self.export_btn)

        # Slider row: province density
        slider_row = QHBoxLayout()
        main_layout.addLayout(slider_row)

        slider_label = QLabel("Province density (points):")
        slider_row.addWidget(slider_label)

        self.density_slider = QSlider(Qt.Orientation.Horizontal)
        self.density_slider.setMinimum(200)
        self.density_slider.setMaximum(10000)
        self.density_slider.setValue(3000)
        self.density_slider.setTickInterval(200)
        self.density_slider.setSingleStep(100)
        slider_row.addWidget(self.density_slider, stretch=1)

        self.density_value_label = QLabel(str(self.density_slider.value()))
        slider_row.addWidget(self.density_value_label)

        self.density_slider.valueChanged.connect(
            lambda v: self.density_value_label.setText(str(v))
        )

        # Progress bar
        self.progress = QProgressBar()
        self.progress.setVisible(False)
        main_layout.addWidget(self.progress)

    # -----------------------
    # Slots / Callbacks
    # -----------------------
    def on_load_image(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Load Image",
            "",
            "Images (*.png *.jpg *.jpeg *.bmp *.gif)",
        )
        if not path:
            return

        try:
            img = load_grayscale_image(path)
        except Exception as e:
            print("Failed to load image:", e)
            return

        self.original_image = img
        self.province_image = None
        self.image_display.show_pil_image(img)

    def on_generate_provinces(self):
        if self.original_image is None:
            return

        num_points = self.density_slider.value()

        # busy indicator
        self.progress.setRange(0, 0)
        self.progress.setVisible(True)
        self.repaint()

        try:
            result = generate_province_map(self.original_image, num_points)
            self.province_image = result
            self.image_display.show_pil_image(result)
        except Exception as e:
            print("Error generating provinces:", e)
        finally:
            self.progress.setVisible(False)

    def on_export_image(self):
        if self.province_image is None:
            return

        path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Province Map",
            "",
            "PNG Files (*.png)",
        )
        if not path:
            return

        try:
            self.province_image.save(path)
        except Exception as e:
            print("Failed to save image:", e)
            return
