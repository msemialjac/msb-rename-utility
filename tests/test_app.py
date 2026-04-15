"""Integration tests for Flask endpoints — preview, apply, undo.

These exercise the filesystem via pytest's tmp_path fixture. The tests assert
the full round-trip: apply creates expected files, writes a recoverable
undo-log, and undo restores the original state exactly.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

def _make_files(tmp_path: Path, names: list[str]) -> None:
    for n in names:
        (tmp_path / n).write_text(f"content of {n}")


# ───────────────────────────────────────────────────────── preview ──
class TestPreview:
    def test_identity_no_pipeline(self, client):
        r = client.post("/api/preview", json={"files": ["a.txt"], "pipeline": []})
        assert r.status_code == 200
        assert r.get_json() == [{"old": "a.txt", "new": "a.txt", "unchanged": True, "collision": False}]

    def test_collision_self(self, client):
        # Two different inputs collapsing to the same new name → collision
        r = client.post("/api/preview", json={
            "files": ["A.TXT", "a.txt"],
            "pipeline": [{"op": "case", "params": {"mode": "lower", "scope": "both"}}],
        })
        rows = r.get_json()
        assert all(row["collision"] for row in rows)

    def test_collision_vs_existing(self, client):
        # Renaming 'a.txt' to 'b.txt' while 'b.txt' is also in the input set
        r = client.post("/api/preview", json={
            "files": ["a.txt", "b.txt"],
            "pipeline": [{"op": "replace", "params": {"find": "a", "with": "b"}}],
        })
        rows = r.get_json()
        assert rows[0]["collision"]  # a.txt → b.txt collides with existing b.txt

    def test_bad_request_shape(self, client):
        r = client.post("/api/preview", json={"files": "not a list", "pipeline": []})
        assert r.status_code == 400

    def test_unknown_op(self, client):
        r = client.post("/api/preview", json={"files": ["a"], "pipeline": [{"op": "zzz", "params": {}}]})
        assert r.status_code == 400


# ─────────────────────────────────────────────────────────── apply ──
class TestApply:
    def test_round_trip(self, client, tmp_path):
        _make_files(tmp_path, ["IMG_01.JPG", "IMG_02.JPG"])
        r = client.post("/api/apply", json={
            "dir": str(tmp_path),
            "files": ["IMG_01.JPG", "IMG_02.JPG"],
            "pipeline": [{"op": "case", "params": {"mode": "lower", "scope": "both"}}],
        })
        assert r.status_code == 200, r.get_json()
        data = r.get_json()
        assert data["applied"] == 2

        # Files renamed, originals gone
        assert (tmp_path / "img_01.jpg").read_text() == "content of IMG_01.JPG"
        assert (tmp_path / "img_02.jpg").read_text() == "content of IMG_02.JPG"
        assert not (tmp_path / "IMG_01.JPG").exists()

        # Undo-log sidecar exists and is well-formed
        log = Path(data["undo_log"])
        assert log.is_file()
        doc = json.loads(log.read_text())
        assert len(doc["renames"]) == 2
        assert doc["renames"][0] == {"from": "IMG_01.JPG", "to": "img_01.jpg"}

    def test_refuses_collision(self, client, tmp_path):
        _make_files(tmp_path, ["A.TXT", "a.txt"])
        r = client.post("/api/apply", json={
            "dir": str(tmp_path),
            "files": ["A.TXT", "a.txt"],
            "pipeline": [{"op": "case", "params": {"mode": "lower", "scope": "both"}}],
        })
        assert r.status_code == 409
        # Nothing was renamed; no undo-log written
        assert (tmp_path / "A.TXT").exists()
        assert not any(p.name.startswith(".rename-undo-") for p in tmp_path.iterdir())

    def test_refuses_missing_file(self, client, tmp_path):
        _make_files(tmp_path, ["a.txt"])
        r = client.post("/api/apply", json={
            "dir": str(tmp_path),
            "files": ["a.txt", "ghost.txt"],
            "pipeline": [{"op": "case", "params": {"mode": "upper", "scope": "stem"}}],
        })
        assert r.status_code == 404
        assert (tmp_path / "a.txt").exists()  # untouched

    def test_refuses_bad_dir(self, client, tmp_path):
        r = client.post("/api/apply", json={
            "dir": str(tmp_path / "does-not-exist"),
            "files": ["a.txt"],
            "pipeline": [],
        })
        assert r.status_code == 400

    def test_rename_into_existing_input_is_refused(self, client, tmp_path):
        # a→b via replace — but b is also an input file, so this is a collision.
        # This guards the "clobber an existing file" case without relying on the
        # two-phase internal mechanism (which is belt-and-braces for this gate).
        for n in ["a", "b", "c"]:
            (tmp_path / n).write_text(n)
        r = client.post("/api/apply", json={
            "dir": str(tmp_path),
            "files": ["a", "b", "c"],
            "pipeline": [{"op": "replace", "params": {"find": "a", "with": "b"}}],
        })
        assert r.status_code == 409

    def test_noop_files_skipped(self, client, tmp_path):
        _make_files(tmp_path, ["a.txt", "b.txt"])
        # Replacing 'zzz' (not present) → every row unchanged
        r = client.post("/api/apply", json={
            "dir": str(tmp_path),
            "files": ["a.txt", "b.txt"],
            "pipeline": [{"op": "replace", "params": {"find": "zzz", "with": "Q"}}],
        })
        assert r.status_code == 200
        data = r.get_json()
        assert data["applied"] == 0  # nothing actually changed
        assert (tmp_path / "a.txt").exists()


# ──────────────────────────────────────────────────────────── undo ──
class TestUndo:
    def test_undo_restores_original_state(self, client, tmp_path):
        _make_files(tmp_path, ["IMG_01.JPG", "IMG_02.JPG"])
        r = client.post("/api/apply", json={
            "dir": str(tmp_path),
            "files": ["IMG_01.JPG", "IMG_02.JPG"],
            "pipeline": [{"op": "case", "params": {"mode": "lower", "scope": "both"}}],
        })
        undo_log = r.get_json()["undo_log"]

        r2 = client.post("/api/undo", json={"undo_log": undo_log})
        assert r2.status_code == 200
        assert r2.get_json() == {"undone": 2}

        assert (tmp_path / "IMG_01.JPG").read_text() == "content of IMG_01.JPG"
        assert (tmp_path / "IMG_02.JPG").read_text() == "content of IMG_02.JPG"
        assert not (tmp_path / "img_01.jpg").exists()

        # Log archived with .done suffix so it can't be replayed again accidentally
        assert not Path(undo_log).exists()
        assert Path(undo_log + ".done").exists()

    def test_undo_missing_log(self, client, tmp_path):
        r = client.post("/api/undo", json={"undo_log": str(tmp_path / "nope.json")})
        assert r.status_code == 404
