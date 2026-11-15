"""Non-canonical inert contracts for proposals and decision attribution.

Validation only: no ranking, authorization, goal commit, task execution, or evidence of autonomy.
"""
AGENCY_VERSION = "0.1-draft"
ACTORS = {"MIRA", "USER", "JOINT"}
PROPOSAL_KINDS = {"QUESTION", "GOAL_REVISION", "DECLINE_WORK"}

class AgencyDraftError(ValueError):
    pass

def _text(value, field):
    if not isinstance(value, str) or not value.strip():
        raise AgencyDraftError(f"{field} must be nonblank text")

def _refs(value, field, minimum=0):
    if not isinstance(value, list) or not minimum <= len(value) <= 50:
        raise AgencyDraftError(f"{field} must be a list containing {minimum}..50 references")
    for ref in value:
        if (not isinstance(ref, dict) or set(ref) != {"kind", "id", "revision"}
            or not isinstance(ref["kind"], str) or not ref["kind"].strip()
            or not isinstance(ref["id"], str) or not ref["id"].strip()
            or not isinstance(ref["revision"], int) or isinstance(ref["revision"], bool)
            or ref["revision"] < 1):
            raise AgencyDraftError(f"{field} contains an invalid versioned reference")

def validate_agency_record(record):
    """Validate a proposal or attribution record; see README for field contract."""
    if not isinstance(record, dict) or record.get("kind") not in {"AgencyProposal", "DecisionAttribution"}:
        raise AgencyDraftError("kind must be AgencyProposal or DecisionAttribution")
    common = {"kind", "id", "revision", "actor", "basis_refs", "created_at", "supersedes_ref"}
    if not isinstance(record.get("id"), str) or not record["id"].strip():
        raise AgencyDraftError("id must be nonblank text")
    if not isinstance(record.get("revision"), int) or isinstance(record["revision"], bool) or record["revision"] < 1:
        raise AgencyDraftError("revision must be a positive integer")
    if record.get("actor") not in ACTORS:
        raise AgencyDraftError("actor must be MIRA, USER, or JOINT")
    _refs(record.get("basis_refs"), "basis_refs", 1)
    _text(record.get("created_at"), "created_at")
    prior = record.get("supersedes_ref")
    if prior is not None:
        _refs([prior], "supersedes_ref", 1)
        if prior["revision"] >= record["revision"]:
            raise AgencyDraftError("supersedes_ref must identify an earlier revision")
    if record["kind"] == "AgencyProposal":
        if set(record) != common | {"proposal_kind", "status", "statement", "reason", "ranking"}:
            raise AgencyDraftError("AgencyProposal field set mismatch")
        if record["proposal_kind"] not in PROPOSAL_KINDS or record["status"] != "PROPOSED":
            raise AgencyDraftError("unsupported proposal kind or non-proposed status")
        _text(record["statement"], "statement")
        _text(record["reason"], "reason")
        rank = record["ranking"]
        if rank is not None:
            if not isinstance(rank, dict) or set(rank) != {"ordinal", "rationale"}:
                raise AgencyDraftError("ranking must be null or contain ordinal and rationale")
            if not isinstance(rank["ordinal"], int) or isinstance(rank["ordinal"], bool) or rank["ordinal"] < 1:
                raise AgencyDraftError("ranking.ordinal must be a positive integer")
            _text(rank["rationale"], "ranking.rationale")
    else:
        if set(record) != common | {"decision", "rationale"}:
            raise AgencyDraftError("DecisionAttribution field set mismatch")
        _text(record["decision"], "decision")
        _text(record["rationale"], "rationale")
    return record

def validate_ranked_proposals(proposals):
    """Validate an ordered set with unique contiguous ranks starting at 1."""
    if not isinstance(proposals, list) or not proposals:
        raise AgencyDraftError("proposals must be a nonempty list")
    ranks = []
    for item in proposals:
        validate_agency_record(item)
        if item["kind"] != "AgencyProposal" or item["ranking"] is None:
            raise AgencyDraftError("every ranked item must be a ranked AgencyProposal")
        ranks.append(item["ranking"]["ordinal"])
    if sorted(ranks) != list(range(1, len(ranks) + 1)):
        raise AgencyDraftError("ranking ordinals must be unique and contiguous from 1")
    return proposals
