"""Validate synthetic MEH evidence records without treating validity as truth."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

_TEXT_FIELDS = ("evidence_id", "recorded_at", "source", "revision", "method")
_CLAIM_FIELDS = ("observations", "self_reports", "inferences", "unknowns", "alternatives", "limitations")
_RECORD_FIELDS = frozenset((*_TEXT_FIELDS, *_CLAIM_FIELDS))
DEFAULT_MAX_LINE_BYTES = 1_048_576


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    """Build an object while refusing ambiguous repeated member names."""
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate object key: {key}")
        result[key] = value
    return result


def validate_record(record: Any) -> list[str]:
    """Return structural errors; schema validity does not establish truth."""
    if not isinstance(record, dict):
        return ["record must be a JSON object"]
    errors = []
    extra_fields = sorted(record.keys() - _RECORD_FIELDS)
    if extra_fields:
        errors.append(f"unexpected fields: {extra_fields!r}")
    for field in _TEXT_FIELDS:
        value = record.get(field)
        if not isinstance(value, str) or not value.strip():
            errors.append(f"{field} must be a non-empty string")
    for field in _CLAIM_FIELDS:
        value = record.get(field)
        if not isinstance(value, list):
            errors.append(f"{field} must be an array of strings")
        elif any(not isinstance(item, str) or not item.strip() for item in value):
            errors.append(f"{field} entries must be non-empty strings")
    return errors


def validate_jsonl(path: Path, max_line_bytes: int = DEFAULT_MAX_LINE_BYTES) -> list[str]:
    """Validate bounded JSONL lines and return line-numbered diagnostics."""
    if isinstance(max_line_bytes, bool) or not isinstance(max_line_bytes, int) or max_line_bytes <= 0:
        return ["max_line_bytes must be a positive integer"]
    errors = []
    try:
        with path.open("rb") as stream:
            line_number = 0
            while line := stream.readline(max_line_bytes + 1):
                line_number += 1
                if len(line) > max_line_bytes:
                    errors.append(f"line {line_number}: exceeds maximum size of {max_line_bytes} bytes")
                    if not line.endswith(b"\n"):
                        while chunk := stream.readline(64 * 1024):
                            if chunk.endswith(b"\n"):
                                break
                    continue
                try:
                    text = line.decode("utf-8")
                except UnicodeDecodeError as exc:
                    errors.append(f"line {line_number}: invalid UTF-8 at byte {exc.start}")
                    continue
                if not text.strip():
                    continue
                try:
                    record = json.loads(text, object_pairs_hook=_reject_duplicate_keys)
                except json.JSONDecodeError as exc:
                    errors.append(f"line {line_number}: invalid JSON: {exc.msg}")
                    continue
                except ValueError as exc:
                    errors.append(f"line {line_number}: invalid JSON: {exc}")
                    continue
                errors.extend(f"line {line_number}: {error}" for error in validate_record(record))
    except OSError as exc:
        errors.append(f"cannot read {path}: {exc}")
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("file", type=Path, help="JSONL file of evidence records")
    parser.add_argument("--max-line-bytes", type=int, default=DEFAULT_MAX_LINE_BYTES,
                        help=f"maximum encoded size per input line (default: {DEFAULT_MAX_LINE_BYTES})")
    args = parser.parse_args(argv)
    errors = validate_jsonl(args.file, args.max_line_bytes)
    if errors:
        print("\n".join(errors))
        return 1
    print(f"OK: {args.file} contains structurally valid evidence records")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
