"""Responsibility: Define supported job types and rollout status for the job-centered UI."""

from __future__ import annotations

from enum import Enum


class JobType(str, Enum):
    """Kinds of conversion jobs the product can expose."""

    IMAGE_CONVERSION = "image_conversion"
    VIDEO_CONVERSION = "video_conversion"
    DOCUMENT_CONVERSION = "document_conversion"
    TABULAR_TEXT_CONVERSION = "tabular_text_conversion"


class JobAvailability(str, Enum):
    """Whether a job type is usable now or only advertised for future rollout."""

    AVAILABLE = "available"
    COMING_SOON = "coming_soon"
