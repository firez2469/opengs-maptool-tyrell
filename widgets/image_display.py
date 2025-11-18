from PyQt6.QtWidgets import QLabel
from PyQt6.QtGui import QPixmap, QImage
from PyQt6.QtCore import Qt
from PIL import Image


class ImageDisplay(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setStyleSheet("background-color: #333; border: 1px solid #666;")
        self.setMinimumSize(400, 400)

    def show_pil_image(self, img: Image.Image):
        """Display a PIL image (L or RGB) scaled to fit the label."""
        if img is None:
            self.clear()
            return

        img = img.copy()
        w, h = img.size

        if img.mode == "L":
            fmt = QImage.Format.Format_Grayscale8
            data = img.tobytes()
            bytes_per_line = w
        else:
            if img.mode != "RGB":
                img = img.convert("RGB")
                w, h = img.size
            fmt = QImage.Format.Format_RGB888
            data = img.tobytes()
            bytes_per_line = 3 * w

        qimage = QImage(data, w, h, bytes_per_line, fmt)
        pixmap = QPixmap.fromImage(qimage)

        scaled = pixmap.scaled(
            self.width(),
            self.height(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        self.setPixmap(scaled)

    def resizeEvent(self, event):
        # Rescale current pixmap on resize
        if self.pixmap() is not None:
            pix = self.pixmap()
            scaled = pix.scaled(
                self.width(),
                self.height(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            self.setPixmap(scaled)
        super().resizeEvent(event)
