"""Pillow-based image handling for product photos.

Images are always re-encoded to a bounded-size JPEG on disk under
``images/items/``; only the relative path is ever stored in the database
(spec section 22). This module has no Qt dependency -- converting the
saved file into a displayable ``QPixmap`` happens in
:mod:`app.ui.widgets.image_view`.
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, UnidentifiedImageError

from app.errors import ValidationError
from app.utils.paths import item_image_relative_path, resolve_image_path

MAX_DIMENSION = 800
JPEG_QUALITY = 85


def save_item_image(source_path: str | Path, item_id: int) -> str:
    """Downscale/convert ``source_path`` and save it as the item's image.

    Returns the relative path to store in ``items.image_path``. Writes to a
    temporary file first and atomically replaces the destination, so a
    failed conversion never leaves a half-written image file behind.
    """
    relative_path = item_image_relative_path(item_id)
    destination = resolve_image_path(relative_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = destination.with_suffix(".tmp.jpg")

    try:
        with Image.open(source_path) as image:
            image = image.convert("RGB")
            image.thumbnail((MAX_DIMENSION, MAX_DIMENSION))
            image.save(tmp_path, "JPEG", quality=JPEG_QUALITY)
    except (OSError, UnidentifiedImageError) as exc:
        tmp_path.unlink(missing_ok=True)
        raise ValidationError("error.image_load_failed") from exc

    tmp_path.replace(destination)
    return relative_path


def delete_item_image(relative_path: str | None) -> None:
    if not relative_path:
        return
    path = resolve_image_path(relative_path)
    if path is not None:
        path.unlink(missing_ok=True)
