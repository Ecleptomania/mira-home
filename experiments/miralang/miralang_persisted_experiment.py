"""Experimental filesystem-backed task state and checkpoint recovery for MiraLang.

Non-canonical. SHA-256 digests detect accidental/tampering changes only when the
attacker cannot rewrite both data and its references. No authentication, locking,
resume authorization, or canonical continuity effect is provided.
"""
from __future__ import annotations

import hashlib
import json
import os
import tempfile
import threading
import uuid
from pathlib import Path
from typing import Any

from miralang_draft import MiraLangError, evaluate_task_continuity

FORMAT = "MiraLang-Persisted-Experiment/0.1"
_LOCKS_GUARD = threading.Lock()
_TASK_LOCKS: dict[str, threading.RLock] = {}


def _task_lock(path: Path) -> threading.RLock:
    key = str(path.resolve())
    with _LOCKS_GUARD:
        return _TASK_LOCKS.setdefault(key, threading.RLock())


def _canonical(value: Any) -> bytes:
    try:
        return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise MiraLangError("state is not canonical JSON data") from exc


def _digest(value: Any) -> str:
    return hashlib.sha256(_canonical(value)).hexdigest()


def _read(path: Path) -> dict:
    try:
        raw = path.read_bytes()
        value = json.loads(raw.decode("utf-8"), object_pairs_hook=_unique_object)
    except FileNotFoundError:
        raise MiraLangError("persisted record not found")
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
        raise MiraLangError("persisted record is unreadable or invalid JSON") from exc
    if not isinstance(value, dict):
        raise MiraLangError("persisted record must be an object")
    return value


def _unique_object(pairs):
    obj = {}
    for key, value in pairs:
        if key in obj:
            raise ValueError("duplicate object key")
        obj[key] = value
    return obj


def _atomic_write(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = _canonical(value) + b"\n"
    fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=str(path.parent))
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    except BaseException:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass
        raise


def _atomic_create(path: Path, value: dict) -> None:
    """Atomically publish only if absent, using same-directory no-clobber linking."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=str(path.parent))
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(_canonical(value) + b"\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.link(temporary, path)
        os.unlink(temporary)
    except BaseException:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass
        raise


def _validate_task(task: dict) -> None:
    if not isinstance(task, dict) or set(task) != {"kind", "id", "revision", "state"}:
        raise MiraLangError("task must contain exactly kind, id, revision, state")
    if task["kind"] != "Task" or not isinstance(task["id"], str) or not task["id"]:
        raise MiraLangError("invalid task identity")
    if not isinstance(task["revision"], int) or isinstance(task["revision"], bool) or task["revision"] < 1:
        raise MiraLangError("invalid task revision")
    _canonical(task["state"])


def _task_ref(task: dict) -> dict:
    return {"kind": "Task", "id": task["id"], "revision": task["revision"]}


class ExperimentalTaskStore:
    """Minimal local store. Callers must serialize writers; cross-process locking is absent."""

    def __init__(self, directory: str | os.PathLike):
        self.root = Path(directory)

    def _task_path(self, task_id: str) -> Path:
        if not isinstance(task_id, str) or not task_id or any(c not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._-" for c in task_id):
            raise MiraLangError("task id must be a safe filename component")
        return self.root / "tasks" / f"{task_id}.json"

    def create(self, task_id: str, state: Any) -> dict:
        path = self._task_path(task_id)
        task = {"kind": "Task", "id": task_id, "revision": 1, "state": state}
        _validate_task(task)
        try:
            _atomic_create(path, task)
        except FileExistsError as exc:
            raise MiraLangError("task already exists") from exc
        return self.load(task_id)

    def load(self, task_id: str) -> dict:
        task = _read(self._task_path(task_id))
        _validate_task(task)
        return task

    def update(self, task_id: str, expected_revision: int, state: Any) -> dict:
        if not isinstance(expected_revision, int) or isinstance(expected_revision, bool) or expected_revision < 1:
            raise MiraLangError("invalid expected revision")
        path = self._task_path(task_id)
        # Process-local serialization only; cross-process writers remain unsupported.
        with _task_lock(path):
            current = self.load(task_id)
            if current["revision"] != expected_revision:
                raise MiraLangError("stale expected revision; update refused")
            updated = {**current, "revision": current["revision"] + 1, "state": state}
            _validate_task(updated)
            _atomic_write(path, updated)
            return self.load(task_id)

    def checkpoint(self, task_id: str) -> dict:
        # Serialize the entire checkpoint publication with local updates.
        # Cross-process writers remain outside this experiment's trust boundary.
        with _task_lock(self._task_path(task_id)):
            return self._checkpoint_locked(task_id)

    def _checkpoint_locked(self, task_id: str) -> dict:
        task = self.load(task_id)
        payload = {"task_ref": _task_ref(task), "state": task["state"]}
        evidence = {"source_file": str(self._task_path(task_id).resolve()), "observed_revision": task["revision"], "observation": "LOCAL_FILE_READ"}
        integrity_payload = {**payload, "evidence": evidence}
        # Checkpoint identity denotes an event, not merely a content version.
        # The digest remains content-derived; the random suffix prevents a later
        # checkpoint of unchanged state from replacing the earlier event record.
        checkpoint = {
            "format": FORMAT,
            "checkpoint_id": f"{task_id}-r{task['revision']}-{uuid.uuid4().hex}",
            **payload,
            "payload_digest": _digest(integrity_payload),
            "evidence": evidence,
        }
        _atomic_create(self.root / "checkpoints" / f"{checkpoint['checkpoint_id']}.json", checkpoint)
        return checkpoint

    def recover(self, task_id: str, checkpoint_id: str) -> dict:
        """Evaluate under the same process-local lock as update()."""
        path = self._task_path(task_id)
        with _task_lock(path):
            return self._recover_locked(task_id, checkpoint_id)

    def _recover_locked(self, task_id: str, checkpoint_id: str) -> dict:
        if not isinstance(checkpoint_id, str) or any(c not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._-" for c in checkpoint_id):
            raise MiraLangError("invalid checkpoint id")
        checkpoint = _read(self.root / "checkpoints" / f"{checkpoint_id}.json")
        current = self.load(task_id)
        if set(checkpoint) != {"format", "checkpoint_id", "task_ref", "state", "payload_digest", "evidence"}:
            raise MiraLangError("checkpoint schema invalid; recovery refused")
        task_ref = checkpoint.get("task_ref")
        evidence = checkpoint.get("evidence")
        if (not isinstance(task_ref, dict) or set(task_ref) != {"kind", "id", "revision"}
                or task_ref.get("kind") != "Task" or not isinstance(task_ref.get("id"), str)
                or not task_ref.get("id") or not isinstance(task_ref.get("revision"), int)
                or isinstance(task_ref.get("revision"), bool) or task_ref["revision"] < 1
                or not isinstance(evidence, dict)
                or set(evidence) != {"source_file", "observed_revision", "observation"}
                or not isinstance(evidence.get("source_file"), str)
                or not isinstance(evidence.get("observed_revision"), int)
                or isinstance(evidence.get("observed_revision"), bool)
                or evidence.get("observation") != "LOCAL_FILE_READ"
                or evidence.get("source_file") != str(self._task_path(task_id).resolve())):
            raise MiraLangError("checkpoint schema invalid; recovery refused")
        expected_payload = {"task_ref": task_ref, "state": checkpoint.get("state"), "evidence": evidence}
        integrity_ok = (
            checkpoint.get("format") == FORMAT
            and checkpoint.get("checkpoint_id") == checkpoint_id
            and checkpoint.get("payload_digest") == _digest(expected_payload)
            and evidence.get("observed_revision") == task_ref.get("revision")
        )
        continuity = evaluate_task_continuity(
            _task_ref(current), task_ref,
            task_ref.get("revision"), _task_ref(current), current["revision"]
        )
        if not integrity_ok:
            outcome, reason = "FAIL", "CHECKPOINT_INTEGRITY_CHECK_FAILED"
        elif continuity["outcome"] == "PASS":
            if _canonical(current["state"]) == _canonical(checkpoint.get("state")):
                outcome, reason = "PASS", "PERSISTED_TASK_AND_CHECKPOINT_MATCH"
            else:
                outcome, reason = "FAIL", "CURRENT_TASK_STATE_DIFFERS_FROM_CHECKPOINT"
        else:
            outcome, reason = continuity["outcome"], continuity["reason"]
        return {
            "outcome": outcome,
            "reason": reason,
            "checkpoint_id": checkpoint_id,
            "task_id": task_id,
            "current_revision": current["revision"],
            "checkpoint_revision": task_ref.get("revision"),
            "checkpoint_payload_digest": checkpoint.get("payload_digest"),
            "checkpoint_integrity": "VERIFIED_LOCAL_DIGEST" if integrity_ok else "FAILED",
            "provenance": checkpoint.get("evidence"),
            "restored_state": checkpoint.get("state") if outcome == "PASS" else None,
            "resume_authorized": False,
            "canonical_commit": False,
            "atomicity": "SINGLE_FILE_REPLACE; MULTI_WRITER_SERIALIZATION_NOT_PROVIDED",
            "authenticity": "UNAUTHENTICATED_LOCAL_METADATA",
        }
