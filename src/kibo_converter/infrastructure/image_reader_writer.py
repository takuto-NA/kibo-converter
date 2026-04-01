# Responsibility: Register HEIF support and perform image open, transform, and save operations.

from __future__ import annotations

from io import BytesIO
from pathlib import Path

from PIL import Image, ImageOps

from kibo_converter.domain.processing_steps import ImageOutputFormat


class HeifSupportInitializationError(Exception):
    """Raised when pillow-heif cannot be registered for HEIC/HEIF input."""


_heif_registration_attempted = False
_heif_registration_succeeded = False


def ensure_heif_support_registered() -> None:
    """Register HEIF opener once; raises when registration fails."""
    global _heif_registration_attempted, _heif_registration_succeeded
    if _heif_registration_succeeded:
        return
    if _heif_registration_attempted and not _heif_registration_succeeded:
        raise HeifSupportInitializationError("HEIF support registration already failed.")

    _heif_registration_attempted = True
    try:
        from pillow_heif import register_heif_opener

        register_heif_opener()
    except Exception as exc:
        raise HeifSupportInitializationError("Failed to register HEIF/HEIC support.") from exc

    _heif_registration_succeeded = True


def open_image(source_path: Path) -> Image.Image:
    """Open an image file including HEIC when HEIF support is available."""
    suffix_lower = source_path.suffix.lower()
    heic_like_suffixes = {".heic", ".heif"}
    if suffix_lower in heic_like_suffixes:
        ensure_heif_support_registered()

    image = Image.open(source_path)
    image.load()
    return image


def apply_exif_orientation(image: Image.Image) -> Image.Image:
    """Apply EXIF orientation so pixel data matches intended display orientation."""
    return ImageOps.exif_transpose(image)


def resize_to_max_edge(image: Image.Image, max_edge_pixels: int) -> Image.Image:
    """Resize so the longer edge equals max_edge_pixels when larger than max."""
    width, height = image.size
    longer_edge = max(width, height)
    if longer_edge <= max_edge_pixels:
        return image

    if width >= height:
        new_width = max_edge_pixels
        new_height = max(1, int(round(height * (max_edge_pixels / width))))
        return image.resize((new_width, new_height), Image.Resampling.LANCZOS)

    new_height = max_edge_pixels
    new_width = max(1, int(round(width * (max_edge_pixels / height))))
    return image.resize((new_width, new_height), Image.Resampling.LANCZOS)


def encode_image_to_bytes(image: Image.Image, output_format: ImageOutputFormat) -> bytes:
    """Encode image to bytes for hashing and collision checks."""
    buffer = BytesIO()
    pil_format = _pil_format_for_output(output_format)
    image_to_encode = _prepare_image_for_output_format(image, output_format)
    save_kwargs = _save_kwargs_for_format(output_format, image_to_encode)
    image_to_encode.save(buffer, format=pil_format, **save_kwargs)
    return buffer.getvalue()


def save_image_to_path(
    image: Image.Image,
    target_path: Path,
    output_format: ImageOutputFormat,
) -> None:
    """Save image to disk using the requested output format."""
    target_path.parent.mkdir(parents=True, exist_ok=True)
    pil_format = _pil_format_for_output(output_format)
    image_to_save = _prepare_image_for_output_format(image, output_format)
    save_kwargs = _save_kwargs_for_format(output_format, image_to_save)
    image_to_save.save(target_path, format=pil_format, **save_kwargs)


def write_encoded_image_bytes_to_path(target_path: Path, encoded_image_bytes: bytes) -> None:
    """Persist already-encoded bytes so hashing and stored output stay consistent."""
    target_path.parent.mkdir(parents=True, exist_ok=True)
    target_path.write_bytes(encoded_image_bytes)


def _pil_format_for_output(output_format: ImageOutputFormat) -> str:
    if output_format == ImageOutputFormat.PNG:
        return "PNG"
    if output_format == ImageOutputFormat.JPEG:
        return "JPEG"
    if output_format == ImageOutputFormat.WEBP:
        return "WEBP"
    raise ValueError(f"Unsupported output format: {output_format}")


def _save_kwargs_for_format(output_format: ImageOutputFormat, image: Image.Image) -> dict[str, object]:
    if output_format == ImageOutputFormat.JPEG:
        return {"quality": 92, "optimize": True}
    if output_format == ImageOutputFormat.WEBP:
        return {"quality": 90, "method": 6}
    if output_format == ImageOutputFormat.PNG:
        return {"optimize": True}
    raise ValueError(f"Unsupported output format: {output_format}")


def _prepare_image_for_output_format(image: Image.Image, output_format: ImageOutputFormat) -> Image.Image:
    if output_format != ImageOutputFormat.JPEG:
        return image
    if image.mode in ("RGBA", "P"):
        return image.convert("RGB")
    return image
