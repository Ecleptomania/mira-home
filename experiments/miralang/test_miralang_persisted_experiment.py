import json
import tempfile
import threading
import unittest
from pathlib import Path

from miralang_draft import MiraLangError
from miralang_persisted_experiment import ExperimentalTaskStore


class PersistedRecoveryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.store = ExperimentalTaskStore(self.tmp.name)
        self.store.create("T-1", {"step": "draft", "notes": ["verified input"]})

    def tearDown(self):
        self.tmp.cleanup()

    def test_persist_checkpoint_and_recover_actual_state(self):
        checkpoint = self.store.checkpoint("T-1")
        # New store instance proves the operation is filesystem-backed, not instance memory.
        recovered = ExperimentalTaskStore(self.tmp.name).recover("T-1", checkpoint["checkpoint_id"])
        self.assertEqual(recovered["outcome"], "PASS")
        self.assertEqual(recovered["restored_state"], {"step": "draft", "notes": ["verified input"]})
        self.assertEqual(recovered["checkpoint_integrity"], "VERIFIED_LOCAL_DIGEST")
        self.assertEqual(recovered["provenance"]["observation"], "LOCAL_FILE_READ")
        self.assertFalse(recovered["resume_authorized"])
        self.assertFalse(recovered["canonical_commit"])

    def test_repeated_checkpoints_preserve_distinct_events_and_are_repeatable(self):
        first = self.store.checkpoint("T-1")
        second = self.store.checkpoint("T-1")

        self.assertNotEqual(first["checkpoint_id"], second["checkpoint_id"])
        self.assertEqual(first["payload_digest"], second["payload_digest"])
        for checkpoint in (first, second):
            path = Path(self.tmp.name) / "checkpoints" / f"{checkpoint['checkpoint_id']}.json"
            self.assertTrue(path.is_file())
            first_result = self.store.recover("T-1", checkpoint["checkpoint_id"])
            repeated_result = self.store.recover("T-1", checkpoint["checkpoint_id"])
            self.assertEqual(first_result, repeated_result)
            self.assertEqual(first_result["outcome"], "PASS")
            self.assertEqual(first_result["restored_state"], {"step": "draft", "notes": ["verified input"]})

    def test_new_revision_checkpoint_does_not_overwrite_old_event(self):
        old = self.store.checkpoint("T-1")
        self.store.update("T-1", 1, {"step": "new revision"})
        new = self.store.checkpoint("T-1")

        old_path = Path(self.tmp.name) / "checkpoints" / f"{old['checkpoint_id']}.json"
        new_path = Path(self.tmp.name) / "checkpoints" / f"{new['checkpoint_id']}.json"
        self.assertTrue(old_path.is_file())
        self.assertTrue(new_path.is_file())
        self.assertEqual(self.store.recover("T-1", old["checkpoint_id"])["outcome"], "FAIL")
        self.assertEqual(self.store.recover("T-1", new["checkpoint_id"])["outcome"], "PASS")

    def test_stale_checkpoint_does_not_return_state(self):
        checkpoint = self.store.checkpoint("T-1")
        self.store.update("T-1", 1, {"step": "changed"})
        result = self.store.recover("T-1", checkpoint["checkpoint_id"])
        self.assertEqual(result["outcome"], "FAIL")
        self.assertEqual(result["reason"], "CHECKPOINT_BASE_REVISION_DIFFERS_FROM_CURRENT_REVISION")
        self.assertIsNone(result["restored_state"])

    def test_payload_tampering_is_detected(self):
        checkpoint = self.store.checkpoint("T-1")
        path = Path(self.tmp.name) / "checkpoints" / f"{checkpoint['checkpoint_id']}.json"
        text = path.read_text()
        path.write_text(text.replace('"draft"', '"forged"'))
        result = self.store.recover("T-1", checkpoint["checkpoint_id"])
        self.assertEqual(result["outcome"], "FAIL")
        self.assertEqual(result["reason"], "CHECKPOINT_INTEGRITY_CHECK_FAILED")
        self.assertIsNone(result["restored_state"])

    def test_update_rejects_boolean_or_nonpositive_expected_revision(self):
        for revision in (True, False, 0, -1):
            with self.subTest(revision=revision), self.assertRaisesRegex(MiraLangError, "invalid expected revision"):
                self.store.update("T-1", revision, {"step": "must not write"})
        self.assertEqual(self.store.load("T-1")["revision"], 1)
        self.assertEqual(self.store.load("T-1")["state"], {"step": "draft", "notes": ["verified input"]})

    def test_stale_compare_and_swap_refuses_update(self):
        self.store.update("T-1", 1, {"step": "new"})
        with self.assertRaisesRegex(MiraLangError, "stale expected revision"):
            self.store.update("T-1", 1, {"step": "clobber"})
        self.assertEqual(self.store.load("T-1")["state"], {"step": "new"})

    def test_duplicate_json_keys_fail_closed(self):
        path = Path(self.tmp.name) / "tasks" / "T-1.json"
        path.write_text('{"kind":"Task","kind":"Task","id":"T-1","revision":1,"state":{}}')
        with self.assertRaisesRegex(MiraLangError, "unreadable or invalid JSON"):
            self.store.load("T-1")

    def test_python_non_finite_state_rejected_on_create_and_update(self):
        with self.assertRaisesRegex(MiraLangError, "state is not canonical JSON data"):
            self.store.create("T-nan", {"value": float("nan")})

        with self.assertRaisesRegex(MiraLangError, "state is not canonical JSON data"):
            self.store.update("T-1", 1, {"value": float("inf")})

        with self.assertRaisesRegex(MiraLangError, "persisted record not found"):
            self.store.load("T-nan")
        self.assertEqual(self.store.load("T-1"), {
            "kind": "Task", "id": "T-1", "revision": 1,
            "state": {"step": "draft", "notes": ["verified input"]},
        })


    def test_concurrent_compare_and_swap_has_one_winner(self):
        barrier = threading.Barrier(2)
        outcomes = []
        def attempt(value):
            barrier.wait()
            try:
                self.store.update("T-1", 1, {"winner": value})
                outcomes.append("PASS")
            except MiraLangError:
                outcomes.append("STALE")
        threads = [threading.Thread(target=attempt, args=(i,)) for i in range(2)]
        for thread in threads: thread.start()
        for thread in threads: thread.join()
        self.assertCountEqual(outcomes, ["PASS", "STALE"])
        self.assertEqual(self.store.load("T-1")["revision"], 2)

    def test_malformed_checkpoint_nested_fields_fail_closed(self):
        checkpoint = self.store.checkpoint("T-1")
        path = Path(self.tmp.name) / "checkpoints" / f"{checkpoint['checkpoint_id']}.json"
        for bad_field in ("task_ref", "evidence"):
            damaged = json.loads(path.read_text())
            damaged[bad_field] = None
            path.write_text(json.dumps(damaged))
            with self.subTest(field=bad_field), self.assertRaisesRegex(MiraLangError, "checkpoint schema invalid"):
                self.store.recover("T-1", checkpoint["checkpoint_id"])
            path.write_text(json.dumps(checkpoint))

    def test_checkpoint_for_another_task_cannot_be_recovered_as_this_task(self):
        self.store.create("T-2", {"step": "different task"})
        checkpoint = self.store.checkpoint("T-2")

        with self.assertRaisesRegex(MiraLangError, "checkpoint schema invalid"):
            self.store.recover("T-1", checkpoint["checkpoint_id"])

    def test_forged_provenance_is_rejected(self):
        checkpoint = self.store.checkpoint("T-1")
        path = Path(self.tmp.name) / "checkpoints" / f"{checkpoint['checkpoint_id']}.json"
        damaged = json.loads(path.read_text())
        damaged["evidence"]["source_file"] = "/forged/path"
        path.write_text(json.dumps(damaged))
        with self.assertRaisesRegex(MiraLangError, "checkpoint schema invalid"):
            self.store.recover("T-1", checkpoint["checkpoint_id"])

    def test_unknown_checkpoint_fields_are_rejected(self):
        checkpoint = self.store.checkpoint("T-1")
        path = Path(self.tmp.name) / "checkpoints" / f"{checkpoint['checkpoint_id']}.json"
        damaged = json.loads(path.read_text())
        damaged["unrecognized"] = "unexpected"
        path.write_text(json.dumps(damaged))
        with self.assertRaisesRegex(MiraLangError, "checkpoint schema invalid"):
            self.store.recover("T-1", checkpoint["checkpoint_id"])

    def test_task_id_cannot_escape_store(self):
        with self.assertRaisesRegex(MiraLangError, "safe filename"):
            self.store.load("../outside")
    def test_direct_state_edit_without_revision_increment_is_not_pass(self):
        checkpoint = self.store.checkpoint("T-1")
        task_path = Path(self.tmp.name) / "tasks" / "T-1.json"
        task = json.loads(task_path.read_text())
        task["state"] = {"step": "silently altered"}
        task_path.write_text(json.dumps(task))  # revision remains 1; checkpoint untouched

        result = self.store.recover("T-1", checkpoint["checkpoint_id"])

        self.assertEqual(result["outcome"], "FAIL")
        self.assertEqual(result["reason"], "CURRENT_TASK_STATE_DIFFERS_FROM_CHECKPOINT")
        self.assertIsNone(result["restored_state"])


    def test_concurrent_create_has_exactly_one_winner_and_no_overwrite(self):
        barrier = threading.Barrier(2)
        outcomes = []
        def attempt(value):
            barrier.wait()
            try:
                self.store.create("T-2", {"winner": value})
                outcomes.append(("CREATED", value))
            except MiraLangError:
                outcomes.append(("EXISTS", value))
        threads = [threading.Thread(target=attempt, args=(i,)) for i in range(2)]
        for thread in threads: thread.start()
        for thread in threads: thread.join()
        self.assertEqual(sum(outcome[0] == "CREATED" for outcome in outcomes), 1)
        winner = self.store.load("T-2")["state"]["winner"]
        self.assertEqual(sum(outcome == ("CREATED", winner) for outcome in outcomes), 1)


if __name__ == "__main__":
    unittest.main()
