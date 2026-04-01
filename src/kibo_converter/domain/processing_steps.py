# Responsibility: Describe image processing steps such as resize and output format for a job.

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class ImageOutputFormat(str, Enum):
    """Supported raster output formats for MVP image conversion."""

    PNG = "png"
    JPEG = "jpeg"
    WEBP = "webp"


@dataclass(frozen=True, slots=True)
class ResizeOptions:
    """Optional resize; when max_edge_pixels is None, dimensions are unchanged."""

    max_edge_pixels: int | None

    def validate(self) -> None:
        """Raise ValueError when resize configuration is invalid."""
        if self.max_edge_pixels is None:
            return
        minimum_allowed_edge_pixels = 1
        if self.max_edge_pixels < minimum_allowed_edge_pixels:
            raise ValueError("max_edge_pixels must be at least 1 when provided.")
