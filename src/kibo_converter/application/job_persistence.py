# Responsibility: Serialize and deserialize JobDefinition to versioned JSON with strict validation.

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from kibo_converter.constants import JOB_SCHEMA_VERSION_CURRENT
from kibo_converter.domain.file_selection import FileSelectionRules
from kibo_converter.domain.job_definition import JobDefinition
from kibo_converter.domain.output_rules import CollisionPolicy, OutputRules
from kibo_converter.domain.processing_steps import ImageOutputFormat, ResizeOptions


class JobPersistenceError(Exception):
    """Raised when a job file cannot be read or deserialized safely."""


def _require_dict_payload(payload: Any) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise JobPersistenceError("設定ファイルの先頭は JSON のオブジェクトである必要があります。")
    return payload


def _require_int(key: str, value: Any) -> int:
    if not isinstance(value, int):
        raise JobPersistenceError(f"Invalid type for '{key}': expected int.")
    return value


def _require_str(key: str, value: Any) -> str:
    if not isinstance(value, str):
        raise JobPersistenceError(f"Invalid type for '{key}': expected string.")
    return value


def _require_non_empty_path_text(key: str, value: Any) -> str:
    text = _require_str(key, value).strip()
    if not text:
        raise JobPersistenceError(f"Invalid '{key}': path text must not be empty.")
    return text


def _require_bool(key: str, value: Any) -> bool:
    if not isinstance(value, bool):
        raise JobPersistenceError(f"Invalid type for '{key}': expected boolean.")
    return value


def _parse_extensions_list(value: Any) -> frozenset[str]:
    if not isinstance(value, list):
        raise JobPersistenceError("included_file_extensions must be a JSON array.")
    normalized: set[str] = set()
    for item in value:
        if not isinstance(item, str):
            raise JobPersistenceError("Each extension must be a string.")
        extension = item.strip().lower()
        if not extension.startswith("."):
            extension = f".{extension}"
        normalized.add(extension)
    if not normalized:
        raise JobPersistenceError("拡張子は1つ以上必要です。")
    return frozenset(normalized)


def job_definition_to_dict(job_definition: JobDefinition) -> dict[str, Any]:
    """Convert a domain job to a JSON-serializable dict."""
    return {
        "schema_version": job_definition.schema_version,
        "selection_rules": {
            "input_directory_path": str(job_definition.selection_rules.input_directory_path),
            "included_file_extensions": sorted(
                job_definition.selection_rules.included_file_extensions_lower_case
            ),
            "include_subdirectories_recursively": (
                job_definition.selection_rules.include_subdirectories_recursively
            ),
        },
        "output_format": job_definition.output_format.value,
        "resize_options": {
            "max_edge_pixels": job_definition.resize_options.max_edge_pixels,
        },
        "output_rules": {
            "output_directory_path": str(job_definition.output_rules.output_directory_path),
            "collision_policy": job_definition.output_rules.collision_policy.value,
        },
    }


def job_definition_from_dict(payload: dict[str, Any]) -> JobDefinition:
    """Build JobDefinition from a dict; raises JobPersistenceError on invalid input."""
    schema_version = _require_int("schema_version", payload.get("schema_version"))
    if schema_version != JOB_SCHEMA_VERSION_CURRENT:
        raise JobPersistenceError(
            f"schema_version {schema_version} はこのアプリでは扱えません。"
            f"対応しているのは {JOB_SCHEMA_VERSION_CURRENT} のみです。"
        )

    selection_payload = payload.get("selection_rules")
    if not isinstance(selection_payload, dict):
        raise JobPersistenceError("selection_rules が無いか、形式が正しくありません。")

    input_directory_path = Path(
        _require_non_empty_path_text("input_directory_path", selection_payload.get("input_directory_path"))
    )
    extensions = _parse_extensions_list(selection_payload.get("included_file_extensions"))
    recursive = _require_bool(
        "include_subdirectories_recursively",
        selection_payload.get("include_subdirectories_recursively"),
    )

    output_format_raw = _require_str("output_format", payload.get("output_format"))
    try:
        output_format = ImageOutputFormat(output_format_raw)
    except ValueError as exc:
        raise JobPersistenceError(f"output_format の値が不正です: {output_format_raw}") from exc

    resize_payload = payload.get("resize_options")
    if not isinstance(resize_payload, dict):
        raise JobPersistenceError("resize_options が無いか、形式が正しくありません。")

    max_edge_value = resize_payload.get("max_edge_pixels")
    max_edge_pixels: int | None
    if max_edge_value is None:
        max_edge_pixels = None
    else:
        max_edge_pixels = _require_int("max_edge_pixels", max_edge_value)

    output_payload = payload.get("output_rules")
    if not isinstance(output_payload, dict):
        raise JobPersistenceError("output_rules が無いか、形式が正しくありません。")

    output_directory_path = Path(
        _require_non_empty_path_text("output_directory_path", output_payload.get("output_directory_path"))
    )
    collision_raw = _require_str("collision_policy", output_payload.get("collision_policy"))
    try:
        collision_policy = CollisionPolicy(collision_raw)
    except ValueError as exc:
        raise JobPersistenceError(f"collision_policy の値が不正です: {collision_raw}") from exc

    selection_rules = FileSelectionRules(
        input_directory_path=input_directory_path,
        included_file_extensions_lower_case=extensions,
        include_subdirectories_recursively=recursive,
    )
    resize_options = ResizeOptions(max_edge_pixels=max_edge_pixels)
    output_rules = OutputRules(
        output_directory_path=output_directory_path,
        collision_policy=collision_policy,
    )

    job_definition = JobDefinition(
        schema_version=schema_version,
        selection_rules=selection_rules,
        output_format=output_format,
        resize_options=resize_options,
        output_rules=output_rules,
    )
    try:
        job_definition.validate()
    except ValueError as exc:
        raise JobPersistenceError(str(exc)) from exc

    return job_definition


def save_job_definition_to_json_file(job_definition: JobDefinition, file_path: Path) -> None:
    """Write JobDefinition as formatted JSON."""
    job_definition.validate()
    file_path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(job_definition_to_dict(job_definition), indent=2, ensure_ascii=False)
    file_path.write_text(text, encoding="utf-8")


def load_job_definition_from_json_file(file_path: Path) -> JobDefinition:
    """Read JobDefinition from JSON; raises JobPersistenceError on malformed files."""
    try:
        raw_text = file_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise JobPersistenceError(f"設定ファイルを読み込めません: {file_path}") from exc

    try:
        payload = json.loads(raw_text)
    except json.JSONDecodeError as exc:
        raise JobPersistenceError("設定ファイルは JSON として読み取れません。") from exc

    root = _require_dict_payload(payload)
    return job_definition_from_dict(root)
