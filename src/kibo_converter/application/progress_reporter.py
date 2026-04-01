# Responsibility: Normalize progress reporting values for UI binding.

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ProgressSnapshot:
    """Immutable progress values for one update tick."""

    completed_file_count: int
    total_file_count: int

    @property
    def ratio(self) -> float:
        """Return a 0.0-1.0 ratio when total is positive."""
        if self.total_file_count <= 0:
            return 0.0
        return self.completed_file_count / self.total_file_count
