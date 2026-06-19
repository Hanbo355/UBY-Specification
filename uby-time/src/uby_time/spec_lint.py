from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from .errors import UBYParseError
from .parsing import parse_uby_expression

_TAG_PATTERN = r"(?:\s+\[[A-Za-z]+=[^\]]+\])"
_UBY_CANDIDATE_RE = re.compile(
    r"\bUBY\s+"
    r"(?:"
    r"\d+(?:\.\d+)?(?:x|×)10\^-?\d+"
    r"|"
    r"\d{6}[+-]\d{6}"
    r"|"
    r"\d{6}\s+(?:AD|BC)\d+"
    r"|"
    r"\d+(?:\.\d+)?(?:[KMGT])?"
    r")"
    rf"(?:{_TAG_PATTERN})*"
)


@dataclass(frozen=True)
class UBYLintIssue:
    """A lint finding for a UBY expression embedded in a specification document."""

    line: int
    column: int
    expression: str
    code: str
    level: str
    message: str


def iter_uby_expression_candidates(text: str) -> Iterable[tuple[int, int, str]]:
    """Yield likely UBY expressions from Markdown-like text.

    The extractor intentionally looks for expression-shaped labels only, so prose
    such as document titles containing the word "UBY" are ignored.
    """

    for line_number, line in enumerate(text.splitlines(), start=1):
        for match in _UBY_CANDIDATE_RE.finditer(line):
            yield line_number, match.start() + 1, match.group(0).strip()


def lint_uby_expressions(text: str, *, require_spec: bool = True) -> list[UBYLintIssue]:
    """Lint UBY expressions embedded in Markdown/specification text."""

    issues: list[UBYLintIssue] = []

    for line, column, expression in iter_uby_expression_candidates(text):
        try:
            parsed = parse_uby_expression(expression)
        except UBYParseError as exc:
            issues.append(
                UBYLintIssue(
                    line=line,
                    column=column,
                    expression=expression,
                    code="INVALID_UBY_EXPRESSION",
                    level="error",
                    message=str(exc),
                )
            )
            continue

        for warning in parsed.warnings:
            if warning == "SPEC_VERSION_UNDECLARED" and not require_spec:
                continue
            issues.append(
                UBYLintIssue(
                    line=line,
                    column=column,
                    expression=expression,
                    code=warning,
                    level="warning",
                    message=warning,
                )
            )

        if require_spec and parsed.uby_version is None:
            issues.append(
                UBYLintIssue(
                    line=line,
                    column=column,
                    expression=expression,
                    code="SPEC_VERSION_REQUIRED",
                    level="error",
                    message="Formal specification examples should include [spec=<version>].",
                )
            )

    return issues


def lint_uby_expressions_in_file(path: str | Path, *, require_spec: bool = True) -> list[UBYLintIssue]:
    """Read and lint a Markdown/specification file."""

    text = Path(path).read_text(encoding="utf-8")
    return lint_uby_expressions(text, require_spec=require_spec)


def lint_issues_to_dicts(issues: Iterable[UBYLintIssue]) -> list[dict[str, object]]:
    """Convert lint issues to JSON-safe dictionaries."""

    return [
        {
            "line": issue.line,
            "column": issue.column,
            "expression": issue.expression,
            "code": issue.code,
            "level": issue.level,
            "message": issue.message,
        }
        for issue in issues
    ]
