"""Contract test for the URL deep-link format.

There's no JS test harness here, but the contract the UI speaks can be
exercised from Python: if we build the same #p=<b64url-json> string and
decode it the same way the UI does, the resulting pipeline must be accepted
by /api/preview. That catches any schema drift on either side.
"""
from __future__ import annotations

import base64
import json

import pytest


def _encode(payload: dict) -> str:
    """Mirror of static/app.js encodeShareHash()."""
    raw = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    b64 = base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")
    return f"#p={b64}"


def _decode(hash_str: str) -> dict | None:
    """Mirror of static/app.js decodeShareHash()."""
    if not hash_str.startswith("#p="):
        return None
    b64 = hash_str[3:]
    pad = "=" * (-len(b64) % 4)
    try:
        return json.loads(base64.urlsafe_b64decode(b64 + pad).decode("utf-8"))
    except Exception:
        return None


class TestDeepLinkCodec:
    def test_roundtrip_simple(self):
        payload = {"pipeline": [{"op": "case", "params": {"mode": "lower", "scope": "both"}}]}
        assert _decode(_encode(payload)) == payload

    def test_roundtrip_with_files(self):
        payload = {
            "pipeline": [{"op": "numbering", "params": {"start": 1, "pad": 3}}],
            "files": "a.txt\nb.txt",
        }
        assert _decode(_encode(payload)) == payload

    def test_roundtrip_unicode(self):
        payload = {"pipeline": [{"op": "replace", "params": {"find": "café", "with": "cafe"}}]}
        assert _decode(_encode(payload)) == payload

    def test_malformed_returns_none(self):
        assert _decode("#nope") is None
        assert _decode("#p=!!!not-base64!!!") is None
        assert _decode("") is None


class TestDeepLinkAcceptedByPreview:
    """Decoded payload must be a valid /api/preview body (modulo `files` parsing)."""

    def test_decoded_pipeline_is_usable(self, client):
        payload = {
            "pipeline": [
                {"op": "case", "params": {"mode": "lower", "scope": "both"}},
                {"op": "numbering", "params": {"start": 1, "pad": 3, "sep": "_"}},
            ],
            "files": "IMG_1.JPG\nIMG_2.JPG",
        }
        decoded = _decode(_encode(payload))
        files = decoded["files"].split("\n")
        r = client.post("/api/preview", json={"files": files, "pipeline": decoded["pipeline"]})
        assert r.status_code == 200
        rows = r.get_json()
        assert [row["new"] for row in rows] == ["img_1_001.jpg", "img_2_002.jpg"]


@pytest.fixture
def client():
    from app import app as flask_app
    flask_app.config["TESTING"] = True
    with flask_app.test_client() as c:
        yield c
