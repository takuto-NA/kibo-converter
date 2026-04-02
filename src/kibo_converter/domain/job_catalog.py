"""Responsibility: Define the visible job catalog for the launcher-style UI."""

from __future__ import annotations

from dataclasses import dataclass

from kibo_converter.domain.job_types import JobAvailability, JobType


@dataclass(frozen=True, slots=True)
class JobCatalogEntry:
    """One job shown in the launcher-style catalog."""

    job_type: JobType
    display_name: str
    short_description: str
    availability: JobAvailability
    input_format_summary: str
    output_format_summary: str
    note: str


def build_default_job_catalog() -> tuple[JobCatalogEntry, ...]:
    """Return the current product job catalog in display order."""
    return (
        JobCatalogEntry(
            job_type=JobType.IMAGE_CONVERSION,
            display_name="画像変換",
            short_description="画像ファイルを別形式へ変換します。",
            availability=JobAvailability.AVAILABLE,
            input_format_summary=".heic, .heif, .png, .jpg, .jpeg, .webp",
            output_format_summary="PNG, JPEG, WEBP",
            note="HEIC / HEIF は実行環境に依存します。",
        ),
        JobCatalogEntry(
            job_type=JobType.VIDEO_CONVERSION,
            display_name="動画変換",
            short_description="動画ファイルの形式変換に対応予定です。",
            availability=JobAvailability.COMING_SOON,
            input_format_summary="近日対応",
            output_format_summary="近日対応",
            note="現在は選択できません。",
        ),
        JobCatalogEntry(
            job_type=JobType.DOCUMENT_CONVERSION,
            display_name="文書変換",
            short_description="文書ファイルの変換に対応予定です。",
            availability=JobAvailability.COMING_SOON,
            input_format_summary="近日対応",
            output_format_summary="近日対応",
            note="現在は選択できません。",
        ),
        JobCatalogEntry(
            job_type=JobType.TABULAR_TEXT_CONVERSION,
            display_name="CSV / テキスト変換",
            short_description="表データやテキスト変換に対応予定です。",
            availability=JobAvailability.COMING_SOON,
            input_format_summary="近日対応",
            output_format_summary="近日対応",
            note="現在は選択できません。",
        ),
    )
