"""Unit + integration tests for date_from_mtime."""
from __future__ import annotations

import os
from datetime import datetime, timezone

import pytest

from ops import date_from_mtime


def _epoch(y, m, d, hh=0, mm=0):
    return datetime(y, m, d, hh, mm, tzinfo=timezone.utc).timestamp()


class TestDateFromMtimeUnit:
    def test_prefix_default_format(self):
        ctx = {"mtimes": [_epoch(2024, 4, 13)]}
        got = date_from_mtime.apply("photo.jpg", 0, ctx, {})
        assert got == "2024-04-13_photo.jpg"

    def test_suffix_custom_format(self):
        ctx = {"mtimes": [_epoch(2024, 4, 13, 15, 30)]}
        got = date_from_mtime.apply("note.txt", 0, ctx, {
            "format": "%Y%m%d-%H%M", "position": "suffix", "sep": "-",
        })
        assert got == "note-20240413-1530.txt"

    def test_missing_mtimes_raises(self):
        with pytest.raises(ValueError, match="filesystem access"):
            date_from_mtime.apply("photo.jpg", 0, {}, {})

    def test_idx_out_of_range_raises(self):
        with pytest.raises(ValueError, match="filesystem access"):
            date_from_mtime.apply("photo.jpg", 5, {"mtimes": [_epoch(2024, 1, 1)]}, {})

    def test_idx_picks_correct_file(self):
        ctx = {"mtimes": [_epoch(2024, 1, 1), _epoch(2024, 6, 15)]}
        assert date_from_mtime.apply("a.jpg", 0, ctx, {}).startswith("2024-01-01_")
        assert date_from_mtime.apply("b.jpg", 1, ctx, {}).startswith("2024-06-15_")


class TestDateFromMtimeIntegration:
    """Exercise through /api/preview with real files to confirm ctx plumbing."""

    def test_preview_with_dir_populates_mtimes(self, client, tmp_path):
        p = tmp_path / "photo.jpg"
        p.write_text("x")
        # Force a known mtime
        target = _epoch(2024, 4, 13)
        os.utime(p, (target, target))

        r = client.post("/api/preview", json={
            "dir": str(tmp_path),
            "files": ["photo.jpg"],
            "pipeline": [{"op": "date_from_mtime", "params": {"format": "%Y-%m-%d"}}],
        })
        assert r.status_code == 200, r.get_json()
        rows = r.get_json()
        assert rows[0]["new"] == "2024-04-13_photo.jpg"

    def test_preview_without_dir_returns_400(self, client):
        r = client.post("/api/preview", json={
            "files": ["photo.jpg"],
            "pipeline": [{"op": "date_from_mtime", "params": {}}],
        })
        assert r.status_code == 400
        assert "filesystem" in r.get_json()["error"]

    def test_apply_end_to_end(self, client, tmp_path):
        p = tmp_path / "photo.jpg"
        p.write_text("x")
        target = _epoch(2024, 4, 13)
        os.utime(p, (target, target))

        r = client.post("/api/apply", json={
            "dir": str(tmp_path),
            "files": ["photo.jpg"],
            "pipeline": [{"op": "date_from_mtime", "params": {}}],
        })
        assert r.status_code == 200, r.get_json()
        assert (tmp_path / "2024-04-13_photo.jpg").is_file()


