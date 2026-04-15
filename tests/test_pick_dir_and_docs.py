"""Tests for /api/pick-dir (zenity wrapper) and /docs/ static serve.

`/api/pick-dir` is tested with mocked subprocess + shutil.which — we never
actually spawn zenity. `/docs/` is tested with a temporary _DOCS_DIR so the
tests don't depend on whether mkdocs has been built locally.
"""
from __future__ import annotations

from pathlib import Path
from unittest.mock import patch, MagicMock


# ──────────────────────────────────────────────── /api/pick-dir branches ──
class TestPickDir:
    def test_returns_503_when_zenity_missing(self, client):
        with patch("app.shutil.which", return_value=None):
            r = client.post("/api/pick-dir")
        assert r.status_code == 503
        assert "zenity" in r.get_json()["error"]

    def test_cancel_returns_200_with_cancelled_flag(self, client):
        fake_result = MagicMock(returncode=1, stdout="", stderr="")
        with patch("app.shutil.which", return_value="/usr/bin/zenity"), \
             patch("app.subprocess.run", return_value=fake_result):
            r = client.post("/api/pick-dir")
        assert r.status_code == 200
        assert r.get_json() == {"cancelled": True}

    def test_success_returns_dir_and_filtered_listing(self, client, tmp_path):
        # Populate: two visible files, one dotfile, one subdirectory (excluded).
        (tmp_path / "a.txt").write_text("a")
        (tmp_path / "b.txt").write_text("b")
        (tmp_path / ".rename-undo-old.json").write_text("{}")  # must be filtered
        (tmp_path / "subdir").mkdir()

        fake_result = MagicMock(returncode=0, stdout=str(tmp_path) + "\n", stderr="")
        with patch("app.shutil.which", return_value="/usr/bin/zenity"), \
             patch("app.subprocess.run", return_value=fake_result):
            r = client.post("/api/pick-dir")

        assert r.status_code == 200
        data = r.get_json()
        assert data["dir"] == str(tmp_path)
        # Dotfile excluded; subdir excluded (not a file); visible files sorted.
        assert data["files"] == ["a.txt", "b.txt"]

    def test_stdout_points_to_non_directory_returns_400(self, client, tmp_path):
        ghost = tmp_path / "does-not-exist"
        fake_result = MagicMock(returncode=0, stdout=str(ghost) + "\n", stderr="")
        with patch("app.shutil.which", return_value="/usr/bin/zenity"), \
             patch("app.subprocess.run", return_value=fake_result):
            r = client.post("/api/pick-dir")
        assert r.status_code == 400
        assert "not a directory" in r.get_json()["error"]


# ───────────────────────────────────────── /docs/ path-traversal safety ──
class TestDocsStaticServe:
    def test_traversal_attempt_is_rejected(self, client, tmp_path, monkeypatch):
        """`send_from_directory` + Werkzeug's path normalization must refuse
        to serve files outside _DOCS_DIR. Confirms the backstop is wired up
        correctly for this project's specific mounting."""
        # Build a minimal fake site/ root and a secret file next to it.
        docs_root = tmp_path / "site"
        docs_root.mkdir()
        (docs_root / "index.html").write_text("<h1>ok</h1>")
        (tmp_path / "secret.txt").write_text("should never be served")

        monkeypatch.setattr("app._DOCS_DIR", docs_root)

        # Normal hit works
        r_ok = client.get("/docs/")
        assert r_ok.status_code == 200
        assert b"ok" in r_ok.data

        # Traversal attempts must not return the secret file.
        # Werkzeug normalizes `..` in URL paths at routing time, so most
        # traversal attempts never reach our handler; the ones that do are
        # caught by safe_join inside send_from_directory.
        for attempt in [
            "/docs/../secret.txt",
            "/docs/%2e%2e/secret.txt",
            "/docs/..%2fsecret.txt",
        ]:
            r = client.get(attempt)
            assert r.status_code in (301, 302, 308, 400, 404), \
                f"traversal path {attempt!r} unexpectedly returned {r.status_code}"
            # Under no circumstance should the secret content leak.
            assert b"should never be served" not in r.data
