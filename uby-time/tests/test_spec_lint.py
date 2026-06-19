from __future__ import annotations

import json

from uby_time import iter_uby_expression_candidates, lint_uby_expressions
from uby_time.cli import main


def test_iter_uby_expression_candidates_ignores_plain_title_words() -> None:
    text = """
# UBY Cross-scale Time Labeling Specification

Example: UBY 380K [model=LCDM-Planck2018] [spec=0.1.0]
Mnemonic: UBY 137870+002026 [model=LCDM-Planck2018] [spec=0.1.0]
"""
    candidates = list(iter_uby_expression_candidates(text))
    assert candidates == [
        (4, 10, "UBY 380K [model=LCDM-Planck2018] [spec=0.1.0]"),
        (5, 11, "UBY 137870+002026 [model=LCDM-Planck2018] [spec=0.1.0]"),
    ]


def test_lint_uby_expressions_reports_missing_spec_as_error_and_warning() -> None:
    issues = lint_uby_expressions("Example: UBY 380K [model=LCDM-Planck2018]")
    codes = [issue.code for issue in issues]
    assert codes == ["SPEC_VERSION_UNDECLARED", "MAGNITUDE_NOT_FOR_STORAGE", "SPEC_VERSION_REQUIRED"]
    assert issues[-1].level == "error"


def test_lint_uby_expressions_allows_missing_spec_when_configured() -> None:
    issues = lint_uby_expressions(
        "Example: UBY 13787002026.0 [model=LCDM-Planck2018]",
        require_spec=False,
    )
    assert issues == []


def test_lint_uby_expressions_reports_model_warning_for_level_2() -> None:
    issues = lint_uby_expressions("Example: UBY 380K [spec=0.1.0]")
    codes = [issue.code for issue in issues]
    assert codes == ["MODEL_VERSION_REQUIRED", "MAGNITUDE_NOT_FOR_STORAGE"]


def test_cli_lint_spec_ok(tmp_path, capsys) -> None:
    path = tmp_path / "spec.md"
    path.write_text("Example: UBY 13787002026.0 [model=LCDM-Planck2018] [spec=0.1.0]\n", encoding="utf-8")

    assert main(["lint", "spec", str(path)]) == 0
    assert capsys.readouterr().out.strip() == "ok"


def test_cli_lint_spec_json_reports_errors(tmp_path, capsys) -> None:
    path = tmp_path / "spec.md"
    path.write_text("Example: UBY 380K [model=LCDM-Planck2018]\n", encoding="utf-8")

    assert main(["lint", "spec", str(path), "--format", "json"]) == 1
    payload = json.loads(capsys.readouterr().out)
    assert [item["code"] for item in payload] == [
        "SPEC_VERSION_UNDECLARED",
        "MAGNITUDE_NOT_FOR_STORAGE",
        "SPEC_VERSION_REQUIRED",
    ]
    assert payload[-1]["level"] == "error"
