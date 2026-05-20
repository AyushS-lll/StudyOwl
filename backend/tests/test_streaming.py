"""
PR 9 — Streaming hints.

Streaming tests against a real server need an HTTP client + DB fixture. Here
we only pin the small primitives that don't require either: the NDJSON
serializer in the sessions router. End-to-end "the chunks render in order"
is a manual smoke check.
"""

import json

from routers.sessions import _ndjson


def test_ndjson_emits_newline_terminated_json():
    out = _ndjson({"type": "chunk", "text": "hello"})
    assert out.endswith(b"\n")
    parsed = json.loads(out.decode("utf-8").rstrip("\n"))
    assert parsed == {"type": "chunk", "text": "hello"}


def test_ndjson_serializes_non_string_defaults():
    # UUIDs etc. get coerced via default=str so the router doesn't blow up on
    # otherwise-unserializable types.
    from uuid import uuid4
    payload = {"type": "session_created", "session_id": uuid4()}
    out = _ndjson(payload)
    parsed = json.loads(out.decode("utf-8").rstrip("\n"))
    assert parsed["type"] == "session_created"
    assert isinstance(parsed["session_id"], str)
    assert len(parsed["session_id"]) == 36  # UUID string length
