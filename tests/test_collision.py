"""Tests for the collision auto-resolve post-pass."""
from __future__ import annotations

import pytest

from ops.collision import resolve


class TestResolve:
    def test_no_duplicates_is_identity(self):
        assert resolve(["a.txt", "b.txt", "c.txt"]) == ["a.txt", "b.txt", "c.txt"]

    def test_first_wins_second_gets_2(self):
        assert resolve(["a.txt", "a.txt"]) == ["a.txt", "a (2).txt"]

    def test_three_way_collision(self):
        assert resolve(["a.txt", "a.txt", "a.txt"]) == ["a.txt", "a (2).txt", "a (3).txt"]

    def test_preserves_extension(self):
        got = resolve(["photo.JPEG", "photo.JPEG"])
        assert got == ["photo.JPEG", "photo (2).JPEG"]

    def test_order_stable(self):
        got = resolve(["x.txt", "y.txt", "x.txt", "y.txt", "x.txt"])
        assert got == ["x.txt", "y.txt", "x (2).txt", "y (2).txt", "x (3).txt"]

    def test_skips_taken_suffix(self):
        # If "a (2).txt" is already in the list before a duplicate "a.txt",
        # the duplicate must become "a (3).txt" — can't reuse (2).
        got = resolve(["a.txt", "a (2).txt", "a.txt"])
        assert got == ["a.txt", "a (2).txt", "a (3).txt"]

    def test_increments_existing_suffix(self):
        # If the duplicate *is already* "a (2).txt", the second one becomes (3).
        got = resolve(["a (2).txt", "a (2).txt"])
        assert got == ["a (2).txt", "a (3).txt"]

    def test_no_extension(self):
        assert resolve(["README", "README"]) == ["README", "README (2)"]

    def test_empty_list(self):
        assert resolve([]) == []


class TestPreviewEndpoint:
    """Integration: auto_resolve_collisions flag flows through /api/preview."""

    def test_flag_resolves_self_collision(self, client):
        r = client.post("/api/preview", json={
            "files": ["A.TXT", "a.txt"],
            "pipeline": [{"op": "case", "params": {"mode": "lower", "scope": "both"}}],
            "auto_resolve_collisions": True,
        })
        rows = r.get_json()
        assert [row["new"] for row in rows] == ["a.txt", "a (2).txt"]
        assert not any(row["collision"] for row in rows)

    def test_flag_off_still_flags(self, client):
        r = client.post("/api/preview", json={
            "files": ["A.TXT", "a.txt"],
            "pipeline": [{"op": "case", "params": {"mode": "lower", "scope": "both"}}],
        })
        assert all(row["collision"] for row in r.get_json())


