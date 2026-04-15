"""Unit tests for the pure op layer. No filesystem, no Flask."""
from __future__ import annotations

import pytest

from ops import run_pipeline
from ops import case, replace, regex, insert, numbering


# ──────────────────────────────────────────────────────────── case ──
class TestCase:
    def test_lower_stem_preserves_ext(self):
        assert case.apply("IMG.JPG", 0, {}, {"mode": "lower", "scope": "stem"}) == "img.JPG"

    def test_lower_both(self):
        assert case.apply("IMG.JPG", 0, {}, {"mode": "lower", "scope": "both"}) == "img.jpg"

    def test_title(self):
        assert case.apply("my notes.txt", 0, {}, {"mode": "title", "scope": "stem"}) == "My Notes.txt"

    def test_sentence(self):
        assert case.apply("hELLO world.md", 0, {}, {"mode": "sentence", "scope": "stem"}) == "Hello world.md"

    def test_no_extension(self):
        assert case.apply("README", 0, {}, {"mode": "lower", "scope": "ext"}) == "README"

    def test_bad_mode_raises(self):
        with pytest.raises(ValueError):
            case.apply("a.b", 0, {}, {"mode": "nope"})


# ───────────────────────────────────────────────────────── replace ──
class TestReplace:
    def test_literal_case_sensitive(self):
        assert replace.apply("IMG_01.JPG", 0, {}, {"find": "IMG", "with": "PHOTO"}) == "PHOTO_01.JPG"

    def test_empty_find_is_noop(self):
        assert replace.apply("a.txt", 0, {}, {"find": "", "with": "X"}) == "a.txt"

    def test_case_insensitive(self):
        got = replace.apply("IMG_img.JPG", 0, {}, {"find": "img", "with": "X", "case_sensitive": False})
        assert got == "X_X.JPG"

    def test_scope_stem_ignores_ext(self):
        got = replace.apply("photo.photo", 0, {}, {"find": "photo", "with": "X", "scope": "stem"})
        assert got == "X.photo"


# ─────────────────────────────────────────────────────────── regex ──
class TestRegex:
    def test_backref(self):
        assert regex.apply("IMG_001.jpg", 0, {}, {"pattern": r"IMG_(\d+)", "repl": r"photo_\1"}) == "photo_001.jpg"

    def test_ignorecase_flag(self):
        got = regex.apply("Hello.txt", 0, {}, {"pattern": "hello", "repl": "hi", "flags": ["i"]})
        assert got == "hi.txt"

    def test_empty_pattern_is_noop(self):
        assert regex.apply("a.txt", 0, {}, {"pattern": "", "repl": "X"}) == "a.txt"

    def test_bad_flag_raises(self):
        with pytest.raises(ValueError):
            regex.apply("a.txt", 0, {}, {"pattern": "a", "repl": "", "flags": ["z"]})


# ────────────────────────────────────────────────────────── insert ──
class TestInsert:
    def test_at_start(self):
        assert insert.apply("photo.jpg", 0, {}, {"text": "NEW_", "at": 0}) == "NEW_photo.jpg"

    def test_at_end_keyword(self):
        assert insert.apply("photo.jpg", 0, {}, {"text": "_END", "at": "end"}) == "photo_END.jpg"

    def test_negative_index(self):
        # 'photo' is 5 chars, at=-2 means insert before the last two ('to')
        assert insert.apply("photo.jpg", 0, {}, {"text": "-", "at": -2}) == "pho-to.jpg"

    def test_empty_text_is_noop(self):
        assert insert.apply("x.y", 0, {}, {"text": "", "at": 0}) == "x.y"


# ─────────────────────────────────────────────────────── numbering ──
class TestNumbering:
    def test_suffix_pad(self):
        got = numbering.apply("a.txt", 4, {}, {"start": 1, "step": 1, "pad": 3})
        assert got == "a_005.txt"

    def test_prefix(self):
        got = numbering.apply("a.txt", 0, {}, {"start": 10, "pad": 2, "position": "prefix", "sep": "-"})
        assert got == "10-a.txt"

    def test_step(self):
        got = numbering.apply("a.txt", 3, {}, {"start": 100, "step": 5, "pad": 0})
        assert got == "a_115.txt"


# ──────────────────────────────────────────────────── run_pipeline ──
class TestPipeline:
    def test_empty_pipeline_is_identity(self):
        assert run_pipeline(["a.txt", "b.TXT"], []) == ["a.txt", "b.TXT"]

    def test_sequential_application(self):
        got = run_pipeline(
            ["IMG_0001.JPG", "IMG_0002.JPG"],
            [
                {"op": "case", "params": {"mode": "lower", "scope": "both"}},
                {"op": "replace", "params": {"find": "img_", "with": "photo_"}},
                {"op": "numbering", "params": {"start": 10, "pad": 3, "sep": "__"}},
            ],
        )
        assert got == ["photo_0001__010.jpg", "photo_0002__011.jpg"]

    def test_unknown_op_raises(self):
        with pytest.raises(ValueError, match="unknown op"):
            run_pipeline(["a.txt"], [{"op": "nonexistent", "params": {}}])

    def test_idx_is_per_input_not_per_op(self):
        # numbering uses idx — two files should get idx=0 and idx=1 respectively
        got = run_pipeline(["a.txt", "b.txt"], [{"op": "numbering", "params": {"start": 0, "pad": 1}}])
        assert got == ["a_0.txt", "b_1.txt"]
