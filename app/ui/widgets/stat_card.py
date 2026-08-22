"""Small read-only "figure + label" card used on the dashboard."""

from __future__ import annotations

from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout


class StatCard(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setMinimumWidth(180)
        self.setStyleSheet(
            "QFrame { background-color: #ffffff; border: 1px solid #dddddd;"
            " border-radius: 8px; padding: 4px; }"
        )
        layout = QVBoxLayout(self)
        self.title_label = QLabel()
        self.title_label.setStyleSheet("color: #555555; font-size: 12px;")
        self.value_label = QLabel()
        self.value_label.setStyleSheet("font-size: 22px; font-weight: 600;")
        layout.addWidget(self.title_label)
        layout.addWidget(self.value_label)

    def set_title(self, text: str) -> None:
        self.title_label.setText(text)

    def set_value(self, text: str) -> None:
        self.value_label.setText(text)
