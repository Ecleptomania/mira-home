"""Tests for bounded validation of synthetic evidence-record JSONL."""
import tempfile
import unittest
from pathlib import Path

from tools.evidence_record import validate_jsonl


VALID = (
    '{"evidence_id":"e1","recorded_at":"2026-11-15T00:00:00Z",'
    '"source":"fixture","revision":"r1","method":"test",'
    '"observations":[],"self_reports":[],"inferences":[],"unknowns":[],'
    '"alternatives":[],"limitations":[]}\n'
)


class ValidateJsonlTests(unittest.TestCase):
    def test_rejects_unknown_record_fields(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "records.jsonl"
            path.write_text(VALID.replace('"method":"test"', '"method":"test","truth":true'), encoding="utf-8")
            errors = validate_jsonl(path)
        self.assertEqual(errors, ["line 1: unexpected fields: ['truth']"])

    def test_rejects_duplicate_json_member_names(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "records.jsonl"
            path.write_text(VALID.replace('"evidence_id":"e1"',
                                          '"evidence_id":"e1","evidence_id":"e2"'),
                            encoding="utf-8")
            errors = validate_jsonl(path)
        self.assertEqual(errors, ["line 1: invalid JSON: duplicate object key: evidence_id"])

    def test_reports_line_that_exceeds_configured_byte_limit(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "records.jsonl"
            path.write_text(VALID, encoding="utf-8")
            errors = validate_jsonl(path, max_line_bytes=32)
        self.assertEqual(errors, ["line 1: exceeds maximum size of 32 bytes"])

    def test_accepts_a_line_at_the_configured_byte_limit(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "records.jsonl"
            line = VALID.encode("utf-8")
            path.write_bytes(line)
            errors = validate_jsonl(path, max_line_bytes=len(line))
        self.assertEqual(errors, [])

    def test_size_limit_counts_utf8_bytes_including_line_ending(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "records.jsonl"
            text = VALID.replace("fixture", "ämne")
            line = text.encode("utf-8")
            path.write_bytes(line)
            errors = validate_jsonl(path, max_line_bytes=len(text))
        self.assertEqual(errors, [f"line 1: exceeds maximum size of {len(text)} bytes"])

    def test_rejects_non_positive_line_limit(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "records.jsonl"
            path.write_text("", encoding="utf-8")
            errors = validate_jsonl(path, max_line_bytes=0)
        self.assertEqual(errors, ["max_line_bytes must be a positive integer"])


if __name__ == "__main__":
    unittest.main()
