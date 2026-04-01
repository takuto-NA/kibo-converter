# Responsibility: Integration tests for output collision resolution behavior.

from __future__ import annotations

from pathlib import Path

from kibo_converter.domain.output_rules import CollisionPolicy
from kibo_converter.infrastructure.output_collision_resolver import resolve_target_path


def test_keep_both_skips_when_existing_bytes_match(tmp_path: Path) -> None:
    desired = tmp_path / "a.png"
    payload = b"same-bytes"
    desired.write_bytes(payload)

    result = resolve_target_path(
        desired_target_path=desired,
        encoded_output_bytes=payload,
        collision_policy=CollisionPolicy.KEEP_BOTH_OUTPUTS,
    )

    assert result.skipped_because_duplicate is True
    assert result.final_target_path == desired


def test_keep_both_writes_unique_name_when_bytes_differ(tmp_path: Path) -> None:
    desired = tmp_path / "a.png"
    desired.write_bytes(b"old-bytes")

    result = resolve_target_path(
        desired_target_path=desired,
        encoded_output_bytes=b"new-bytes",
        collision_policy=CollisionPolicy.KEEP_BOTH_OUTPUTS,
    )

    assert result.skipped_because_duplicate is False
    assert result.final_target_path != desired
    assert result.final_target_path.name.startswith("a__")


def test_overwrite_always_targets_desired_path(tmp_path: Path) -> None:
    desired = tmp_path / "a.png"
    desired.write_bytes(b"old-bytes")

    result = resolve_target_path(
        desired_target_path=desired,
        encoded_output_bytes=b"new-bytes",
        collision_policy=CollisionPolicy.OVERWRITE_EXISTING_OUTPUT,
    )

    assert result.final_target_path == desired
    assert result.skipped_because_duplicate is False
