import json

import pytest

from services.editorial_svc import parse_decision


def test_valid_json():
    raw = json.dumps({
        "topic_category": "sports",
        "register": "playful",
        "chosen_angle": "An underdog final nobody predicted.",
        "framing_note": None,
        "rationale": "It's a World Cup story — fun, not finance.",
    })
    d = parse_decision(raw)
    assert d.topic_category == "sports"
    assert d.register == "playful"
    assert d.framing_note is None


def test_fenced_json():
    raw = (
        "```json\n"
        '{"topic_category": "finance_markets", "register": "analytical", '
        '"chosen_angle": "Earnings beat expectations.", '
        '"framing_note": "investor framing fits: revenue and guidance", '
        '"rationale": "earnings story"}\n'
        "```"
    )
    d = parse_decision(raw)
    assert d.topic_category == "finance_markets"
    assert "investor" in d.framing_note


def test_garbage_raises():
    with pytest.raises(ValueError):
        parse_decision("I could not decide, sorry!")


def test_unknown_category_and_register_coerce():
    raw = json.dumps({
        "topic_category": "cryptozoology",
        "register": "operatic",
        "chosen_angle": "x",
        "framing_note": "null",
        "rationale": "y",
    })
    d = parse_decision(raw)
    assert d.topic_category == "general"
    assert d.register == "conversational"
    assert d.framing_note is None
