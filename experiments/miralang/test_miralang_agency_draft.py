import copy
import unittest
from miralang_agency_draft import AgencyDraftError, validate_agency_record, validate_ranked_proposals

REF = {"kind":"Evidence", "id":"e1", "revision":1}
def proposal(n=1, kind="QUESTION", rank=1):
    return {"kind":"AgencyProposal", "id":f"p{n}", "revision":1, "proposal_kind":kind,
            "actor":"MIRA", "status":"PROPOSED", "statement":"Ask whether the source is current",
            "reason":"Freshness is unresolved", "basis_refs":[REF], "created_at":"session:turn-4",
            "supersedes_ref":None, "ranking":{"ordinal":rank,"rationale":"High information value"}}

class AgencyDraftTests(unittest.TestCase):
    def test_question_goal_revision_and_decline_are_valid_inert_proposals(self):
        for kind in ("QUESTION", "GOAL_REVISION", "DECLINE_WORK"):
            item=proposal(kind=kind)
            self.assertIs(validate_agency_record(item), item)

    def test_decision_attribution_labels_each_actor(self):
        for actor in ("MIRA", "USER", "JOINT"):
            item={"kind":"DecisionAttribution", "id":"d1", "revision":1, "actor":actor,
                  "basis_refs":[REF], "created_at":"session:turn-4", "supersedes_ref":None,
                  "decision":"Proceed with the evidence review", "rationale":"Within agreed scope"}
            self.assertIs(validate_agency_record(item), item)

    def test_supersession_must_be_older(self):
        item=proposal()
        item["revision"]=2
        item["supersedes_ref"]={"kind":"AgencyProposal", "id":"p1", "revision":1}
        validate_agency_record(item)
        item["supersedes_ref"]["revision"]=2
        with self.assertRaises(AgencyDraftError): validate_agency_record(item)

    def test_rejects_empty_decline_reason_and_commit_like_status(self):
        item=proposal(kind="DECLINE_WORK"); item["reason"]="  "
        with self.assertRaises(AgencyDraftError): validate_agency_record(item)
        item=proposal(); item["status"]="COMMITTED"
        with self.assertRaises(AgencyDraftError): validate_agency_record(item)

    def test_ranked_list_requires_distinct_contiguous_ordinals(self):
        validate_ranked_proposals([proposal(1, rank=1), proposal(2, rank=2)])
        with self.assertRaises(AgencyDraftError): validate_ranked_proposals([proposal(1, rank=1), proposal(2, rank=1)])
        with self.assertRaises(AgencyDraftError): validate_ranked_proposals([proposal(1, rank=2)])

    def test_rejects_missing_provenance_and_bool_revision(self):
        item=proposal(); item["basis_refs"]=[]
        with self.assertRaises(AgencyDraftError): validate_agency_record(item)
        item=proposal(); item["revision"]=True
        with self.assertRaises(AgencyDraftError): validate_agency_record(item)

if __name__ == "__main__": unittest.main()
