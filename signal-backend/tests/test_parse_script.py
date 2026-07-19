from services.script_svc import (
    extract_title,
    parse_script,
    spoken_word_count,
    strip_audio_tags,
)

SCRIPT = """TITLE: The Ninety-Sixth Minute

### CHAPTER: Cold Open [intro]
[MAYA]: So I watched the whole thing twice. | delivery: neutral
[DEV]: [laughs] Twice? The match was three hours. | delivery: reaction
[MAYA]: The winner came in the ninety-sixth minute — I had to see how they built it. | delivery: thoughtful

### CHAPTER: The Final [core]
[DEV]: Okay, walk me through it, because I only saw the highlight. | delivery: question
[MAYA]: It starts with a throw-in, of all things — | delivery: interrupting
[DEV]: A throw-in? | delivery: reaction
[MAYA]: A throw-in. Forty yards out. And from there it's five passes, none of them touched grass. | delivery: neutral

### CHAPTER: What's Next [closer]
[MAYA]: So the question now is whether they can do it again in four years. | delivery: closer-beat
"""


def test_parse_full_script():
    title, cleaned = extract_title(SCRIPT)
    assert title == "The Ninety-Sixth Minute"
    segments, chapters = parse_script(cleaned)
    assert len(segments) == 8
    assert [c.role.value for c in chapters] == ["intro", "core", "closer"]
    assert segments[1].speaker == "DEV"
    assert segments[1].delivery == "reaction"
    # Inline audio tags survive in the spoken text (v3 renders them).
    assert "[laughs]" in segments[1].text


def test_unknown_delivery_soft_coerces():
    segments, _ = parse_script("[MAYA]: Sure. | delivery: bombastic")
    assert segments[0].delivery == "neutral"


def test_strip_audio_tags():
    assert strip_audio_tags("[laughs] Wait — really?") == "Wait — really?"
    assert strip_audio_tags("No tags here.") == "No tags here."


def test_spoken_word_count_excludes_tags():
    segments, _ = parse_script(
        "[DEV]: [sighs] Fine. | delivery: reaction"
    )
    assert spoken_word_count(segments) == 1


def test_no_chapter_markers_falls_back():
    segments, chapters = parse_script(
        "[MAYA]: Hello. | delivery: neutral\n[DEV]: Hi. | delivery: reaction"
    )
    assert len(segments) == 2
    assert len(chapters) == 1
    assert chapters[0].segment_indices == [0, 1]
