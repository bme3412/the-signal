import re

from personas import HOSTS, MAYA, persona_prompt_block, voice_for


def test_host_keys_match_parser_regex():
    for key in HOSTS:
        assert re.fullmatch(r"[A-Z]+", key), key


def test_hosts_have_voices():
    for p in HOSTS.values():
        assert p.voice_id
        assert 0.0 <= p.voice_settings.stability <= 1.0


def test_voice_for_known_and_unknown():
    vid, settings = voice_for("MAYA")
    assert vid == MAYA.voice_id
    # Unknown speaker tags (e.g. legacy ALEX) fall back to the first host.
    fallback_vid, _ = voice_for("ALEX")
    assert fallback_vid == MAYA.voice_id


def test_prompt_block_mentions_both_hosts():
    block = persona_prompt_block("conversational")
    for key in HOSTS:
        assert key in block
