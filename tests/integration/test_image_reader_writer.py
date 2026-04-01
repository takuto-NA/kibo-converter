# Responsibility: Integration tests for image open, EXIF handling, resize, and encode helpers.

from __future__ import annotations

from pathlib import Path

from PIL import Image

from kibo_converter.domain.processing_steps import ImageOutputFormat
from kibo_converter.infrastructure.image_reader_writer import (
    apply_exif_orientation,
    encode_image_to_bytes,
    open_image,
    resize_to_max_edge,
    save_image_to_path,
    write_encoded_image_bytes_to_path,
)


def test_png_save_and_reopen_dimensions(tmp_path: Path) -> None:
    source_path = tmp_path / "source.png"
    image = Image.new("RGB", (100, 50), color=(10, 20, 30))
    image.save(source_path, format="PNG")

    loaded = open_image(source_path)
    loaded = apply_exif_orientation(loaded)
    assert loaded.size == (100, 50)

    target_path = tmp_path / "out.png"
    save_image_to_path(loaded, target_path, ImageOutputFormat.PNG)

    reloaded = Image.open(target_path)
    reloaded.load()
    assert reloaded.size == (100, 50)


def test_resize_to_max_edge_scales_longer_edge(tmp_path: Path) -> None:
    image = Image.new("RGB", (200, 100), color=(1, 2, 3))
    resized = resize_to_max_edge(image, max_edge_pixels=100)
    assert resized.size[0] == 100
    assert resized.size[1] == 50


def test_encode_image_to_bytes_is_deterministic_for_png(tmp_path: Path) -> None:
    image = Image.new("RGB", (10, 10), color=(5, 6, 7))
    first = encode_image_to_bytes(image, ImageOutputFormat.PNG)
    second = encode_image_to_bytes(image, ImageOutputFormat.PNG)
    assert first == second


def test_write_encoded_image_bytes_to_path_preserves_encoded_bytes(tmp_path: Path) -> None:
    image = Image.new("RGB", (12, 12), color=(25, 50, 75))
    encoded_bytes = encode_image_to_bytes(image, ImageOutputFormat.WEBP)
    target_path = tmp_path / "out.webp"

    write_encoded_image_bytes_to_path(target_path, encoded_bytes)

    assert target_path.read_bytes() == encoded_bytes
