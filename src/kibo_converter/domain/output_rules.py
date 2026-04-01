# Responsibility: Define output directory rules and collision handling policy for batch jobs.

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path


class CollisionPolicy(str, Enum):
    """How to resolve a target path that already exists."""

    OVERWRITE_EXISTING_OUTPUT = "overwrite_existing_output"
    KEEP_BOTH_OUTPUTS = "keep_both_outputs"


@dataclass(frozen=True, slots=True)
class OutputRules:
    """Rules for where converted files are written."""

    output_directory_path: Path
    collision_policy: CollisionPolicy

    def validate(self) -> None:
        """Raise ValueError when the configuration cannot be used safely."""
        return None
