# Responsibility: Run image conversion jobs off the UI thread using QObject + QThread + signals.

from __future__ import annotations

import traceback
from datetime import datetime, timezone
from pathlib import Path

from PyQt6.QtCore import QObject, QThread, pyqtSignal

from kibo_converter.application.job_preflight import JobPreflightError, run_job_preflight
from kibo_converter.application.progress_reporter import ProgressSnapshot
from kibo_converter.domain.job_definition import JobDefinition
from kibo_converter.domain.job_result import FileResultRecord, FileResultStatus, JobRunSummary
from kibo_converter.domain.processing_steps import ImageOutputFormat
from kibo_converter.infrastructure import filesystem_scanner
from kibo_converter.infrastructure.image_reader_writer import (
    apply_exif_orientation,
    encode_image_to_bytes,
    open_image,
    resize_to_max_edge,
    write_encoded_image_bytes_to_path,
)
from kibo_converter.infrastructure.output_collision_resolver import resolve_target_path
from kibo_converter.infrastructure.result_logger import append_file_result_json_line, write_job_summary_json_line


def build_default_target_path(
    *,
    source_path: Path,
    output_format: ImageOutputFormat,
    output_directory_path: Path,
) -> Path:
    """Build the default output path preserving the source stem."""
    extension = _file_extension_for_image_output_format(output_format)
    return output_directory_path / f"{source_path.stem}{extension}"


def _file_extension_for_image_output_format(output_format: ImageOutputFormat) -> str:
    if output_format == ImageOutputFormat.PNG:
        return ".png"
    if output_format == ImageOutputFormat.JPEG:
        return ".jpg"
    if output_format == ImageOutputFormat.WEBP:
        return ".webp"
    raise ValueError(f"Unsupported output format: {output_format}")


class ImageConversionWorker(QObject):
    """Worker object that runs on a QThread and emits Qt signals for UI updates."""

    preflight_failed = pyqtSignal(str)
    progress_updated = pyqtSignal(object)
    file_result_emitted = pyqtSignal(object)
    job_finished = pyqtSignal(object)

    def __init__(
        self,
        *,
        job_definition: JobDefinition,
        log_file_path: Path | None,
    ) -> None:
        super().__init__()
        self._job_definition = job_definition
        self._log_file_path = log_file_path
        self._cancellation_requested = False

    def request_cancel(self) -> None:
        """Request cooperative cancellation before starting the next file."""
        self._cancellation_requested = True

    def run_conversion_job(self) -> None:
        """Execute the conversion job until completion or cancellation."""
        try:
            run_job_preflight(self._job_definition)
        except JobPreflightError as exc:
            self.preflight_failed.emit(str(exc))
            return

        source_files = filesystem_scanner.list_matching_files(self._job_definition.selection_rules)
        total_files = len(source_files)
        summary = JobRunSummary(total_files=total_files)

        initial_snapshot = ProgressSnapshot(completed_file_count=0, total_file_count=total_files)
        self.progress_updated.emit(initial_snapshot)

        if total_files == 0:
            if self._log_file_path is not None:
                write_job_summary_json_line(
                    self._log_file_path,
                    total_files=summary.total_files,
                    success_count=summary.success_count,
                    failure_count=summary.failure_count,
                    skipped_count=summary.skipped_count,
                    cancelled_count=summary.cancelled_count,
                )
            self.job_finished.emit(summary)
            return

        for index, source_path in enumerate(source_files, start=1):
            if self._cancellation_requested:
                for skipped_path in source_files[index - 1 :]:
                    record = _build_cancelled_record(skipped_path=skipped_path)
                    summary.file_results.append(record)
                    summary.cancelled_count += 1
                    self._emit_file_result(record)
                break

            record = self._process_single_source_file(source_path=source_path)
            summary.file_results.append(record)

            if record.status == FileResultStatus.SUCCESS:
                summary.success_count += 1
            elif record.status == FileResultStatus.FAILURE:
                summary.failure_count += 1
            elif record.status == FileResultStatus.SKIPPED_DUPLICATE_OUTPUT:
                summary.skipped_count += 1
            elif record.status == FileResultStatus.SKIPPED_CANCELLED:
                summary.cancelled_count += 1

            self._emit_file_result(record)

            snapshot = ProgressSnapshot(
                completed_file_count=index,
                total_file_count=total_files,
            )
            self.progress_updated.emit(snapshot)

        if self._log_file_path is not None:
            write_job_summary_json_line(
                self._log_file_path,
                total_files=summary.total_files,
                success_count=summary.success_count,
                failure_count=summary.failure_count,
                skipped_count=summary.skipped_count,
                cancelled_count=summary.cancelled_count,
            )

        self.job_finished.emit(summary)

    def _emit_file_result(self, record: FileResultRecord) -> None:
        self.file_result_emitted.emit(record)
        if self._log_file_path is None:
            return
        append_file_result_json_line(self._log_file_path, record)

    def _process_single_source_file(self, *, source_path: Path) -> FileResultRecord:
        started_at = datetime.now(timezone.utc)
        desired_target_path = build_default_target_path(
            source_path=source_path,
            output_format=self._job_definition.output_format,
            output_directory_path=self._job_definition.output_rules.output_directory_path,
        )

        try:
            image = open_image(source_path)
            image = apply_exif_orientation(image)
            max_edge = self._job_definition.resize_options.max_edge_pixels
            if max_edge is not None:
                image = resize_to_max_edge(image, max_edge)

            encoded_bytes = encode_image_to_bytes(image, self._job_definition.output_format)
            resolution = resolve_target_path(
                desired_target_path=desired_target_path,
                encoded_output_bytes=encoded_bytes,
                collision_policy=self._job_definition.output_rules.collision_policy,
            )

            if resolution.skipped_because_duplicate:
                finished_at = datetime.now(timezone.utc)
                return FileResultRecord(
                    source_path=source_path,
                    target_path=resolution.final_target_path,
                    status=FileResultStatus.SKIPPED_DUPLICATE_OUTPUT,
                    error_code=None,
                    error_summary=None,
                    error_detail=None,
                    started_at=started_at,
                    finished_at=finished_at,
                )

            write_encoded_image_bytes_to_path(resolution.final_target_path, encoded_bytes)
            finished_at = datetime.now(timezone.utc)
            return FileResultRecord(
                source_path=source_path,
                target_path=resolution.final_target_path,
                status=FileResultStatus.SUCCESS,
                error_code=None,
                error_summary=None,
                error_detail=None,
                started_at=started_at,
                finished_at=finished_at,
            )
        except Exception as exc:
            finished_at = datetime.now(timezone.utc)
            return FileResultRecord(
                source_path=source_path,
                target_path=desired_target_path,
                status=FileResultStatus.FAILURE,
                error_code=type(exc).__name__,
                error_summary=str(exc),
                error_detail=traceback.format_exc(),
                started_at=started_at,
                finished_at=finished_at,
            )


def _build_cancelled_record(*, skipped_path: Path) -> FileResultRecord:
    now = datetime.now(timezone.utc)
    return FileResultRecord(
        source_path=skipped_path,
        target_path=None,
        status=FileResultStatus.SKIPPED_CANCELLED,
        error_code="cancelled",
        error_summary="Job cancelled before this file started.",
        error_detail=None,
        started_at=now,
        finished_at=now,
    )


class ImageJobThreadController:
    """Owns a QThread and ImageConversionWorker for a single job run."""

    def __init__(self) -> None:
        self._thread = QThread()
        self._worker: ImageConversionWorker | None = None

    def start_job(self, *, job_definition: JobDefinition, log_file_path: Path | None) -> ImageConversionWorker:
        """Start worker on a background thread; returns the worker for signal wiring."""
        self._worker = ImageConversionWorker(job_definition=job_definition, log_file_path=log_file_path)
        self._worker.moveToThread(self._thread)
        self._thread.started.connect(self._worker.run_conversion_job)
        self._worker.job_finished.connect(self._thread.quit)
        self._worker.preflight_failed.connect(self._thread.quit)
        self._thread.start()
        return self._worker

    def request_cancel(self) -> None:
        """Forward cancellation to the active worker."""
        if self._worker is None:
            return
        self._worker.request_cancel()

    def wait_until_finished(self, timeout_milliseconds: int) -> bool:
        """Wait for the background thread to stop."""
        return self._thread.wait(timeout_milliseconds)
