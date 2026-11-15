import copy
import unittest
from miralang_draft import (
    MiraLangError, bundle_digest, canonical_bundle_object, correlate_result,
    request_fingerprint, strict_json_loads, validate_parsed_request_binding,
    parse_surface, render_surface, validate_bundle_structure, validate_operator_result,
)

class DraftPrimitiveTests(unittest.TestCase):
    def setUp(self):
        self.bundle = {"manifest": {"bundle_id":"B1", "schema_version":"0.2-draft", "semantics_version":"0.2-draft", "canonicalization_version":"MIRAJSON-CANON-0.3-draft", "root_refs":[{"kind":"Task","id":"T1","revision":1}], "external_refs":[], "extensions":{}}, "records":[{"kind":"Task","id":"T1","revision":1,"objective":"test","scope":{"include":["test"],"exclude":[]},"acceptance":[],"lifecycle_state":"ACTIVE","continuation_policy":"NO_AUTO_EFFECT","goal_refs":[],"checkpoint_refs":[],"provenance_refs":[],"state_receipt_ref":None,"completion_verification_ref":None}]}
        self.request = {"request_id":"r1", "operator":"MEMINI", "args":{"scope_refs":[{"kind":"Task","id":"T1","revision":1}],"query":"test","max_results":1,"max_result_bytes":1024}}
        self.parsed = {"surface_version":"0.4-draft", "bundle":copy.deepcopy(self.bundle), "request":self.request}
        self.request.update({"bundle_id":"B1","schema_version":"0.2-draft","semantics_version":"0.2-draft"})
        self.request["request_fingerprint"] = request_fingerprint(self.request,self.bundle["manifest"],self.bundle)

    def test_strict_json(self):
        self.assertEqual(strict_json_loads(b'{"x":1}'),{"x":1})
        for raw in [b'{"x":1,"x":2}', b'{"x":NaN}', b'\xff', b'"\\ud800"', b'{"x":1.5}']:
            with self.subTest(raw=raw), self.assertRaises(MiraLangError): strict_json_loads(raw)

    def test_ordering_and_bundle_digest(self):
        reordered=copy.deepcopy(self.bundle); reordered["records"].reverse(); reordered["manifest"]["root_refs"].reverse()
        self.assertEqual(bundle_digest(self.bundle),bundle_digest(reordered))
        self.assertEqual(canonical_bundle_object(self.bundle),canonical_bundle_object(reordered))

    def test_detached_manifest_is_rejected(self):
        detached=copy.deepcopy(self.bundle["manifest"])
        detached["bundle_id"]="OTHER"
        with self.assertRaises(MiraLangError):
            request_fingerprint(self.request,detached,self.bundle)

    def test_manifest_declarations_are_consistent(self):
        bad=copy.deepcopy(self.parsed)
        bad["bundle"]["manifest"]["external_refs"].append({"kind":"Task","id":"T1","revision":1})
        bad["request"]["request_fingerprint"]=request_fingerprint(bad["request"],bad["bundle"]["manifest"],bad["bundle"])
        with self.assertRaises(MiraLangError): validate_parsed_request_binding(bad)
        bad=copy.deepcopy(self.parsed)
        bad["bundle"]["manifest"]["root_refs"][0]["revision"]=0
        with self.assertRaises(MiraLangError): validate_parsed_request_binding(bad)

    def test_mismatched_declaration_states_rejected(self):
        bad=copy.deepcopy(self.parsed)
        bad["request"]["reference_declaration_states"]={"Task:T1@1":"UNKNOWN"}
        bad["request"]["request_fingerprint"]=request_fingerprint(bad["request"],bad["bundle"]["manifest"],bad["bundle"])
        with self.assertRaises(MiraLangError): validate_parsed_request_binding(bad)

    def test_binding_success_and_mutations(self):
        self.assertEqual(validate_parsed_request_binding(self.parsed)["status"],"MATCHED_LOCAL_DRAFT")
        bad=copy.deepcopy(self.parsed); bad["request"]["schema_version"]="wrong"
        with self.assertRaises(MiraLangError): validate_parsed_request_binding(bad)
        bad=copy.deepcopy(self.parsed); bad["bundle"]["records"][0]["objective"]="tampered"
        with self.assertRaises(MiraLangError): validate_parsed_request_binding(bad)

    def test_bundle_structure_rejects_unknown_and_undeclared_refs(self):
        self.assertEqual(validate_bundle_structure(self.bundle)["status"], "STRUCTURALLY_VALID_DRAFT")
        bad = copy.deepcopy(self.bundle)
        bad["records"][0]["surprise"] = True
        with self.assertRaises(MiraLangError): validate_bundle_structure(bad)
        bad = copy.deepcopy(self.bundle)
        bad["records"][0]["goal_refs"] = [{"kind":"Goal", "id":"missing", "revision":1}]
        with self.assertRaises(MiraLangError): validate_bundle_structure(bad)
        bad = copy.deepcopy(self.bundle)
        bad["records"][0]["lifecycle_state"] = "MAGIC"
        with self.assertRaises(MiraLangError): validate_bundle_structure(bad)
        bad = copy.deepcopy(self.bundle)
        bad["records"][0]["objective"] = []
        with self.assertRaises(MiraLangError): validate_bundle_structure(bad)
        bad = copy.deepcopy(self.bundle)
        bad["manifest"]["extensions"] = {"oops": "x"}
        with self.assertRaises(MiraLangError): validate_bundle_structure(bad)
        bad = copy.deepcopy(self.bundle)
        bad["manifest"]["root_refs"] = [{"kind":"Task", "id":"missing", "revision":1}]
        with self.assertRaises(MiraLangError): validate_bundle_structure(bad)

    def test_surface_roundtrip(self):
        text = render_surface(self.parsed)
        reparsed = parse_surface(text)
        self.assertEqual(reparsed["bundle"], self.parsed["bundle"])
        self.assertEqual(reparsed["request"]["request_fingerprint"], self.parsed["request"]["request_fingerprint"])
        self.assertEqual(render_surface(reparsed), text)

    def test_surface_bundle_without_request_roundtrips(self):
        parsed = {"surface_version":"0.4-draft", "bundle":copy.deepcopy(self.bundle), "request":None}
        text = render_surface(parsed)
        reparsed = parse_surface(text)
        self.assertIsNone(reparsed["request"])
        self.assertEqual(reparsed["bundle"], parsed["bundle"])
        self.assertEqual(render_surface(reparsed), text)

    def test_surface_renderer_rejects_unrecognized_top_level_fields(self):
        parsed = copy.deepcopy(self.parsed)
        parsed["unreviewed_metadata"] = {"claim": "must not be silently discarded"}
        with self.assertRaisesRegex(MiraLangError, "parsed Surface object fields invalid"):
            render_surface(parsed)

    def test_surface_rejects_duplicate_keys_and_late_record(self):
        bad = "MIRALANG-SURFACE 0.4-draft\nBUNDLE {\"bundle_id\":\"b1\",\"bundle_id\":\"b2\"}"
        with self.assertRaises(MiraLangError): parse_surface(bad)
        late = render_surface(self.parsed) + "\nTASK {\"id\":\"t2\"}"
        with self.assertRaises(MiraLangError): parse_surface(late)

    def test_surface_rejects_line_endings_and_bad_request_type(self):
        with self.assertRaises(MiraLangError): parse_surface(render_surface(self.parsed).replace("\n", "\r\n"))
        bad = copy.deepcopy(self.parsed)
        bad["request"]["args"]["query"] = "\ud800"
        bad["request"]["request_fingerprint"] = "sha256:" + "0" * 64
        with self.assertRaises(MiraLangError): render_surface(bad)

    def test_operator_result_schemas_and_invariants(self):
        examples = []
        mem = {"request_id":self.request["request_id"], "request_fingerprint":self.request["request_fingerprint"], "operator":"MEMINI", "semantics_version":"0.2-draft", "kind":"RetrievalResult", "status":"RESULTS_RETURNED", "scope_refs":copy.deepcopy(self.request["args"]["scope_refs"]), "items":[{"record_ref":copy.deepcopy(self.request["args"]["scope_refs"][0])}], "unresolved_refs":[], "as_of":"2026-01-01T00:00:00Z", "authority_status":"UNKNOWN", "authority_receipt_ref":None, "retrieval_receipt_ref":None}
        mem["retriever_profile_ref"]={"kind":"RetrievalProfile", "id":"lexical-v1", "revision":1}
        examples.append((self.request, mem))
        iud_request={"request_id":"i1", "request_fingerprint":"sha256:"+"1"*64, "operator":"IUDICO", "semantics_version":"0.2-draft", "args":{"claim_ref":{"kind":"Claim","id":"c1","revision":1},"criteria_ref":{"kind":"AssessmentCriteria","id":"ac1","revision":1},"evidence_refs":[{"kind":"Evidence","id":"e1","revision":1}],"assessment_kind":"SUPPORT_CHECK"}}
        iud={"request_id":"i1", "request_fingerprint":iud_request["request_fingerprint"], "operator":"IUDICO", "semantics_version":"0.2-draft", "kind":"AssessmentResult", "status":"ASSESSMENT_EMITTED", "claim_ref":iud_request["args"]["claim_ref"], "criteria_ref":iud_request["args"]["criteria_ref"], "assessment_kind":"SUPPORT_CHECK", "outcome":"INDETERMINATE", "used_evidence_refs":iud_request["args"]["evidence_refs"], "unresolved_refs":[], "uncertainties":[], "as_of":None, "input_authorization_receipt_refs":[], "input_resolution_receipt_refs":[{"kind":"InputResolutionReceiptRef","id":"r1","revision":1}]}
        examples.append((iud_request,iud))
        mut_request={"request_id":"m1", "request_fingerprint":"sha256:"+"2"*64, "operator":"MUTOR", "semantics_version":"0.2-draft", "args":{}}
        mut={"request_id":"m1", "request_fingerprint":mut_request["request_fingerprint"], "operator":"MUTOR", "semantics_version":"0.2-draft", "kind":"ProposalResult", "status":"PROPOSAL_EMITTED", "proposal_id":"proposal-1", "proposal_digest":"sha256:"+"3"*64, "target_ref":{"kind":"Claim","id":"c1","revision":1}, "base_revision":1, "replacement_proposition":"new", "reason":"evidence", "basis_refs":[{"kind":"Evidence","id":"e1","revision":1}], "unresolved_basis_refs":[], "proposal_state":"PROPOSED", "persistence_state":"NOT_PERSISTED", "as_of":None}
        examples.append((mut_request,mut))
        cont_request={"request_id":"c1", "request_fingerprint":"sha256:"+"4"*64, "operator":"CONTINUO", "semantics_version":"0.2-draft", "args":{"task_ref":{"kind":"Task","id":"t1","revision":1},"checkpoint_ref":None,"mode":"REPORT_ONLY"}}
        cont={"request_id":"c1", "request_fingerprint":cont_request["request_fingerprint"], "operator":"CONTINUO", "semantics_version":"0.2-draft", "kind":"ContinuationPlan", "status":"UNKNOWN", "task_ref":cont_request["args"]["task_ref"], "checkpoint_ref":None, "blockers":[], "conflicts":[], "unknowns":["no verified state"], "mode":"REPORT_ONLY", "execution":"NOT_PERFORMED", "canonical_commit":False, "as_of":None, "checkpoint_task_ref":None, "input_authorization_receipt_refs":[], "input_resolution_receipt_refs":[]}
        examples.append((cont_request,cont))
        for request,result in examples:
            with self.subTest(operator=request["operator"]): self.assertEqual(validate_operator_result(request,result)["status"],"RESULT_SCHEMA_VALID")
        bad=copy.deepcopy(cont);bad["execution"]="PERFORMED"
        with self.assertRaises(MiraLangError): validate_operator_result(cont_request,bad)
        bad=copy.deepcopy(iud);bad["status"]="UNKNOWN";bad["outcome"]="SUPPORTED"
        with self.assertRaises(MiraLangError): validate_operator_result(iud_request,bad)

    def test_continuity_revision_evaluation(self):
        from miralang_draft import evaluate_task_continuity
        task = {"kind": "Task", "id": "T1", "revision": 4}
        checkpoint = {"kind": "Task", "id": "T1", "revision": 4}
        passed = evaluate_task_continuity(task, checkpoint, 4, task, 4)
        self.assertEqual(passed["outcome"], "PASS")
        self.assertFalse(passed["resume_authorized"])
        self.assertFalse(passed["canonical_commit"])
        stale = evaluate_task_continuity(task, checkpoint, 4, {"kind": "Task", "id": "T1", "revision": 5}, 5)
        self.assertEqual(stale["outcome"], "FAIL")
        self.assertEqual(stale["reason"], "CHECKPOINT_BASE_REVISION_DIFFERS_FROM_CURRENT_REVISION")
        self.assertEqual(evaluate_task_continuity(task, checkpoint, None, task, 4)["outcome"], "UNKNOWN")
        other = evaluate_task_continuity(task, checkpoint, 4, {"kind": "Task", "id": "T2", "revision": 4}, 4)
        self.assertEqual(other["reason"], "REQUESTED_TASK_DIFFERS_FROM_OBSERVED_CURRENT_TASK")
        boolean_revision = evaluate_task_continuity(task, checkpoint, True, task, True)
        self.assertEqual(boolean_revision["outcome"], "UNKNOWN")
        # Python treats bool as an int subclass; revision checks must reject it.
        boolean_task_ref = {"kind": "Task", "id": "T1", "revision": True}
        invalid_ref = evaluate_task_continuity(boolean_task_ref, checkpoint, 4, task, 4)
        self.assertEqual(invalid_ref["outcome"], "UNKNOWN")
        self.assertEqual(invalid_ref["reason"], "REQUIRED_CONTINUITY_INPUT_MISSING_OR_INVALID")

    def test_memini_results_must_be_within_requested_scope(self):
        result={"request_id":self.request["request_id"],"request_fingerprint":self.request["request_fingerprint"],"operator":"MEMINI","semantics_version":"0.2-draft","kind":"RetrievalResult","status":"RESULTS_RETURNED","scope_refs":copy.deepcopy(self.request["args"]["scope_refs"]),"items":[{"record_ref":{"kind":"Task","id":"OUTSIDE","revision":1}}],"unresolved_refs":[],"as_of":"2026-01-01T00:00:00Z","authority_status":"UNKNOWN","authority_receipt_ref":None,"retrieval_receipt_ref":None,"retriever_profile_ref":{"kind":"RetrievalProfile","id":"lexical-v1","revision":1}}
        with self.assertRaisesRegex(MiraLangError, "outside requested scope"):
            validate_operator_result(self.request, result)

    def test_memini_result_must_echo_exact_requested_scope(self):
        result={"request_id":self.request["request_id"],"request_fingerprint":self.request["request_fingerprint"],"operator":"MEMINI","semantics_version":"0.2-draft","kind":"RetrievalResult","status":"UNKNOWN","scope_refs":[],"items":[],"unresolved_refs":[],"as_of":None,"authority_status":"UNKNOWN","authority_receipt_ref":None,"retrieval_receipt_ref":None,"retriever_profile_ref":None}
        with self.assertRaisesRegex(MiraLangError, "scope does not match"):
            validate_operator_result(self.request, result)

    def test_result_correlation(self):
        result={"request_id":"r1","operator":"MEMINI","request_fingerprint":self.request["request_fingerprint"],"semantics_version":"0.2-draft","kind":"RetrievalResult","status":"RESULTS_RETURNED"}
        self.assertEqual(correlate_result(self.request,result)["status"],"CORRELATED_LOCAL_FIELDS")
        result["request_id"]="other"
        with self.assertRaises(MiraLangError): correlate_result(self.request,result)

if __name__ == "__main__": unittest.main()

class DeepNestingBoundaryTests(unittest.TestCase):
    def test_excessive_json_nesting_uses_draft_error(self):
        deeply_nested = "[" * 2000 + "0" + "]" * 2000
        with self.assertRaisesRegex(MiraLangError, "nesting exceeds supported depth"):
            strict_json_loads(deeply_nested)
