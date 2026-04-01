# Responsibility: Unit tests for output rules validation.

from __future__ import annotations

from pathlib import Path

from kibo_converter.domain.output_rules import CollisionPolicy, OutputRules


def test_output_rules_accepts_absolute_directory_path() -> None:
    rules = OutputRules(
        output_directory_path=Path("C:/output"),
        collision_policy=CollisionPolicy.KEEP_BOTH_OUTPUTS,
    )

    rules.validate()


def test_output_rules_accept_current_directory_path() -> None:
    rules = OutputRules(
        output_directory_path=Path("."),
        collision_policy=CollisionPolicy.KEEP_BOTH_OUTPUTS,
    )

    rules.validate()
