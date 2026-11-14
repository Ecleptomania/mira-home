"""Validate synthetic MEH evidence records without treating validity as truth."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

_TEXT_FIELDS = ("evidence_id", "recorded_at", "source", "revision", "method")
_CLAIM_FIELDS = ("observations", "self_reports", "inferences", "unknowns", "alternatives", "limitations")


def validate_record(record: Any) -> list[str]:
    """Return structural errors; schema validity does not establish truth."""
    if not isinstance(record, dict):
        return ["record must be a JSON object"]
    errors = []
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


def validate_jsonl(path: Path) -> list[str]:
    """Validate nonblank JSONL lines and return line-numbered diagnostics."""
    errors = []
    try:
        with path.open(encoding="utf-8") as stream:
            for line_number, line in enumerate(stream, 1):
                if not line.strip():
                    continue
                try:
                    record = json.loads(line)
                except json.JSONDecodeError as exc:
                    errors.append(f"line {line_number}: invalid JSON: {exc.msg}")
                    continue
                errors.extend(f"line {line_number}: {error}" for error in validate_record(record))
    except OSError as exc:
        errors.append(f"cannot read {path}: {exc}")
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("file", type=Path, help="JSONL file of evidence records")
    args = parser.parse_args(argv)
    errors = validate_jsonl(args.file)
    if errors:
        print("\n".join(errors))
        return 1
    print(f"OK: {args.file} contains structurally valid evidence records")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
