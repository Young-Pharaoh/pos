"""Small read-only "figure + label" card used on the dashboard."""

from __future__ import annotations

from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout

from app.text_scale import stat_card_title_stylesheet, stat_card_value_stylesheet


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
        self.value_label = QLabel()
        layout.addWidget(self.title_label)
        layout.addWidget(self.value_label)

    def apply_text_scale(self, preset: str) -> None:
        self.title_label.setStyleSheet(stat_card_title_stylesheet(preset))
        self.value_label.setStyleSheet(stat_card_value_stylesheet(preset))

    def set_title(self, text: str) -> None:
        self.title_label.setText(text)

    def set_value(self, text: str) -> None:
        self.value_label.setText(text)
