import config
from PyQt6.QtWidgets import QLabel, QToolTip
from PyQt6.QtGui import QPixmap, QImage, QMouseEvent
from PyQt6.QtCore import Qt, QPoint


class ImageDisplay(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(config.DISPLAY_SIZE_WIDTH,
                            config.DISPLAY_SIZE_HEIGHT)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setStyleSheet("background-color: #333")
        self.setMouseTracking(True)

        self._image = None
        self._index_map = None
        self._metadata = None
        self._pixmap_scale = 1.0
        self._pixmap_offset = QPoint(0, 0)
        
    def set_interactive_data(self, index_map, metadata):
        self._index_map = index_map
        self._metadata = metadata

    def set_image(self, image):
        self._image = image
        # Ensure image is RGBA for QImage
        if image.mode != "RGBA":
            # Handle P, L, RGB, etc.
            display_img = image.convert("RGBA")
        else:
            display_img = image
            
        qimage = QImage(
            display_img.tobytes("raw", "RGBA"),
            display_img.width,
            display_img.height,
            QImage.Format.Format_RGBA8888
        )
        pixmap = QPixmap.fromImage(qimage)
        pixmap = pixmap.scaled(
            self.size(),
            Qt.AspectRatioMode.KeepAspectRatio)

        self.setPixmap(pixmap)
        
        # Calculate scaling and offset for mouse mapping
        if self._image.width > 0 and self._image.height > 0:
             scale_w = pixmap.width() / self._image.width
             scale_h = pixmap.height() / self._image.height
             # Maintain aspect ratio means we use the min scale? 
             # QImage scaled with KeepAspectRatio uses same scale for both dims.
             self._pixmap_scale = scale_w # or scale_h, should be same
             
             # The pixmap is centered in the label.
             # Calculate offset
             x_off = (self.width() - pixmap.width()) / 2
             y_off = (self.height() - pixmap.height()) / 2
             self._pixmap_offset = QPoint(int(x_off), int(y_off))

    def mouseMoveEvent(self, ev: QMouseEvent):
        if self._index_map is None or self._metadata is None:
            super().mouseMoveEvent(ev)
            return

        pos = ev.pos()
        # Transform local pos to image pos
        x = pos.x() - self._pixmap_offset.x()
        y = pos.y() - self._pixmap_offset.y()
        
        if self._pixmap_scale > 0:
            img_x = int(x / self._pixmap_scale)
            img_y = int(y / self._pixmap_scale)
            
            h, w = self._index_map.shape
            
            if 0 <= img_x < w and 0 <= img_y < h:
                idx = self._index_map[img_y, img_x]
                if idx >= 0 and idx < len(self._metadata):
                    data = self._metadata[idx]
                    biome_name = data.get("Biome_Name", "Unknown")
                    ptype = data.get("province_type", "Unknown")
                    
                    text = f"Biome: {biome_name}\nType: {ptype}\nID: {data['province_id']}"
                    QToolTip.showText(ev.globalPosition().toPoint(), text, self)
                    return
        
        QToolTip.hideText()
        super().mouseMoveEvent(ev)
        
    def resizeEvent(self, event):
        if self._image:
             self.set_image(self._image)
        super().resizeEvent(event)

    def get_image(self):
        return self._image
