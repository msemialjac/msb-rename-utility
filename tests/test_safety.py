"""Tests for the safety / hardening fixes from the code review.

Covers: partial-failure rollback, external-file clobber detection, double-undo
rejection, date_from_mtime 400 surface, ReDoS baseline, path-separator
rejection, undo-log filename prefix validation, undo JSON schema validation.
"""
from __future__ import annotations

import json
import re
import time
from pathlib import Path
from unittest.mock import patch

import pytest


# ──────────────────────────────────────────────── partial-failure rollback ──
class TestApplyRollback:
    def test_phase1_failure_rolls_back(self, client, tmp_path):
        """If src.rename(tmp) fails partway, earlier temps must return to their
        original source names — no `.tmp` files left, originals intact."""
        for n in ["a.txt", "b.txt", "c.txt"]:
            (tmp_path / n).write_text(f"content {n}")

        real_rename = Path.rename
        call_count = {"n": 0}

        def flaky_rename(self, target):
            call_count["n"] += 1
            # Succeed on the first 2 phase-1 moves, fail on the 3rd
            if call_count["n"] == 3:
                raise OSError("simulated mid-run failure")
            return real_rename(self, target)

        with patch.object(Path, "rename", flaky_rename):
            r = client.post("/api/apply", json={
                "dir": str(tmp_path),
                "files": ["a.txt", "b.txt", "c.txt"],
                "pipeline": [{"op": "case", "params": {"mode": "upper", "scope": "stem"}}],
            })
        assert r.status_code == 500
        body = r.get_json()
        assert "rename failed mid-run" in body["error"]

        # No temp files should remain in the directory.
        leftovers = [p.name for p in tmp_path.iterdir() if p.name.startswith(".__rename_")]
        assert leftovers == [], f"temp files leaked: {leftovers}"
        # Originals all present and untouched.
        for n in ["a.txt", "b.txt", "c.txt"]:
            assert (tmp_path / n).read_text() == f"content {n}"
        # Undo-log must be removed — stale log against restored files would be
        # a recipe for catastrophe if later replayed.
        logs = [p.name for p in tmp_path.iterdir() if p.name.startswith(".rename-undo-")]
        assert logs == [], f"stale undo-log left: {logs}"


# ─────────────────────────────────────── external-on-disk clobber detection ──
class TestExternalClobber:
    def test_refuses_clobber_of_file_not_in_batch(self, client, tmp_path):
        (tmp_path / "a.txt").write_text("A")
        (tmp_path / "b_renamed.txt").write_text("existing B — DO NOT CLOBBER")

        r = client.post("/api/apply", json={
            "dir": str(tmp_path),
            "files": ["a.txt"],
            "pipeline": [{"op": "replace", "params": {"find": "a", "with": "b_renamed"}}],
        })
        assert r.status_code == 409
        assert "clobber" in r.get_json()["error"]
        # The external file must be untouched.
        assert (tmp_path / "b_renamed.txt").read_text() == "existing B — DO NOT CLOBBER"
        # The source must also be untouched.
        assert (tmp_path / "a.txt").read_text() == "A"


# ─────────────────────────────────────────────── double-undo replay blocked ──
class TestDoubleUndo:
    def test_second_undo_returns_404(self, client, tmp_path):
        (tmp_path / "a.txt").write_text("A")
        r = client.post("/api/apply", json={
            "dir": str(tmp_path),
            "files": ["a.txt"],
            "pipeline": [{"op": "case", "params": {"mode": "upper", "scope": "stem"}}],
        })
        undo_log = r.get_json()["undo_log"]

        r1 = client.post("/api/undo", json={"undo_log": undo_log})
        assert r1.status_code == 200

        r2 = client.post("/api/undo", json={"undo_log": undo_log})
        assert r2.status_code == 404  # log archived as .done — original path no longer exists


# ───────────────────── date_from_mtime without dir surfaces a clean 400 ──
class TestDateFromMtimeMissingDir:
    def test_without_dir_returns_400_mentioning_dir(self, client):
        r = client.post("/api/preview", json={
            "files": ["photo.jpg"],
            "pipeline": [{"op": "date_from_mtime", "params": {}}],
        })
        assert r.status_code == 400
        # Message must mention what to do (supply `dir`), not a bare traceback.
        assert "dir" in r.get_json()["error"].lower()


# ───────────────────────────── regex ReDoS baseline (no timeout, just guard) ──
class TestRegexRedosBaseline:
    def test_pathological_pattern_completes_fast_on_short_input(self, client):
        """Document that short inputs don't trigger catastrophic backtracking
        on the filenames we'd plausibly process. Full ReDoS mitigation
        (thread/timeout) is out of scope; this test establishes a floor."""
        start = time.monotonic()
        r = client.post("/api/preview", json={
            "files": ["aaaaaaaaaaX.txt"],  # 10 a's — well below catastrophic threshold
            "pipeline": [{"op": "regex", "params": {"pattern": "(a+)+$", "repl": "z"}}],
        })
        elapsed = time.monotonic() - start
        assert r.status_code == 200
        # Guard against a regression that would make even tiny inputs hang.
        # 2s is generous; a healthy CPython runs this in milliseconds.
        assert elapsed < 2.0, f"regex took {elapsed:.2f}s on 10-char input"


# ────────────────────────── path-separator rejection (no silent stripping) ──
class TestPathSeparatorRejection:
    def test_preview_rejects_slash_in_filename(self, client):
        r = client.post("/api/preview", json={
            "files": ["../etc/passwd"],
            "pipeline": [],
        })
        assert r.status_code == 400
        assert "basename" in r.get_json()["error"]

    def test_apply_rejects_backslash_in_filename(self, client, tmp_path):
        r = client.post("/api/apply", json={
            "dir": str(tmp_path),
            "files": [r"subdir\file.txt"],
            "pipeline": [],
        })
        assert r.status_code == 400


# ─────────────────── undo-log filename and schema must validate ──
class TestUndoLogValidation:
    def test_rejects_non_prefix_log_path(self, client, tmp_path):
        rogue = tmp_path / "evil.json"
        rogue.write_text(json.dumps({
            "dir": str(tmp_path), "renames": [{"from": "a", "to": "b"}],
        }))
        r = client.post("/api/undo", json={"undo_log": str(rogue)})
        assert r.status_code == 400
        assert "valid undo-log filename" in r.get_json()["error"]

    def test_rejects_malformed_json(self, client, tmp_path):
        bad = tmp_path / ".rename-undo-bad.json"
        bad.write_text("{ not valid json")
        r = client.post("/api/undo", json={"undo_log": str(bad)})
        assert r.status_code == 400
        assert "not valid JSON" in r.get_json()["error"]

    def test_rejects_missing_renames_key(self, client, tmp_path):
        bad = tmp_path / ".rename-undo-missing.json"
        bad.write_text(json.dumps({"dir": str(tmp_path)}))  # no `renames`
        r = client.post("/api/undo", json={"undo_log": str(bad)})
        assert r.status_code == 400

    def test_rejects_wrong_type_in_renames(self, client, tmp_path):
        bad = tmp_path / ".rename-undo-wrongtype.json"
        bad.write_text(json.dumps({
            "dir": str(tmp_path),
            "renames": [{"from": 42, "to": "x"}],  # from is not a string
        }))
        r = client.post("/api/undo", json={"undo_log": str(bad)})
        assert r.status_code == 400


# ──────────────────────── rapid successive applies don't stomp each other ──
class TestNoLogCollision:
    def test_two_applies_in_same_second_produce_distinct_logs(self, client, tmp_path):
        """Previously: second apply within the same second silently overwrote
        the first undo-log. Fix: UUID suffix in the filename."""
        (tmp_path / "a.txt").write_text("A")
        (tmp_path / "b.txt").write_text("B")

        r1 = client.post("/api/apply", json={
            "dir": str(tmp_path),
            "files": ["a.txt"],
            "pipeline": [{"op": "case", "params": {"mode": "upper", "scope": "stem"}}],
        })
        r2 = client.post("/api/apply", json={
            "dir": str(tmp_path),
            "files": ["b.txt"],
            "pipeline": [{"op": "case", "params": {"mode": "upper", "scope": "stem"}}],
        })
        assert r1.status_code == 200
        assert r2.status_code == 200
        log1 = r1.get_json()["undo_log"]
        log2 = r2.get_json()["undo_log"]
        assert log1 != log2
        # Both logs must still be on disk — neither was clobbered.
        assert Path(log1).is_file()
        assert Path(log2).is_file()
