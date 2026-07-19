from models import AudioProductionConfig, Chapter, ChapterRole, ScriptSegment
from services.audio_svc import derive_gaps
from services.tts_svc import build_tts_body, snap_v3_stability
from models import VoiceSettings


def _seg(delivery=None):
    return ScriptSegment(speaker="MAYA", text="hello there", delivery=delivery)


def test_gap_classes():
    segments = [
        _seg("neutral"),        # 0: chapter start -> 0
        _seg("reaction"),       # 1: short
        _seg("question"),       # 2: medium
        _seg("neutral"),        # 3: after a question -> short + 50
        _seg("transition"),     # 4: medium + 150
        _seg("neutral"),        # 5: new chapter start -> 0
        _seg("interrupting"),   # 6: short
    ]
    chapters = [
        Chapter(title="A", role=ChapterRole.intro, segment_indices=[0, 1, 2, 3, 4]),
        Chapter(title="B", role=ChapterRole.core, segment_indices=[5, 6]),
    ]
    cfg = AudioProductionConfig()
    gaps = derive_gaps(segments, chapters, cfg)
    assert gaps == [0, 120, 250, 170, 400, 0, 120]


def test_legacy_silence_becomes_medium():
    cfg = AudioProductionConfig.model_validate({"silence_duration_ms": 500})
    assert cfg.effective_medium_ms() == 500
    cfg2 = AudioProductionConfig.model_validate(
        {"silence_duration_ms": 500, "gap_medium_ms": 200}
    )
    assert cfg2.effective_medium_ms() == 200
    assert AudioProductionConfig().effective_medium_ms() == 250


def test_snap_v3_stability():
    assert snap_v3_stability(0.4) == 0.5
    assert snap_v3_stability(0.1) == 0.0
    assert snap_v3_stability(0.9) == 1.0


def test_tts_body_v3_keeps_tags_omits_v2_knobs():
    body = build_tts_body("[laughs] Sure.", "eleven_v3", VoiceSettings())
    assert body["text"] == "[laughs] Sure."
    assert body["voice_settings"]["stability"] == 0.5
    assert "style" not in body["voice_settings"]
    assert "speed" not in body["voice_settings"]


def test_tts_body_v2_strips_tags():
    body = build_tts_body("[laughs] Sure.", "eleven_multilingual_v2", VoiceSettings())
    assert body["text"] == "Sure."
    assert body["voice_settings"]["style"] == 0.5
