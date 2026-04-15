"""Unit tests for pad, trim, remove_at, change_ext."""
from __future__ import annotations

import pytest

from ops import pad, trim, remove_at, change_ext


class TestPad:
    def test_single_run(self):
        assert pad.apply("IMG_7.jpg", 0, {}, {"width": 4}) == "IMG_0007.jpg"

    def test_multiple_runs(self):
        # Every maximal run gets padded independently
        assert pad.apply("a1b22c.txt", 0, {}, {"width": 3}) == "a001b022c.txt"

    def test_already_wide_enough(self):
        assert pad.apply("a0123.txt", 0, {}, {"width": 3}) == "a0123.txt"

    def test_no_digits(self):
        assert pad.apply("photo.txt", 0, {}, {"width": 4}) == "photo.txt"

    def test_zero_width_is_noop(self):
        assert pad.apply("a7.txt", 0, {}, {"width": 0}) == "a7.txt"

    def test_scope_name_pads_ext_digits_too(self):
        assert pad.apply("a7.jp2", 0, {}, {"width": 3, "scope": "name"}) == "a007.jp002"


class TestTrim:
    def test_default_strips_whitespace(self):
        assert trim.apply("  hi  .txt", 0, {}, {}) == "hi.txt"

    def test_custom_chars(self):
        assert trim.apply("__name__.txt", 0, {}, {"chars": "_"}) == "name.txt"

    def test_left_only(self):
        assert trim.apply("..name..txt", 0, {}, {"chars": ".", "side": "left"}) == "name..txt"

    def test_right_only(self):
        assert trim.apply("..name.txt", 0, {}, {"chars": ".", "side": "right"}) == "..name.txt"

    def test_preserves_extension(self):
        assert trim.apply("  name  .TXT", 0, {}, {}) == "name.TXT"

    def test_bad_side_raises(self):
        with pytest.raises(ValueError):
            trim.apply("a.b", 0, {}, {"side": "diagonal"})


class TestRemoveAt:
    def test_removes_range(self):
        assert remove_at.apply("photo.jpg", 0, {}, {"start": 0, "count": 3}) == "to.jpg"

    def test_zero_count_noop(self):
        assert remove_at.apply("photo.jpg", 0, {}, {"start": 0, "count": 0}) == "photo.jpg"

    def test_negative_start(self):
        # stem 'photo' len 5; start=-3 → 2; count=2 → remove 'ot'
        assert remove_at.apply("photo.jpg", 0, {}, {"start": -3, "count": 2}) == "pho.jpg"

    def test_range_past_end_clamps(self):
        assert remove_at.apply("ab.txt", 0, {}, {"start": 1, "count": 999}) == "a.txt"

    def test_preserves_extension(self):
        # Removing from stem only; the .txt must survive even if we'd overshoot
        assert remove_at.apply("ab.txt", 0, {}, {"start": 0, "count": 5}) == ".txt"


class TestChangeExt:
    def test_basic(self):
        assert change_ext.apply("photo.JPEG", 0, {}, {"to": "jpg"}) == "photo.jpg"

    def test_accepts_leading_dot(self):
        assert change_ext.apply("photo.JPEG", 0, {}, {"to": ".jpg"}) == "photo.jpg"

    def test_empty_removes_extension(self):
        assert change_ext.apply("photo.jpg", 0, {}, {"to": ""}) == "photo"

    def test_adds_extension_when_none(self):
        assert change_ext.apply("README", 0, {}, {"to": "md"}) == "README.md"

    def test_only_if_matches_case_insensitively(self):
        assert change_ext.apply("photo.JPEG", 0, {}, {"to": "jpg", "only_if": "jpeg"}) == "photo.jpg"

    def test_only_if_skips_non_match(self):
        assert change_ext.apply("photo.PNG", 0, {}, {"to": "jpg", "only_if": "jpeg"}) == "photo.PNG"

    def test_only_if_empty_string_treated_as_unset(self):
        # UI sends "" for unset text fields; must NOT act as "only if ext is empty"
        assert change_ext.apply("photo.JPEG", 0, {}, {"to": "jpg", "only_if": ""}) == "photo.jpg"
