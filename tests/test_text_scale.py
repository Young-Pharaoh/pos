"""Tests for operator text scale: settings persistence and scale helpers."""

from __future__ import annotations

from PySide6.QtWidgets import QApplication

from app.services.settings_service import TEXT_SCALE_KEY, SettingsService
from app.text_scale import (
    DEFAULT_TEXT_SCALE,
    TEXT_SCALE_EXTRA_LARGE,
    TEXT_SCALE_LARGE,
    TEXT_SCALE_NORMAL,
    apply_to_application,
    normalize_text_scale,
    scaled_px,
    scale_factor,
    window_size_for_preset,
)


def test_settings_default_text_scale_is_normal(settings_service: SettingsService):
    assert settings_service.get_all().text_scale == TEXT_SCALE_NORMAL


def test_settings_persist_text_scale(settings_service: SettingsService):
    settings_service.set(TEXT_SCALE_KEY, TEXT_SCALE_LARGE)
    assert settings_service.get_all().text_scale == TEXT_SCALE_LARGE


def test_normalize_text_scale_rejects_unknown_values():
    assert normalize_text_scale(None) == DEFAULT_TEXT_SCALE
    assert normalize_text_scale("huge") == DEFAULT_TEXT_SCALE
    assert normalize_text_scale(TEXT_SCALE_EXTRA_LARGE) == TEXT_SCALE_EXTRA_LARGE


def test_scale_factor_matches_spec_ratios():
    assert scale_factor(TEXT_SCALE_NORMAL) == 1.0
    assert scale_factor(TEXT_SCALE_LARGE) == 1.2
    assert scale_factor(TEXT_SCALE_EXTRA_LARGE) == 1.4


def test_scaled_px_rounds_from_baseline():
    assert scaled_px(20, TEXT_SCALE_NORMAL) == 20
    assert scaled_px(20, TEXT_SCALE_LARGE) == 24
    assert scaled_px(20, TEXT_SCALE_EXTRA_LARGE) == 28


def test_window_size_grows_with_preset():
    normal = window_size_for_preset(TEXT_SCALE_NORMAL)
    extra_large = window_size_for_preset(TEXT_SCALE_EXTRA_LARGE)
    assert extra_large[0] > normal[0]
    assert extra_large[1] > normal[1]


def test_apply_to_application_increases_font_point_size(qtbot):
    app = QApplication.instance()
    assert app is not None

    apply_to_application(app, TEXT_SCALE_NORMAL)
    normal_size = app.font().pointSizeF()

    apply_to_application(app, TEXT_SCALE_EXTRA_LARGE)
    assert app.font().pointSizeF() > normal_size
