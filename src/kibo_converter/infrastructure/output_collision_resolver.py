# Responsibility: Resolve output filename conflicts using overwrite or content-hash based unique names.

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from kibo_converter.constants import DEFAULT_HASH_PREFIX_LENGTH_CHARACTERS
from kibo_converter.domain.output_rules import CollisionPolicy


@dataclass(frozen=True, slots=True)
class CollisionResolutionResult:
    """Outcome of resolving a target path for one conversion."""

    action: str
    final_target_path: Path
    skipped_because_duplicate: bool


def compute_sha256_hex_digest_bytes(content_bytes: bytes) -> str:
    """Compute a stable hex digest for output bytes."""
    return hashlib.sha256(content_bytes).hexdigest()


def resolve_target_path(
    *,
    desired_target_path: Path,
    encoded_output_bytes: bytes,
    collision_policy: CollisionPolicy,
) -> CollisionResolutionResult:
    """
    Decide the final output path.

    When KEEP_BOTH_OUTPUTS and a file exists:
    - If bytes match, skip write.
    - If bytes differ, pick a unique sibling name using a hash prefix.
    """
    if collision_policy == CollisionPolicy.OVERWRITE_EXISTING_OUTPUT:
        return CollisionResolutionResult(
            action="overwrite",
            final_target_path=desired_target_path,
            skipped_because_duplicate=False,
        )

    if not desired_target_path.exists():
        return CollisionResolutionResult(
            action="create_new",
            final_target_path=desired_target_path,
            skipped_because_duplicate=False,
        )

    existing_bytes = desired_target_path.read_bytes()
    new_digest = compute_sha256_hex_digest_bytes(encoded_output_bytes)
    existing_digest = compute_sha256_hex_digest_bytes(existing_bytes)
    if new_digest == existing_digest:
        return CollisionResolutionResult(
            action="skip_identical_existing_output",
            final_target_path=desired_target_path,
            skipped_because_duplicate=True,
        )

    unique_path = _build_unique_sibling_path(
        base_path=desired_target_path,
        content_digest_hex=new_digest,
    )
    return CollisionResolutionResult(
        action="write_unique_name",
        final_target_path=unique_path,
        skipped_because_duplicate=False,
    )


def _build_unique_sibling_path(*, base_path: Path, content_digest_hex: str) -> Path:
    """Build a non-colliding filename using a short hash prefix and fallback suffix."""
    parent = base_path.parent
    stem = base_path.stem
    suffix = base_path.suffix
    hash_prefix = content_digest_hex[:DEFAULT_HASH_PREFIX_LENGTH_CHARACTERS]
    candidate = parent / f"{stem}__{hash_prefix}{suffix}"
    if not candidate.exists():
        return candidate

    timestamp_utc = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    sequential_index = 1
    while True:
        fallback = parent / f"{stem}__{hash_prefix}__{timestamp_utc}__{sequential_index}{suffix}"
        if not fallback.exists():
            return fallback
        sequential_index += 1
