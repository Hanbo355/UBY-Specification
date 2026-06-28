from __future__ import annotations

import argparse
import csv
import json
import sys
from typing import Any

from .anchors import DEFAULT_ANCHOR
from .constants import DEFAULT_MODEL_VERSION, DEFAULT_ROUNDING_RULE, GENERATED_BY, UBY_SPEC_VERSION
from .cross_domain import cross_domain_join, null_hypothesis_test
from .conversion import (
    astronomical_year_to_uby,
    bc_year_to_uby,
    iso_to_uby,
    jd_to_uby,
    uby_to_iso,
    uby_to_jd,
)
from .cosmology import redshift_to_uby
from .formatting import (
    format_academic_mnemonic,
    format_full,
    format_magnitude,
    format_scientific,
)
from .models import PrecisionLevel, UBYTime, ValidationMessage
from .parsing import parse_uby_expression
from .serialization import to_dict
from .spec_lint import lint_issues_to_dicts, lint_uby_expressions_in_file
from .validation import validate_uby_time


def _csv_value(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, list):
        return "|".join(str(item) for item in value)
    return str(value)


def _print_csv_rows(rows: list[dict[str, Any]], *, fieldnames: list[str] | None = None) -> None:
    if fieldnames is None:
        fieldnames = []
        for row in rows:
            for key in row:
                if key not in fieldnames:
                    fieldnames.append(key)

    writer = csv.DictWriter(sys.stdout, fieldnames=fieldnames, lineterminator="\n")
    writer.writeheader()
    for row in rows:
        writer.writerow({key: _csv_value(row.get(key)) for key in fieldnames})


def _print_payload(payload: Any, *, output_format: str) -> None:
    if output_format == "json":
        print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))
    elif output_format == "csv":
        if isinstance(payload, list):
            _print_csv_rows(payload)
        elif isinstance(payload, dict):
            _print_csv_rows([payload])
        else:
            _print_csv_rows([{"value": payload}])
    else:
        if isinstance(payload, dict):
            for key, value in payload.items():
                print(f"{key}={value}")
        else:
            print(payload)


def _parsed_to_uby(parsed) -> UBYTime:
    return UBYTime(
        uby_value=parsed.uby_value,
        uby_version=parsed.uby_version or UBY_SPEC_VERSION,
        model_version=parsed.model_version,
        precision_level=parsed.precision_level or PrecisionLevel.LEVEL_1,
        source_time=parsed.raw,
        source_system="UBYExpression",
        rounding_rule=DEFAULT_ROUNDING_RULE,
        generated_by=GENERATED_BY,
        anchor_id=DEFAULT_ANCHOR.anchor_id,
        anchor_jd=DEFAULT_ANCHOR.anchor_jd,
        anchor_uby=DEFAULT_ANCHOR.anchor_uby,
    )


def _add_common_output_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--format", choices=["text", "json", "csv"], default="text")
    parser.add_argument("--model", default=DEFAULT_MODEL_VERSION)
    parser.add_argument("--spec", default=UBY_SPEC_VERSION)
    parser.add_argument("--no-spec", action="store_true")


def _display_uby(
    uby: UBYTime,
    *,
    output_format: str,
    include_spec: bool = True,
    extra_fields: dict[str, Any] | None = None,
) -> None:
    if output_format in {"json", "csv"}:
        payload = to_dict(uby)
        if extra_fields:
            payload.update(extra_fields)
        _print_payload(payload, output_format=output_format)
    else:
        print(format_full(uby, include_spec=include_spec))
        print(f"precision_level={uby.precision_level.value}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="uby")
    sub = parser.add_subparsers(dest="cmd", required=True)

    convert = sub.add_parser("convert", help="Convert native time values to UBY")
    convert_sub = convert.add_subparsers(dest="kind", required=True)

    convert_iso = convert_sub.add_parser("iso", help="Convert ISO 8601 / UTC time to UBY")
    convert_iso.add_argument("value")
    _add_common_output_options(convert_iso)

    convert_jd = convert_sub.add_parser("jd", help="Convert Julian Date to UBY")
    convert_jd.add_argument("value")
    _add_common_output_options(convert_jd)

    convert_year = convert_sub.add_parser("year", help="Convert ISO astronomical year to UBY")
    convert_year.add_argument("value", type=int)
    convert_year.add_argument("--include-model", action="store_true")
    _add_common_output_options(convert_year)

    convert_bc = convert_sub.add_parser("bc", help="Convert traditional BC year to UBY")
    convert_bc.add_argument("value", type=int)
    convert_bc.add_argument("--include-model", action="store_true")
    _add_common_output_options(convert_bc)

    redshift = sub.add_parser("redshift", help="Convert cosmological redshift z to UBY")
    redshift.add_argument("z", type=float)
    redshift.add_argument("--cosmology", default="Planck18")
    _add_common_output_options(redshift)

    reverse = sub.add_parser("reverse", help="Convert UBY values back to native forms")
    reverse_sub = reverse.add_subparsers(dest="kind", required=True)

    reverse_jd = reverse_sub.add_parser("jd")
    reverse_jd.add_argument("value")

    reverse_iso = reverse_sub.add_parser("iso")
    reverse_iso.add_argument("value")

    parse_cmd = sub.add_parser("parse", help="Parse a UBY expression")
    parse_cmd.add_argument("expression")
    parse_cmd.add_argument("--format", choices=["text", "json", "csv"], default="text")

    validate_cmd = sub.add_parser("validate", help="Validate a UBY expression")
    validate_cmd.add_argument("expression")
    validate_cmd.add_argument("--format", choices=["text", "json", "csv"], default="text")

    fmt = sub.add_parser("format", help="Reformat a UBY expression")
    fmt_sub = fmt.add_subparsers(dest="kind", required=True)

    fmt_full = fmt_sub.add_parser("full")
    fmt_full.add_argument("expression")
    _add_common_output_options(fmt_full)

    fmt_magnitude = fmt_sub.add_parser("magnitude")
    fmt_magnitude.add_argument("expression")
    fmt_magnitude.add_argument("--digits", type=int, default=4)
    _add_common_output_options(fmt_magnitude)

    fmt_scientific = fmt_sub.add_parser("scientific")
    fmt_scientific.add_argument("expression")
    fmt_scientific.add_argument("--digits", type=int, default=3)
    _add_common_output_options(fmt_scientific)

    lint = sub.add_parser("lint", help="Lint UBY expressions in documents")
    lint_sub = lint.add_subparsers(dest="kind", required=True)

    lint_spec = lint_sub.add_parser("spec", help="Lint UBY expressions in a Markdown specification document")
    lint_spec.add_argument("path")
    lint_spec.add_argument("--format", choices=["text", "json", "csv"], default="text")
    lint_spec.add_argument("--allow-missing-spec", action="store_true")

    cross_join = sub.add_parser(
        "cross-join",
        help="Execute the §19 cross-domain proximity JOIN on a UBY SQLite database",
    )
    cross_join.add_argument("--db", required=True, help="Path to a SQLite database with the uby_events table")
    cross_join.add_argument("--cat-a", required=True, help="event_category for set A")
    cross_join.add_argument("--cat-b", required=True, help="event_category for set B")
    cross_join.add_argument("--tau", type=float, required=True, help="Proximity threshold in Julian years")
    cross_join.add_argument("--limit", type=int, default=0, help="Cap the number of returned pairs (0 = unlimited)")
    cross_join.add_argument("--format", choices=["text", "json", "csv"], default="text")

    null_test = sub.add_parser(
        "null-test",
        help="Execute the §20 Monte Carlo permutation test on a cross-domain alignment",
    )
    null_test.add_argument("--db", required=True, help="Path to a SQLite database with the uby_events table")
    null_test.add_argument("--cat-a", required=True, help="event_category for set A")
    null_test.add_argument("--cat-b", required=True, help="event_category for set B")
    null_test.add_argument("--tau", type=float, required=True, help="Proximity threshold in Julian years")
    null_test.add_argument("--n-mc", type=int, default=1000, help="Monte Carlo iterations (default: 1000)")
    null_test.add_argument("--seed", type=int, default=None, help="Random seed for reproducibility")
    null_test.add_argument("--format", choices=["text", "json", "csv"], default="text")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.cmd == "convert":
        include_spec = not args.no_spec

        if args.kind == "iso":
            uby = iso_to_uby(args.value, model_version=args.model, uby_version=args.spec)
            _display_uby(uby, output_format=args.format, include_spec=include_spec)
            return 0

        if args.kind == "jd":
            uby = jd_to_uby(args.value, model_version=args.model, uby_version=args.spec)
            _display_uby(uby, output_format=args.format, include_spec=include_spec)
            return 0

        if args.kind == "year":
            uby = astronomical_year_to_uby(
                args.value,
                model_version=args.model,
                include_model=args.include_model,
                uby_version=args.spec,
            )
            academic_mnemonic = format_academic_mnemonic(args.value, model_version=args.model, uby_version=args.spec, include_spec=include_spec)
            _display_uby(
                uby,
                output_format=args.format,
                include_spec=include_spec,
                extra_fields={"academic_mnemonic": academic_mnemonic} if args.format in {"json", "csv"} else None,
            )
            if args.format == "text":
                print(f"academic_mnemonic={academic_mnemonic}")
            return 0

        if args.kind == "bc":
            astronomical_year = 1 - args.value
            uby = bc_year_to_uby(
                args.value,
                model_version=args.model,
                include_model=args.include_model,
                uby_version=args.spec,
            )
            academic_mnemonic = format_academic_mnemonic(astronomical_year, model_version=args.model, uby_version=args.spec, include_spec=include_spec)
            _display_uby(
                uby,
                output_format=args.format,
                include_spec=include_spec,
                extra_fields={"academic_mnemonic": academic_mnemonic} if args.format in {"json", "csv"} else None,
            )
            if args.format == "text":
                print(f"academic_mnemonic={academic_mnemonic}")
            return 0

    if args.cmd == "redshift":
        include_spec = not args.no_spec
        uby = redshift_to_uby(
            args.z,
            cosmology_name=args.cosmology,
            model_version=args.model,
            uby_version=args.spec,
        )
        if args.format in {"json", "csv"}:
            _print_payload(to_dict(uby), output_format=args.format)
        else:
            print(format_magnitude(uby, include_spec=include_spec))
            print(f"precision_level={uby.precision_level.value}")
            print(f"note={uby.propagation_note}")
        return 0

    if args.cmd == "reverse":
        if args.kind == "jd":
            print(uby_to_jd(args.value))
            return 0
        if args.kind == "iso":
            print(uby_to_iso(args.value))
            return 0

    if args.cmd == "parse":
        parsed = parse_uby_expression(args.expression)
        if args.format in {"json", "csv"}:
            _print_payload(
                {
                    "notation": parsed.notation,
                    "uby_value": str(parsed.uby_value),
                    "model_version": parsed.model_version,
                    "uby_version": parsed.uby_version,
                    "precision_level": parsed.precision_level.value if parsed.precision_level else None,
                    "mnemonic_prefix": parsed.mnemonic_prefix,
                    "warnings": parsed.warnings,
                    "raw": parsed.raw,
                },
                output_format=args.format,
            )
        else:
            print(f"notation={parsed.notation}")
            print(f"uby_value={parsed.uby_value}")
            print(f"model_version={parsed.model_version}")
            print(f"uby_version={parsed.uby_version}")
            if parsed.mnemonic_prefix is not None:
                print(f"mnemonic_prefix={parsed.mnemonic_prefix}")
            if parsed.warnings:
                print("warnings=" + ",".join(parsed.warnings))
        return 0

    if args.cmd == "validate":
        parsed = parse_uby_expression(args.expression)
        uby = _parsed_to_uby(parsed)
        messages = validate_uby_time(uby)

        # Include parser warnings in validation output.
        for warning in parsed.warnings:
            if warning not in {message.code for message in messages}:
                messages.append(ValidationMessage(warning, "warning", warning))

        if args.format in {"json", "csv"}:
            rows = [
                {"code": message.code, "level": message.level, "message": message.message}
                for message in messages
            ]
            if args.format == "csv" and not rows:
                _print_csv_rows([], fieldnames=["code", "level", "message"])
            else:
                _print_payload(rows, output_format=args.format)
        else:
            if not messages:
                print("ok")
            for msg in messages:
                print(f"{msg.level}:{msg.code}:{msg.message}")
        return 0

    if args.cmd == "format":
        include_spec = not args.no_spec
        parsed = parse_uby_expression(args.expression)
        uby = _parsed_to_uby(parsed)

        if args.kind == "full":
            print(format_full(uby, include_spec=include_spec))
            return 0
        if args.kind == "magnitude":
            print(format_magnitude(uby, digits=args.digits, include_spec=include_spec))
            return 0
        if args.kind == "scientific":
            print(format_scientific(uby, significant_digits=args.digits, include_spec=include_spec))
            return 0

    if args.cmd == "lint":
        if args.kind == "spec":
            issues = lint_uby_expressions_in_file(
                args.path,
                require_spec=not args.allow_missing_spec,
            )
            if args.format in {"json", "csv"}:
                rows = lint_issues_to_dicts(issues)
                if args.format == "csv" and not rows:
                    _print_csv_rows([], fieldnames=["level", "line", "column", "code", "expression", "message"])
                else:
                    _print_payload(rows, output_format=args.format)
            else:
                if not issues:
                    print("ok")
                for issue in issues:
                    print(
                        f"{issue.level}:{issue.line}:{issue.column}:"
                        f"{issue.code}:{issue.expression}:{issue.message}"
                    )
            return 1 if any(issue.level == "error" for issue in issues) else 0

    if args.cmd == "cross-join":
        result = cross_domain_join(
            args.db,
            cat_a=args.cat_a,
            cat_b=args.cat_b,
            tau_years=args.tau,
        )
        pairs = result.pairs if args.limit <= 0 else result.pairs[: args.limit]
        if args.format == "json":
            payload = {
                "cat_a": result.cat_a,
                "cat_b": result.cat_b,
                "tau": result.tau,
                "pair_count": len(result.pairs),
                "returned_pair_count": len(pairs),
                "null_test_result": result.null_test_result,
                "pairs": [pair.to_dict() for pair in pairs],
            }
            print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))
        elif args.format == "csv":
            fieldnames = [
                "a_event_id", "b_event_id", "a_event_name", "b_event_name",
                "a_event_category", "b_event_category",
                "a_uby_value", "b_uby_value", "delta",
                "a_uby_precision_level", "b_uby_precision_level", "tau",
            ]
            _print_csv_rows([pair.to_dict() for pair in pairs], fieldnames=fieldnames)
        else:
            print(f"cat_a={result.cat_a}")
            print(f"cat_b={result.cat_b}")
            print(f"tau={result.tau}")
            print(f"pair_count={len(result.pairs)}")
            print(f"null_test_result={result.null_test_result}")
            for pair in pairs:
                print(
                    f"pair: a={pair.a_event_name} ({pair.a_event_category} "
                    f"L{pair.a_uby_precision_level}) "
                    f"b={pair.b_event_name} ({pair.b_event_category} "
                    f"L{pair.b_uby_precision_level}) "
                    f"delta={pair.delta:.6g}"
                )
        return 0

    if args.cmd == "null-test":
        import random as _random
        rng = _random.Random(args.seed) if args.seed is not None else None
        result = null_hypothesis_test(
            args.db,
            cat_a=args.cat_a,
            cat_b=args.cat_b,
            tau_years=args.tau,
            n_mc=args.n_mc,
            rng=rng,
        )
        payload = result.to_dict()
        if args.format == "json":
            print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))
        elif args.format == "csv":
            _print_csv_rows([payload])
        else:
            for key, value in payload.items():
                print(f"{key}={value}")
        return 0

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
