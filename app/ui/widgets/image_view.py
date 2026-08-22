"""A QLabel that shows a product image, or a neutral placeholder.

Handles the "missing or corrupted image file" case (spec section 29)
gracefully: a bad path never raises inside the UI, it just falls back to
the placeholder icon.
"""

from __future__ import annotations

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QLabel

from app.utils.paths import resolve_image_path


class ImageView(QLabel):
    def __init__(self, size: int = 120, parent=None):
        super().__init__(parent)
        self._size = QSize(size, size)
        self.setFixedSize(self._size)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setStyleSheet(
            "QLabel { background-color: #f0f0f0; border: 1px solid #cccccc; }"
        )
        self.set_image(None)

    def set_image(self, relative_path: str | None) -> None:
        pixmap = self._load_pixmap(relative_path)
        if pixmap is None:
            self.setText("Sin imagen\n\u0644\u0627 \u062a\u0648\u062c\u062f \u0635\u0648\u0631\u0629")
            self.setPixmap(QPixmap())
        else:
            self.setText("")
            self.setPixmap(pixmap)

    def _load_pixmap(self, relative_path: str | None) -> QPixmap | None:
        if not relative_path:
            return None
        path = resolve_image_path(relative_path)
        if path is None or not path.exists():
            return None
        pixmap = QPixmap(str(path))
        if pixmap.isNull():
            return None
        return pixmap.scaled(
            self._size,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
