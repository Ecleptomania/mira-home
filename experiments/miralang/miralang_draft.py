"""Standalone, explicitly non-canonical MiraLang draft primitives (stdlib only)."""
from __future__ import annotations
import hashlib
import json
import math
import re
from typing import Any

SURFACE_VERSION = "0.4-draft"
ASSESSMENT_KINDS = {"SUPPORT_CHECK", "CONTRADICTION_CHECK", "CONSISTENCY_CHECK", "FRESHNESS_CHECK", "SUFFICIENCY_CHECK"}
SURFACE_RECORDS = {"GOAL": "Goal", "SOURCE": "Source", "CHECKPOINT": "Checkpoint", "TASK": "Task", "ACTOR": "Actor", "ROLE": "Role", "RUNTIME_BINDING": "RuntimeBinding", "ASSIGNMENT": "Assignment", "EVIDENCE": "Evidence", "CLAIM": "Claim", "PROPOSAL": "Proposal", "ASSESSMENT_CRITERIA": "AssessmentCriteria"}
RECORD_KEYWORD = {value: key for key, value in SURFACE_RECORDS.items()}
REQUEST_ID_RE = re.compile(r"^[A-Za-z0-9._:-]{1,128}$")

RECORD_REQUIRED = {
    "Goal": {"statement", "provenance_refs"},
    "Source": {"source_kind", "locator_digest", "observed_at", "epistemic_source", "freshness"},
    "Checkpoint": {"task_ref", "base_task_revision", "payload_digest", "completeness", "freshness", "verification_ref", "provenance_refs"},
    "Task": {"objective", "scope", "acceptance", "lifecycle_state", "continuation_policy", "goal_refs", "checkpoint_refs", "provenance_refs", "state_receipt_ref", "completion_verification_ref"},
    "Actor": {"actor_class", "provenance_refs"},
    "Role": {"role_name", "scope", "provenance_refs"},
    "RuntimeBinding": {"provider", "session_ref", "lifecycle_observation", "provenance_refs"},
    "Assignment": {"task_ref", "actor_ref", "runtime_binding_ref", "role_ref", "status", "provenance_refs"},
    "Evidence": {"source_ref", "content_digest", "content_ref", "captured_at", "validation_state", "verification_ref", "provenance_refs"},
    "Claim": {"subject_ref", "proposition", "basis_refs", "epistemic_source", "validation_state", "verification_ref", "provenance_refs"},
    "Proposal": {"target_ref", "base_revision", "delta", "reason", "basis_refs", "proposal_state"},
    "AssessmentCriteria": {"assessment_kind", "criteria_digest", "criteria_ref", "provenance_refs"},
}
ENUMS = {
    "lifecycle_state": {"DRAFT", "QUEUED", "ACTIVE", "WAITING", "INTERRUPTED", "BLOCKED", "UNCERTAIN", "COMPLETED", "CANCELLED"},
    "continuation_policy": {"MANUAL_ONLY", "REAUTHORIZE_BEFORE_EFFECT", "NO_AUTO_EFFECT"},
    "freshness": {"FRESH", "STALE", "UNKNOWN"},
    "completeness": {"COMPLETE", "PARTIAL", "UNKNOWN"},
    "validation_state": {"UNVERIFIED", "VERIFIED", "STALE", "CONFLICTED", "UNKNOWN"},
    "proposal_state": {"PROPOSED"},
    "lifecycle_observation": {"OBSERVED_LIVE", "OBSERVED_ENDED", "OBSERVED_LOST", "REPORTED", "UNKNOWN"},
    "status": {"PROPOSED", "ACTIVE", "ENDED", "LOST", "UNKNOWN"},
    "actor_class": {"SEMANTIC", "WORKER", "VERIFIER"},
    "source_kind": {"USER_MESSAGE", "TOOL_OBSERVATION", "TOOL_RECEIPT", "MODEL_OUTPUT", "ARCHIVE", "OTHER"},
    "epistemic_source": {"REPORTED", "OBSERVED", "INFERRED", "PROPOSED", "RETRIEVED"},
    "assessment_kind": ASSESSMENT_KINDS,
}
REF_FIELDS = {
    "Goal": {"provenance_refs": "Source"}, "Source": {},
    "Checkpoint": {"task_ref": "Task", "verification_ref": "VerificationReceiptRef", "provenance_refs": "Source"},
    "Task": {"goal_refs": "Goal", "checkpoint_refs": "Checkpoint", "provenance_refs": "Source", "state_receipt_ref": "CommitReceiptRef", "completion_verification_ref": "VerificationReceiptRef"},
    "Actor": {"provenance_refs": "Source"}, "Role": {"provenance_refs": "Source"},
    "RuntimeBinding": {"session_ref": "Session", "provenance_refs": "Source"},
    "Assignment": {"task_ref": "Task", "actor_ref": "Actor", "runtime_binding_ref": "RuntimeBinding", "role_ref": "Role", "provenance_refs": "Source"},
    "Evidence": {"source_ref": "Source", "content_ref": "EvidenceBlob", "verification_ref": "VerificationReceiptRef", "provenance_refs": "Source"},
    "Claim": {"subject_ref": None, "basis_refs": "Evidence", "verification_ref": "VerificationReceiptRef", "provenance_refs": "Source"},
    "Proposal": {"target_ref": None, "basis_refs": "Evidence"},
    "AssessmentCriteria": {"criteria_ref": "CriteriaArtifact", "provenance_refs": "Source"},
}

def _identity(ref):
    _validate_ref(ref)
    return ref["kind"], ref["id"], ref["revision"]

def validate_bundle_structure(bundle: dict) -> dict:
    """Validate draft shape, typed local refs and declarations; no external resolution."""
    if not isinstance(bundle, dict) or set(bundle) != {"manifest", "records"}:
        raise MiraLangError("bundle must contain exactly manifest and records")
    manifest, records = bundle["manifest"], bundle["records"]
    manifest_fields = {"bundle_id", "schema_version", "semantics_version", "canonicalization_version", "root_refs", "external_refs", "extensions", "producer_ref", "canonical_digest"}
    required_manifest = {"bundle_id", "schema_version", "semantics_version", "canonicalization_version", "root_refs", "external_refs", "extensions"}
    if not isinstance(manifest, dict) or required_manifest - set(manifest) or set(manifest) - manifest_fields:
        raise MiraLangError("manifest field set invalid")
    for key in ("bundle_id", "schema_version", "semantics_version", "canonicalization_version"):
        if not isinstance(manifest[key], str) or not manifest[key]: raise MiraLangError(f"manifest {key} must be nonempty text")
    if manifest["canonicalization_version"] != CANON_VERSION: raise MiraLangError("unsupported canonicalization profile")
    if not isinstance(manifest["extensions"], dict): raise MiraLangError("manifest extensions must be an object")
    if any(not isinstance(key, str) or ":" not in key for key in manifest["extensions"]): raise MiraLangError("manifest extension keys must be namespaced")
    if manifest.get("canonical_digest") is not None and (not isinstance(manifest["canonical_digest"], str) or re.fullmatch(r"sha256:[0-9a-f]{64}", manifest["canonical_digest"]) is None): raise MiraLangError("canonical_digest must be sha256:<64 lowercase hex>")
    if not isinstance(records, list): raise MiraLangError("records must be an array")
    local = {}
    for record in records:
        if not isinstance(record, dict): raise MiraLangError("record must be an object")
        kind = record.get("kind")
        if kind not in RECORD_REQUIRED: raise MiraLangError("unknown record kind")
        required = RECORD_REQUIRED[kind] | {"kind", "id", "revision"}
        allowed = required | {"extensions"}
        if required - set(record) or set(record) - allowed: raise MiraLangError(f"{kind} record fields invalid")
        if not isinstance(record["id"], str) or not record["id"] or not isinstance(record["revision"], int) or isinstance(record["revision"], bool) or record["revision"] < 1: raise MiraLangError("record identity invalid")
        if "extensions" in record:
            if not isinstance(record["extensions"], dict): raise MiraLangError("record extensions must be object")
            if any(not isinstance(key, str) or ":" not in key for key in record["extensions"]): raise MiraLangError("record extension keys must be namespaced")
        identity = (kind, record["id"], record["revision"])
        if identity in local: raise MiraLangError("duplicate local record identity")
        local[identity] = record
        text_fields = {"statement", "source_kind", "locator_digest", "observed_at", "epistemic_source", "freshness", "payload_digest", "completeness", "objective", "lifecycle_state", "continuation_policy", "actor_class", "role_name", "provider", "lifecycle_observation", "status", "content_digest", "captured_at", "validation_state", "proposition", "proposal_state", "reason", "assessment_kind", "criteria_digest"}
        for field in text_fields & set(record):
            if not isinstance(record[field], str) or not record[field].strip(): raise MiraLangError(f"{kind}.{field} must be nonblank text")
        list_fields = {"provenance_refs", "goal_refs", "checkpoint_refs", "acceptance", "basis_refs"}
        for field in list_fields & set(record):
            if not isinstance(record[field], list): raise MiraLangError(f"{kind}.{field} must be an array")
        for field in ("scope", "delta"):
            if field in record and not isinstance(record[field], dict): raise MiraLangError(f"{kind}.{field} must be an object")
        for field, allowed_values in ENUMS.items():
            if field in record and record[field] not in allowed_values: raise MiraLangError(f"unknown {field}")
        for field in ("base_task_revision", "base_revision"):
            if field in record and (not isinstance(record[field], int) or isinstance(record[field], bool) or record[field] < 0): raise MiraLangError(f"{kind}.{field} must be a nonnegative integer")
        if "scope" in record:
            scope = record["scope"]
            if set(scope) != {"include", "exclude"} or any(not isinstance(scope[key], list) or any(not isinstance(item, str) for item in scope[key]) for key in ("include", "exclude")):
                raise MiraLangError(f"{kind}.scope must contain include/exclude string arrays")
        if "acceptance" in record and any(not isinstance(item, str) for item in record["acceptance"]): raise MiraLangError("Task.acceptance must be a string array")
        if "criteria_digest" in record and re.fullmatch(r"sha256:[0-9a-f]{64}", record["criteria_digest"]) is None: raise MiraLangError("AssessmentCriteria.criteria_digest invalid")
    external = set()
    roots = set()
    for field, sink in (("root_refs", roots), ("external_refs", external)):
        if not isinstance(manifest[field], list): raise MiraLangError(f"{field} must be an array")
        for ref in manifest[field]:
            identity = _identity(ref)
            if identity in sink: raise MiraLangError(f"duplicate identity in {field}")
            sink.add(identity)
    if roots & external: raise MiraLangError("root and external declarations overlap")
    if external & set(local): raise MiraLangError("external declaration shadows local record")
    if not roots <= set(local): raise MiraLangError("root reference must resolve to a local record")
    if manifest.get("producer_ref") is not None: _identity(manifest["producer_ref"])
    for record in records:
        kind = record["kind"]
        for field, expected_kind in REF_FIELDS[kind].items():
            value = record[field]
            if value is None and field in {"verification_ref", "state_receipt_ref", "completion_verification_ref", "role_ref"}: continue
            is_list = field.endswith("_refs")
            values = value if is_list else [value]
            if is_list and not isinstance(values, list): raise MiraLangError(f"{kind}.{field} must be an array")
            for ref in values:
                _identity(ref)
                if expected_kind is not None and ref["kind"] != expected_kind: raise MiraLangError(f"{kind}.{field} reference kind mismatch")
                identity = _identity(ref)
                if identity not in local and identity not in external: raise MiraLangError(f"{kind}.{field} reference is not declared")
    return {"status": "STRUCTURALLY_VALID_DRAFT", "local_record_count": len(local), "external_declaration_count": len(external), "external_content_resolved": False}


def parse_surface(text: str) -> dict:
    """Parse a bounded line-oriented Surface 0.4 draft. Parser has no effects."""
    if not isinstance(text, str):
        raise MiraLangError("Surface input must be text")
    try:
        encoded = text.encode("utf-8", errors="strict")
    except UnicodeEncodeError as exc:
        raise MiraLangError("Surface input contains a surrogate") from exc
    if len(encoded) > 2_000_000:
        raise MiraLangError("Surface input exceeds byte limit")
    if "\r" in text or "\x00" in text:
        raise MiraLangError("Surface input must use LF lines and contain no NUL")
    lines = text.split("\n")
    if not lines or lines[0] != f"MIRALANG-SURFACE {SURFACE_VERSION}":
        raise MiraLangError("unsupported Surface version")
    manifest = None
    records = []
    request = None
    for line_number, line in enumerate(lines[1:], start=2):
        if not line.strip():
            continue
        if line.startswith("BUNDLE "):
            if manifest is not None or records or request is not None:
                raise MiraLangError("BUNDLE must occur once before records/request")
            manifest = strict_json_loads(line[len("BUNDLE "):], max_bytes=1_000_000)
            if not isinstance(manifest, dict):
                raise MiraLangError("BUNDLE payload must be an object")
            continue
        if manifest is None:
            raise MiraLangError("BUNDLE is required before statements")
        if line.startswith("REQUEST "):
            if request is not None:
                raise MiraLangError("at most one REQUEST is allowed")
            parts = line.split(" ", 3)
            if len(parts) != 4 or parts[1] not in OPERATOR_ARGS or not REQUEST_ID_RE.fullmatch(parts[2]) or not parts[3]:
                raise MiraLangError("invalid REQUEST syntax")
            args = strict_json_loads(parts[3], max_bytes=256_000)
            validate_request_shape(parts[1], args)
            request = {"request_id": parts[2], "operator": parts[1], "args": args}
            continue
        if request is not None:
            raise MiraLangError("record statements must precede REQUEST")
        parts = line.split(" ", 1)
        if len(parts) != 2 or parts[0] not in SURFACE_RECORDS:
            raise MiraLangError(f"unknown statement at line {line_number}")
        body = strict_json_loads(parts[1], max_bytes=256_000)
        if not isinstance(body, dict) or "kind" in body:
            raise MiraLangError("record body must be an object without kind")
        records.append({"kind": SURFACE_RECORDS[parts[0]], **body})
    if manifest is None:
        raise MiraLangError("BUNDLE is required")
    parsed = {"surface_version": SURFACE_VERSION, "bundle": {"manifest": manifest, "records": records}, "request": None}
    validate_bundle_structure(parsed["bundle"])
    if request is not None:
        for field in ("bundle_id", "schema_version", "semantics_version"):
            request[field] = manifest.get(field)
        request["request_fingerprint"] = request_fingerprint(request, manifest, parsed["bundle"])
        parsed["request"] = request
        validate_parsed_request_binding(parsed)
    else:
        bundle_digest(parsed["bundle"])
    return parsed

def render_surface(parsed: dict) -> str:
    """Render this draft AST deterministically; no semantic effects."""
    if not isinstance(parsed, dict) or parsed.get("surface_version") != SURFACE_VERSION:
        raise MiraLangError("unsupported parsed Surface object")
    if set(parsed) != {"surface_version", "bundle", "request"}:
        raise MiraLangError("parsed Surface object fields invalid")
    bundle = parsed.get("bundle")
    if not isinstance(bundle, dict) or set(bundle) != {"manifest", "records"}:
        raise MiraLangError("parsed bundle shape invalid")
    validate_bundle_structure(bundle)
    manifest = bundle["manifest"]
    lines = [f"MIRALANG-SURFACE {SURFACE_VERSION}", "BUNDLE " + canonical_json_bytes(manifest).decode("utf-8")]
    for record in sorted(bundle["records"], key=lambda item: (item.get("kind", ""), item.get("id", ""), item.get("revision", 0))):
        if not isinstance(record, dict) or "kind" not in record:
            raise MiraLangError("record kind required")
        keyword = RECORD_KEYWORD.get(record["kind"])
        if keyword is None:
            raise MiraLangError("unsupported record kind")
        body = {key: value for key, value in record.items() if key != "kind"}
        lines.append(keyword + " " + canonical_json_bytes(body).decode("utf-8"))
    request = parsed.get("request")
    if request is not None:
        validate_parsed_request_binding(parsed)
        lines.append("REQUEST " + request["operator"] + " " + request["request_id"] + " " + canonical_json_bytes(request["args"]).decode("utf-8"))
    return "\n".join(lines)

CANON_VERSION = "MIRAJSON-CANON-0.3-draft"
MAX_SAFE_INTEGER = 2**53 - 1
OPERATOR_ARGS = {
    "MEMINI": {"scope_refs", "query", "max_results", "max_result_bytes"},
    "IUDICO": {"claim_ref", "evidence_refs", "criteria_ref", "assessment_kind"},
    "MUTOR": {"target_ref", "base_revision", "replacement_proposition", "reason", "basis_refs"},
    "CONTINUO": {"task_ref", "checkpoint_ref", "mode"},
}
RESULT_KIND = {"MEMINI": "RetrievalResult", "IUDICO": "AssessmentResult", "MUTOR": "ProposalResult", "CONTINUO": "ContinuationPlan"}
ASSESSMENT_KINDS = {"SUPPORT_CHECK", "CONTRADICTION_CHECK", "CONSISTENCY_CHECK", "FRESHNESS_CHECK", "SUFFICIENCY_CHECK"}

class MiraLangError(ValueError):
    """Malformed or inconsistent local draft input."""

def _pairs_no_duplicates(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise MiraLangError(f"duplicate JSON key: {key!r}")
        result[key] = value
    return result

def _reject_constant(token):
    raise MiraLangError(f"non-JSON numeric constant: {token}")

def strict_json_loads(raw: bytes | str, *, max_bytes: int = 1_048_576) -> Any:
    """Strict UTF-8/JSON parser: duplicate keys, constants and surrogates reject."""
    if isinstance(raw, bytes):
        if len(raw) > max_bytes:
            raise MiraLangError("JSON input exceeds byte limit")
        try:
            text = raw.decode("utf-8", errors="strict")
        except UnicodeDecodeError as exc:
            raise MiraLangError("input is not strict UTF-8") from exc
    elif isinstance(raw, str):
        try:
            encoded = raw.encode("utf-8", errors="strict")
        except UnicodeEncodeError as exc:
            raise MiraLangError("input contains a surrogate code point") from exc
        if len(encoded) > max_bytes:
            raise MiraLangError("JSON input exceeds byte limit")
        text = raw
    else:
        raise MiraLangError("JSON input must be bytes or str")
    try:
        value = json.loads(text, object_pairs_hook=_pairs_no_duplicates, parse_constant=_reject_constant)
    except MiraLangError:
        raise
    except (json.JSONDecodeError, UnicodeError, ValueError, RecursionError) as exc:
        raise MiraLangError("invalid JSON") from exc
    try:
        _validate_exact_tree(value)
    except RecursionError as exc:
        raise MiraLangError("JSON nesting exceeds supported depth") from exc
    return value

def _validate_exact_tree(value: Any) -> Any:
    if value is None or isinstance(value, bool):
        return value
    if isinstance(value, int):
        if abs(value) > MAX_SAFE_INTEGER:
            raise MiraLangError("integer exceeds interoperable safe range")
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            raise MiraLangError("non-finite number")
        raise MiraLangError("floating-point numbers are not in this draft profile")
    if isinstance(value, str):
        if any(0xD800 <= ord(char) <= 0xDFFF for char in value):
            raise MiraLangError("surrogate code point is not a Unicode scalar")
        return value
    if isinstance(value, list):
        for item in value:
            _validate_exact_tree(item)
        return value
    if isinstance(value, dict):
        for key, item in value.items():
            if not isinstance(key, str) or not key.isascii():
                raise MiraLangError("object keys must be ASCII in this draft profile")
            _validate_exact_tree(item)
        return value
    raise MiraLangError(f"unsupported JSON value: {type(value).__name__}")

def _ref_key(ref):
    if not isinstance(ref, dict):
        return ("", "", 0)
    return (ref.get("kind", ""), ref.get("id", ""), ref.get("revision", 0))

def canonical_bundle_object(bundle: dict) -> dict:
    """Return canonicalizable copy; arrays of refs/records have deterministic order."""
    _validate_exact_tree(bundle)
    if not isinstance(bundle, dict) or set(bundle) != {"manifest", "records"} or not isinstance(bundle["manifest"], dict) or not isinstance(bundle["records"], list):
        raise MiraLangError("bundle must have exactly manifest and records")
    out = json.loads(json.dumps(bundle, ensure_ascii=False, allow_nan=False))
    for field in ("root_refs", "external_refs"):
        refs = out["manifest"].get(field)
        if refs is not None:
            if not isinstance(refs, list):
                raise MiraLangError(f"manifest {field} must be an array")
            identities = []
            for ref in refs:
                _validate_ref(ref)
                identities.append((ref["kind"], ref["id"], ref["revision"]))
            if len(identities) != len(set(identities)):
                raise MiraLangError(f"duplicate reference identity in {field}")
            refs.sort(key=_ref_key)
    identities = []
    for record in out["records"]:
        if not isinstance(record, dict) or not isinstance(record.get("kind"), str) or not record["kind"] or not isinstance(record.get("id"), str) or not record["id"] or not isinstance(record.get("revision"), int) or isinstance(record.get("revision"), bool) or record["revision"] < 1:
            raise MiraLangError("record requires nonempty kind/id and positive integer revision")
        identities.append((record["kind"], record["id"], record["revision"]))
    if len(identities) != len(set(identities)):
        raise MiraLangError("duplicate local record identity")
    out["records"].sort(key=_ref_key)
    return out

def canonical_json_bytes(value: Any) -> bytes:
    _validate_exact_tree(value)
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")

def bundle_digest(bundle: dict) -> str:
    obj = canonical_bundle_object(bundle)
    obj["manifest"].pop("canonical_digest", None)
    return "sha256:" + hashlib.sha256(canonical_json_bytes(obj)).hexdigest()

def request_fingerprint(request: dict, manifest: dict, bundle: dict, *, surface_version: str = SURFACE_VERSION) -> str:
    """Draft v0.4 request hash: binds versions, request and complete bundle digest."""
    if not isinstance(bundle, dict) or set(bundle) != {"manifest", "records"} or not isinstance(bundle.get("manifest"), dict):
        raise MiraLangError("complete bundle with manifest required")
    if not isinstance(manifest, dict) or manifest != bundle["manifest"]:
        raise MiraLangError("supplied manifest must exactly match complete bundle manifest")
    required_manifest = {"canonicalization_version", "bundle_id", "schema_version", "semantics_version"}
    if not required_manifest <= set(manifest):
        raise MiraLangError("bundle manifest is missing fingerprint fields")
    if not isinstance(request, dict) or not {"request_id", "operator", "args"} <= set(request):
        raise MiraLangError("request is missing fingerprint fields")
    body = {
        "surface_version": surface_version,
        "canonicalization_version": manifest["canonicalization_version"],
        "bundle_id": manifest["bundle_id"],
        "schema_version": manifest["schema_version"],
        "semantics_version": manifest["semantics_version"],
        "bundle_digest": bundle_digest(bundle),
        "request_id": request["request_id"],
        "operator": request["operator"],
        "args": request["args"],
    }
    return "sha256:" + hashlib.sha256(canonical_json_bytes(body)).hexdigest()

def _validate_ref(ref, expected_kind=None):
    if not isinstance(ref, dict) or set(ref) != {"kind", "id", "revision"}:
        raise MiraLangError("reference must have exactly kind, id, revision")
    if not isinstance(ref["kind"], str) or not ref["kind"] or not isinstance(ref["id"], str) or not ref["id"]:
        raise MiraLangError("reference kind/id must be nonempty strings")
    if not isinstance(ref["revision"], int) or isinstance(ref["revision"], bool) or ref["revision"] < 1:
        raise MiraLangError("reference revision must be a positive integer")
    if expected_kind is not None and ref["kind"] != expected_kind:
        raise MiraLangError(f"expected {expected_kind} reference")

def validate_request_shape(operator: str, args: dict) -> None:
    if operator not in OPERATOR_ARGS or not isinstance(args, dict) or set(args) != OPERATOR_ARGS[operator]:
        raise MiraLangError("unknown operator or argument shape mismatch")
    if operator == "MEMINI":
        refs = args["scope_refs"]
        if not isinstance(refs, list) or not 1 <= len(refs) <= 32: raise MiraLangError("MEMINI scope_refs must contain 1..32 refs")
        if not isinstance(args["query"], str) or not args["query"].strip(): raise MiraLangError("MEMINI query must be nonblank text")
        try:
            query_bytes = args["query"].encode("utf-8", errors="strict")
        except UnicodeEncodeError as exc:
            raise MiraLangError("MEMINI query contains a surrogate") from exc
        if len(query_bytes) > 16384: raise MiraLangError("MEMINI query must be <=16384 UTF-8 bytes")
        if not isinstance(args["max_results"], int) or isinstance(args["max_results"], bool) or not 1 <= args["max_results"] <= 50: raise MiraLangError("MEMINI max_results must be 1..50")
        if not isinstance(args["max_result_bytes"], int) or isinstance(args["max_result_bytes"], bool) or not 1 <= args["max_result_bytes"] <= 65536: raise MiraLangError("MEMINI max_result_bytes must be 1..65536")
        for ref in refs: _validate_ref(ref)
    elif operator == "IUDICO":
        _validate_ref(args["claim_ref"], "Claim"); _validate_ref(args["criteria_ref"], "AssessmentCriteria")
        refs = args["evidence_refs"]
        if not isinstance(refs, list) or not 1 <= len(refs) <= 50: raise MiraLangError("IUDICO evidence_refs must contain 1..50 refs")
        for ref in refs: _validate_ref(ref, "Evidence")
        if args["assessment_kind"] not in ASSESSMENT_KINDS: raise MiraLangError("unsupported assessment_kind")
    elif operator == "MUTOR":
        _validate_ref(args["target_ref"], "Claim")
        refs = args["basis_refs"]
        if not isinstance(refs, list) or not 1 <= len(refs) <= 50: raise MiraLangError("MUTOR basis_refs must contain 1..50 refs")
        for ref in refs: _validate_ref(ref, "Evidence")
        if not isinstance(args["base_revision"], int) or isinstance(args["base_revision"], bool) or args["base_revision"] != args["target_ref"]["revision"]: raise MiraLangError("MUTOR target/base revision mismatch")
        for name in ("replacement_proposition", "reason"):
            if not isinstance(args[name], str) or not args[name].strip(): raise MiraLangError(f"MUTOR {name} must be nonblank")
    else:
        _validate_ref(args["task_ref"], "Task")
        if args["checkpoint_ref"] is not None: _validate_ref(args["checkpoint_ref"], "Checkpoint")
        if args["mode"] != "REPORT_ONLY": raise MiraLangError("CONTINUO mode must be REPORT_ONLY")

def _request_refs(request: dict) -> list[dict]:
    args = request["args"]
    op = request["operator"]
    if op == "MEMINI": return list(args["scope_refs"])
    if op == "IUDICO": return [args["claim_ref"], *args["evidence_refs"], args["criteria_ref"]]
    if op == "MUTOR": return [args["target_ref"], *args["basis_refs"]]
    if op == "CONTINUO": return [args["task_ref"]] + ([] if args["checkpoint_ref"] is None else [args["checkpoint_ref"]])
    raise MiraLangError("unknown operator")

def _classify_ref(ref: dict, bundle: dict) -> str:
    identity = (ref["kind"], ref["id"], ref["revision"])
    if identity in {(r["kind"], r["id"], r["revision"]) for r in bundle["records"]}: return "LOCAL_PRESENT"
    if identity in {(r["kind"], r["id"], r["revision"]) for r in bundle["manifest"].get("external_refs", [])}: return "EXTERNAL_DECLARED"
    return "UNKNOWN"

def validate_parsed_request_binding(parsed: dict) -> dict:
    """Check request mirrors and recomputed fingerprint; no authority or resolution."""
    if not isinstance(parsed, dict) or not isinstance(parsed.get("request"), dict) or not isinstance(parsed.get("bundle"), dict):
        raise MiraLangError("parsed request and bundle required")
    bundle, request = parsed["bundle"], parsed["request"]
    bundle_status = validate_bundle_structure(bundle)
    manifest = bundle["manifest"]
    if parsed.get("surface_version") != SURFACE_VERSION:
        raise MiraLangError("surface version mismatch")
    if manifest.get("canonical_digest") is not None and manifest["canonical_digest"] != bundle_digest(bundle):
        raise MiraLangError("manifest canonical_digest mismatch")
    record_ids = []
    for record in bundle["records"]:
        if not isinstance(record, dict) or not isinstance(record.get("kind"), str) or not record["kind"] or not isinstance(record.get("id"), str) or not record["id"] or not isinstance(record.get("revision"), int) or isinstance(record.get("revision"), bool) or record["revision"] < 1:
            raise MiraLangError("malformed local record identity")
        record_ids.append((record["kind"], record["id"], record["revision"]))
    if len(record_ids) != len(set(record_ids)):
        raise MiraLangError("duplicate local record identity")
    declarations = {}
    for field in ("root_refs", "external_refs"):
        refs = manifest.get(field, [])
        if not isinstance(refs, list):
            raise MiraLangError(f"manifest {field} must be an array")
        keys = []
        for ref in refs:
            _validate_ref(ref)
            keys.append((ref["kind"], ref["id"], ref["revision"]))
        if len(keys) != len(set(keys)):
            raise MiraLangError(f"duplicate identity in {field}")
        declarations[field] = set(keys)
    if declarations["root_refs"] & declarations["external_refs"]:
        raise MiraLangError("root_refs and external_refs overlap")
    if declarations["external_refs"] & set(record_ids):
        raise MiraLangError("external_refs shadow a local record")
    if not declarations["root_refs"] <= set(record_ids):
        raise MiraLangError("root_refs must resolve to local record identities")
    for field in ("bundle_id", "schema_version", "semantics_version"):
        if request.get(field) != manifest.get(field): raise MiraLangError(f"request mirror mismatch: {field}")
    if not isinstance(request.get("request_id"), str) or not request["request_id"]: raise MiraLangError("request_id required")
    validate_request_shape(request.get("operator"), request.get("args"))
    record_set = set(record_ids)
    declared_set = declarations["root_refs"] | declarations["external_refs"]
    for ref in _request_refs(request):
        identity = (ref["kind"], ref["id"], ref["revision"])
        if identity not in record_set and identity not in declared_set:
            raise MiraLangError("request reference absent from local records and manifest declarations")
    states = request.get("reference_declaration_states")
    if states is not None:
        if not isinstance(states, dict) or any(not isinstance(k, str) or not isinstance(v, str) for k, v in states.items()):
            raise MiraLangError("reference_declaration_states must be a string map")
        expected_states = {f"{ref['kind']}:{ref['id']}@{ref['revision']}": _classify_ref(ref, bundle) for ref in _request_refs(request)}
        if states != dict(sorted(expected_states.items())):
            raise MiraLangError("reference_declaration_states mismatch")
    expected = request_fingerprint(request, manifest, bundle, surface_version=parsed["surface_version"])
    if request.get("request_fingerprint") != expected: raise MiraLangError("request fingerprint mismatch")
    return {"status": "MATCHED_LOCAL_DRAFT", "request_fingerprint": expected, "bundle_digest": bundle_digest(bundle), "authority": "NOT_CHECKED", "references_resolved": False}


def evaluate_task_continuity(requested_task_ref, checkpoint_task_ref, checkpoint_base_revision, observed_current_task_ref, observed_current_revision):
    """Task identity/revision comparison only; never authorizes resume or effects."""
    requested = _task_identity(requested_task_ref)
    checkpoint = _task_identity(checkpoint_task_ref)
    observed = _task_identity(observed_current_task_ref)
    base_valid = isinstance(checkpoint_base_revision, int) and not isinstance(checkpoint_base_revision, bool) and checkpoint_base_revision >= 1
    current_valid = isinstance(observed_current_revision, int) and not isinstance(observed_current_revision, bool) and observed_current_revision >= 1
    if requested and observed and requested[:2] != observed[:2]:
        outcome, reason = "FAIL", "REQUESTED_TASK_DIFFERS_FROM_OBSERVED_CURRENT_TASK"
    elif requested and checkpoint and requested[:2] != checkpoint[:2]:
        outcome, reason = "FAIL", "CHECKPOINT_TASK_DIFFERS_FROM_REQUESTED_TASK"
    elif checkpoint and observed and checkpoint[:2] != observed[:2]:
        outcome, reason = "FAIL", "CHECKPOINT_TASK_DIFFERS_FROM_OBSERVED_CURRENT_TASK"
    elif base_valid and current_valid and checkpoint_base_revision != observed_current_revision:
        outcome, reason = "FAIL", "CHECKPOINT_BASE_REVISION_DIFFERS_FROM_CURRENT_REVISION"
    elif not (requested and checkpoint and observed and base_valid and current_valid):
        outcome, reason = "UNKNOWN", "REQUIRED_CONTINUITY_INPUT_MISSING_OR_INVALID"
    elif requested[2] != observed_current_revision or checkpoint[2] != checkpoint_base_revision or observed[2] != observed_current_revision:
        outcome, reason = "FAIL", "TASK_REFERENCE_REVISION_DIFFERS_FROM_OBSERVED_HEAD"
    else:
        outcome, reason = "PASS", "TASK_IDENTITY_AND_REVISION_MATCH_AT_OBSERVATION_POINT"
    return {"outcome": outcome, "reason": reason, "resume_authorized": False, "canonical_commit": False, "atomicity": "POINT_IN_TIME_ONLY", "receipt_authenticity": "NOT_ESTABLISHED"}

def _task_identity(ref):
    if not isinstance(ref, dict) or set(ref) != {"kind", "id", "revision"} or ref.get("kind") != "Task": return None
    if not isinstance(ref.get("id"), str) or not ref["id"] or not isinstance(ref.get("revision"), int) or isinstance(ref.get("revision"), bool) or ref["revision"] < 1: return None
    return ("Task", ref["id"], ref["revision"])

RESULT_FIELDS = {
    "MEMINI": {"request_id", "request_fingerprint", "operator", "semantics_version", "kind", "status", "scope_refs", "items", "unresolved_refs", "as_of", "authority_status", "authority_receipt_ref", "retrieval_receipt_ref", "retriever_profile_ref"},
    "IUDICO": {"request_id", "request_fingerprint", "operator", "semantics_version", "kind", "status", "claim_ref", "criteria_ref", "assessment_kind", "outcome", "used_evidence_refs", "unresolved_refs", "uncertainties", "as_of", "input_authorization_receipt_refs", "input_resolution_receipt_refs"},
    "MUTOR": {"request_id", "request_fingerprint", "operator", "semantics_version", "kind", "status", "proposal_id", "proposal_digest", "target_ref", "base_revision", "replacement_proposition", "reason", "basis_refs", "unresolved_basis_refs", "proposal_state", "persistence_state", "as_of"},
    "CONTINUO": {"request_id", "request_fingerprint", "operator", "semantics_version", "kind", "status", "task_ref", "checkpoint_ref", "blockers", "conflicts", "unknowns", "mode", "execution", "canonical_commit", "as_of", "checkpoint_task_ref", "input_authorization_receipt_refs", "input_resolution_receipt_refs"},
}
RESULT_STATUS = {"MEMINI": {"RESULTS_RETURNED", "PARTIAL", "NOT_FOUND", "BLOCKED", "UNKNOWN"}, "IUDICO": {"ASSESSMENT_EMITTED", "BLOCKED", "UNKNOWN"}, "MUTOR": {"PROPOSAL_EMITTED", "BLOCKED_STALE_BASE", "BLOCKED", "UNKNOWN"}, "CONTINUO": {"PLAN_EMITTED", "BLOCKED", "UNKNOWN"}}

def _validate_ref_list(value, kind=None):
    if not isinstance(value, list): raise MiraLangError("reference collection must be a list")
    for ref in value: _validate_ref(ref, kind)

def validate_operator_result(request: dict, result: dict) -> dict:
    """Validate result shape and request correlation; never authenticates receipts."""
    if not isinstance(request, dict) or not isinstance(result, dict): raise MiraLangError("request/result must be objects")
    operator = request.get("operator")
    if operator not in RESULT_KIND: raise MiraLangError("unknown result operator")
    required = RESULT_FIELDS[operator]
    if set(result) != required: raise MiraLangError("operator result fields mismatch")
    correlate_result(request, result)
    if result["status"] not in RESULT_STATUS[operator]: raise MiraLangError("unknown operator result status")
    if not isinstance(result["semantics_version"], str) or not result["semantics_version"]: raise MiraLangError("semantics_version required")
    if result["as_of"] is not None and (not isinstance(result["as_of"], str) or not result["as_of"]): raise MiraLangError("as_of must be timestamp text or null")
    args = request.get("args")
    if not isinstance(args, dict): raise MiraLangError("request args required for result binding")
    if operator == "MEMINI":
        _validate_ref_list(result["scope_refs"])
        if not isinstance(result["items"], list) or not isinstance(result["unresolved_refs"], list): raise MiraLangError("MEMINI items/unresolved_refs must be arrays")
        _validate_ref_list(result["unresolved_refs"])
        if result["scope_refs"] != args.get("scope_refs"):
            raise MiraLangError("MEMINI result scope does not match requested scope")
        requested_scope = {(ref["kind"], ref["id"], ref["revision"]) for ref in args.get("scope_refs", [])} if isinstance(args, dict) else set()
        for item in result["items"]:
            if not isinstance(item, dict) or "record_ref" not in item:
                raise MiraLangError("MEMINI item must contain record_ref")
            ref = item["record_ref"]
            _validate_ref(ref)
            if (ref["kind"], ref["id"], ref["revision"]) not in requested_scope:
                raise MiraLangError("MEMINI item is outside requested scope")
        if result["status"] == "RESULTS_RETURNED" and not result["items"]: raise MiraLangError("RESULTS_RETURNED requires items")
        if not isinstance(result["authority_status"], str): raise MiraLangError("authority_status must be text")
        for field in ("authority_receipt_ref", "retrieval_receipt_ref", "retriever_profile_ref"):
            if result[field] is not None: _validate_ref(result[field])
    elif operator == "IUDICO":
        _validate_ref(result["claim_ref"], "Claim"); _validate_ref(result["criteria_ref"], "AssessmentCriteria")
        _validate_ref_list(result["used_evidence_refs"], "Evidence"); _validate_ref_list(result["unresolved_refs"])
        if not isinstance(result["uncertainties"], list) or any(not isinstance(x, str) for x in result["uncertainties"]): raise MiraLangError("uncertainties must be strings")
        if result["assessment_kind"] not in ASSESSMENT_KINDS: raise MiraLangError("unsupported assessment kind")
        if result["status"] == "ASSESSMENT_EMITTED" and result["outcome"] not in {"SUPPORTED", "CONTRADICTED", "INDETERMINATE"}: raise MiraLangError("emitted assessment requires a typed outcome")
        if result["status"] != "ASSESSMENT_EMITTED" and result["outcome"] is not None: raise MiraLangError("non-emitted assessment cannot claim outcome")
        for field in ("input_authorization_receipt_refs", "input_resolution_receipt_refs"): _validate_ref_list(result[field])
    elif operator == "MUTOR":
        _validate_ref(result["target_ref"], "Claim"); _validate_ref_list(result["basis_refs"], "Evidence"); _validate_ref_list(result["unresolved_basis_refs"])
        if result["base_revision"] != result["target_ref"]["revision"]: raise MiraLangError("proposal base_revision must match target revision")
        if result["status"] == "PROPOSAL_EMITTED":
            if result["proposal_state"] != "PROPOSED" or result["persistence_state"] != "NOT_PERSISTED": raise MiraLangError("MUTOR only emits unpersisted proposals")
            if not isinstance(result["proposal_id"], str) or not result["proposal_id"] or not isinstance(result["proposal_digest"], str) or re.fullmatch(r"sha256:[0-9a-f]{64}", result["proposal_digest"]) is None: raise MiraLangError("proposal identity/digest invalid")
            if not isinstance(result["replacement_proposition"], str) or not result["replacement_proposition"].strip() or not isinstance(result["reason"], str) or not result["reason"].strip(): raise MiraLangError("proposal text required")
    else:
        _validate_ref(result["task_ref"], "Task")
        if result["checkpoint_ref"] is not None: _validate_ref(result["checkpoint_ref"], "Checkpoint")
        if result["mode"] != "REPORT_ONLY" or result["execution"] != "NOT_PERFORMED" or result["canonical_commit"] is not False: raise MiraLangError("CONTINUO must remain report-only and non-committing")
        for field in ("blockers", "conflicts", "unknowns", "input_authorization_receipt_refs", "input_resolution_receipt_refs"): 
            if not isinstance(result[field], list): raise MiraLangError(f"{field} must be an array")
        for field in ("blockers", "conflicts", "unknowns"): 
            if any(not isinstance(x, str) for x in result[field]): raise MiraLangError(f"{field} must contain text")
        if result["checkpoint_task_ref"] is not None: _validate_ref(result["checkpoint_task_ref"], "Task")
    return {"status": "RESULT_SCHEMA_VALID", "operator": operator, "receipt_authenticity": "NOT_VERIFIED_HERE", "authority": "NOT_CHECKED", "effects_performed": False}


def correlate_result(request: dict, result: dict) -> dict:
    """Correlate result fields only; intentionally does not validate schema/authenticity."""
    if not isinstance(request, dict) or not isinstance(result, dict): raise MiraLangError("request/result must be objects")
    for field in ("request_id", "operator", "request_fingerprint", "semantics_version"):
        if result.get(field) != request.get(field): raise MiraLangError(f"result {field} mismatch")
    if request.get("operator") not in RESULT_KIND or result.get("kind") != RESULT_KIND[request["operator"]]: raise MiraLangError("result kind/operator mismatch")
    return {"status": "CORRELATED_LOCAL_FIELDS", "result_schema_validated": False, "receipt_authenticity": "NOT_CHECKED", "authority": "NOT_CHECKED"}
