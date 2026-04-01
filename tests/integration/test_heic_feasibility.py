# Responsibility: Verify HEIC can be opened and exported to PNG on the host (pillow-heif + Pillow).

from __future__ import annotations

from pathlib import Path

from PIL import Image


def test_heic_reads_and_exports_png(heic_sample_path: Path) -> None:
    from pillow_heif import register_heif_opener

    register_heif_opener()

    loaded_image = Image.open(heic_sample_path)
    loaded_image.load()

    assert loaded_image.size == (64, 64)

    output_png = heic_sample_path.parent / "out.png"
    loaded_image.save(output_png, format="PNG")

    reloaded = Image.open(output_png)
    reloaded.load()
    assert reloaded.format == "PNG"
    assert reloaded.size == (64, 64)
