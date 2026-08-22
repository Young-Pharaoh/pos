"""Operator text scale: preset sizes for the whole UI.

Three presets map to fixed scale factors applied through the application
font and a small set of derived pixel sizes for widgets that use explicit
stylesheets today. Product photo thumbnails stay at their fixed size.
"""

from __future__ import annotations

from PySide6.QtWidgets import QApplication

TEXT_SCALE_NORMAL = "normal"
TEXT_SCALE_LARGE = "large"
TEXT_SCALE_EXTRA_LARGE = "extra_large"

TEXT_SCALE_PRESETS = (TEXT_SCALE_NORMAL, TEXT_SCALE_LARGE, TEXT_SCALE_EXTRA_LARGE)
DEFAULT_TEXT_SCALE = TEXT_SCALE_NORMAL

SCALE_FACTORS = {
    TEXT_SCALE_NORMAL: 1.0,
    TEXT_SCALE_LARGE: 1.2,
    TEXT_SCALE_EXTRA_LARGE: 1.4,
}

BASE_APP_FONT_POINT_SIZE = 10.0
BASE_WINDOW_WIDTH = 1150
BASE_WINDOW_HEIGHT = 740


def normalize_text_scale(value: str | None) -> str:
    if value in SCALE_FACTORS:
        return value
    return DEFAULT_TEXT_SCALE


def scale_factor(preset: str) -> float:
    return SCALE_FACTORS[normalize_text_scale(preset)]


def scaled_px(base: int, preset: str) -> int:
    return max(1, round(base * scale_factor(preset)))


def app_title_stylesheet(preset: str) -> str:
    return f"font-size: {scaled_px(22, preset)}px; font-weight: 700;"


def page_title_stylesheet(preset: str) -> str:
    return f"font-size: {scaled_px(20, preset)}px; font-weight: 600;"


def total_label_stylesheet(preset: str) -> str:
    return f"font-size: {scaled_px(18, preset)}px; font-weight: 700;"


def muted_label_stylesheet() -> str:
    return "color: #555555;"


def hint_label_stylesheet() -> str:
    return "color: #777777; font-style: italic;"


def stat_card_title_stylesheet(preset: str) -> str:
    return f"color: #555555; font-size: {scaled_px(12, preset)}px;"


def stat_card_value_stylesheet(preset: str) -> str:
    return f"font-size: {scaled_px(22, preset)}px; font-weight: 600;"


def nav_button_min_height(preset: str) -> int:
    return scaled_px(48, preset)


def complete_sale_button_min_height(preset: str) -> int:
    return scaled_px(44, preset)


def action_button_min_height(preset: str) -> int:
    return scaled_px(36, preset)


def table_row_height(preset: str) -> int:
    return scaled_px(28, preset)


def window_size_for_preset(preset: str) -> tuple[int, int]:
    factor = scale_factor(preset)
    return (
        round(BASE_WINDOW_WIDTH * factor),
        round(BASE_WINDOW_HEIGHT * factor),
    )


def apply_to_application(app: QApplication, preset: str) -> None:
    font = app.font()
    font.setPointSizeF(BASE_APP_FONT_POINT_SIZE * scale_factor(preset))
    app.setFont(font)


def apply_table_row_height(table, preset: str) -> None:
    row_height = table_row_height(preset)
    table.verticalHeader().setDefaultSectionSize(row_height)
    for row in range(table.rowCount()):
        table.setRowHeight(row, row_height)
