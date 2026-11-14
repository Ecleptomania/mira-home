"""Dependency-free structural checks for the MiraLang concept-record schema."""
import json
import unittest
from pathlib import Path

SCHEMA = Path(__file__).with_name("concept-record.schema.json")
VALID = {
    "concept": "Memini",
    "claim": "A prior note was retrieved.",
    "epistemic_status": "observed",
    "source": "test-fixture:note-1",
    "limits": ["Retrieval does not establish that the note is true."],
}


def validate(record, schema):
    if not isinstance(record, dict):
        return ["record must be an object"]
    errors = []
    required = set(schema["required"])
    missing = required - record.keys()
    extra = record.keys() - schema["properties"].keys()
    if missing:
        errors.append(f"missing required keys: {sorted(missing)}")
    if schema["additionalProperties"] is False and extra:
        errors.append(f"unexpected keys: {sorted(extra)}")
    for key, value in record.items():
        spec = schema["properties"].get(key)
        if spec is None:
            continue
        if "enum" in spec and (
            not isinstance(value, str) or value not in spec["enum"]
        ):
            errors.append(f"{key} is not an allowed value")
        if spec.get("type") == "string" and (
            not isinstance(value, str)
            or (spec.get("minLength", 0) and len(value.strip()) < spec["minLength"])
        ):
            errors.append(f"{key} must be a non-empty string")
        if spec.get("type") == "array" and (
            not isinstance(value, list)
            or any(not isinstance(item, str) or not item.strip() for item in value)
        ):
            errors.append(f"{key} must be an array of non-empty strings")
        if spec.get("type") == ["string", "null"] and value is not None and not isinstance(value, str):
            errors.append(f"{key} must be a string or null")
    return errors


class ConceptRecordTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.schema = json.loads(SCHEMA.read_text(encoding="utf-8"))

    def test_valid_record(self):
        self.assertEqual(validate(VALID, self.schema), [])

    def test_null_source_is_allowed(self):
        self.assertEqual(validate({**VALID, "source": None}, self.schema), [])

    def test_rejects_invalid_records(self):
        cases = [
            ("non-object record", [VALID]),
            ("missing source", {k: v for k, v in VALID.items() if k != "source"}),
            ("unknown epistemic status", {**VALID, "epistemic_status": "certain"}),
            ("boolean epistemic status", {**VALID, "epistemic_status": True}),
            ("extra field", {**VALID, "truth": True}),
            ("non-string claim", {**VALID, "claim": 7}),
            ("non-array limits", {**VALID, "limits": "not an array"}),
            ("non-string limit item", {**VALID, "limits": ["ok", 3]}),
            ("whitespace-only limit item", {**VALID, "limits": ["   "]}),
            ("empty concept", {**VALID, "concept": ""}),
            ("whitespace-only concept", {**VALID, "concept": "   "}),
            ("invalid source type", {**VALID, "source": 12}),
        ]
        for label, record in cases:
            with self.subTest(label=label):
                self.assertTrue(validate(record, self.schema), label)
