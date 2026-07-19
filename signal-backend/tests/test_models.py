"""Back-compat: old clients still send the 8-dimension style block."""

from models import Episode, EpisodeRequest

LEGACY_PAYLOAD = {
    "article_ids": ["abc"],
    "style": {
        "depth": "deep_dive",
        "tone": "debate",
        "lens": "investor",
        "pacing": "rapid",
        "humor": "roast",
        "audience": "insider",
        "structure": "contrarian",
        "closer": "prediction",
    },
    "focus": "the fed decision",
    "target_minutes": 20,
}


def test_legacy_style_payload_is_ignored():
    req = EpisodeRequest.model_validate(LEGACY_PAYLOAD)
    assert req.article_ids == ["abc"]
    assert req.focus == "the fed decision"
    assert not hasattr(req, "style")


def test_episode_response_keeps_style_shim():
    # iOS decodes Episode.style non-optionally with the legacy enum values.
    ep = Episode(article_ids=["abc"])
    dumped = ep.model_dump()
    assert dumped["style"]["tone"] == "casual"
    assert dumped["style"]["lens"] == "investor"
    assert dumped["editorial"] is None
