from __future__ import annotations

from pathlib import Path

import pytest

from uby_time import lint_uby_expressions_in_file


def test_real_specification_has_no_uby_lint_errors() -> None:
    spec_path = Path(__file__).resolve().parents[2] / "UBY-TLS-WD-0.1.0.md"
    if not spec_path.exists():
        pytest.skip("UBY-TLS-WD-0.1.0.md is outside this package checkout")

    issues = lint_uby_expressions_in_file(spec_path)
    errors = [issue for issue in issues if issue.level == "error"]

    assert errors == []
