# Responsibility: UI tests for candidate review table behavior.

from __future__ import annotations

from pathlib import Path

from kibo_converter.domain.job_ui_models import CandidateReviewItem, CandidateReviewStatus
from kibo_converter.ui.candidate_review_panel import CandidateReviewPanelWidget


def test_candidate_review_panel_populates_rows(qtbot) -> None:
    widget = CandidateReviewPanelWidget()
    qtbot.addWidget(widget)

    widget.set_candidate_items(
        [
            CandidateReviewItem(
                source_path=Path("C:/input/a.png"),
                extension_lower_case=".png",
                status=CandidateReviewStatus.INCLUDED,
                reason="このジョブの変換対象です。",
                is_selected=True,
            ),
            CandidateReviewItem(
                source_path=Path("C:/input/b.txt"),
                extension_lower_case=".txt",
                status=CandidateReviewStatus.EXCLUDED,
                reason="このジョブでは未対応の拡張子です。",
                is_selected=False,
            ),
        ]
    )

    assert widget.row_count() == 2


def test_candidate_review_panel_allows_rechecking_user_excluded_rows(qtbot) -> None:
    widget = CandidateReviewPanelWidget()
    qtbot.addWidget(widget)
    excluded_source_path = Path("C:/input/a.png")

    widget.set_candidate_items(
        [
            CandidateReviewItem(
                source_path=excluded_source_path,
                extension_lower_case=".png",
                status=CandidateReviewStatus.EXCLUDED_BY_USER,
                reason="ユーザーが今回の実行対象から外しました。",
                is_selected=False,
            )
        ]
    )

    assert widget.manually_excluded_source_paths() == frozenset({excluded_source_path})

    widget.set_row_checked(0, True)

    assert widget.manually_excluded_source_paths() == frozenset()
