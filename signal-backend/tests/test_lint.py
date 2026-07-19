from models import Chapter, ChapterRole, EditorialDecision, ScriptSegment
from services.lint_svc import lint


def _make(lines, title="A", role=ChapterRole.core):
    segments = [
        ScriptSegment(speaker=s, text=t, delivery=d) for s, t, d in lines
    ]
    chapters = [Chapter(
        title=title, role=role, segment_indices=list(range(len(segments)))
    )]
    return segments, chapters


GOOD_LINES = [
    ("MAYA", "So I watched the whole thing twice, and honestly the second time was better because you can see the shape of the collapse coming.", "neutral"),
    ("DEV", "Twice?", "reaction"),
    ("MAYA", "The winner came in the ninety-sixth minute. I had to see how they built it, pass by pass, from the throw-in all the way to the far post.", "thoughtful"),
    ("DEV", "Okay, walk me through it, because I only saw the highlight — what actually happened in the build-up?", "question"),
    ("MAYA", "It starts with a throw-in, of all things, forty yards out.", "neutral"),
    ("DEV", "A throw-in?", "reaction"),
    ("MAYA", "A throw-in. And from there it's five passes, none of them touched grass, and the last one is a backheel that shouldn't exist.", "neutral"),
    ("DEV", "Huh.", "reaction"),
]

SPORTS = EditorialDecision(
    topic_category="sports", register="playful", chosen_angle="the final"
)


def test_good_script_passes_clean():
    segments, chapters = _make(GOOD_LINES)
    report = lint(segments, chapters, SPORTS)
    assert not report.needs_revision, [f.detail for f in report.flags]


def test_uniform_turns_flagged():
    lines = [
        ("MAYA" if i % 2 == 0 else "DEV",
         "This is a sentence with exactly eleven words in it, okay there.",
         "neutral")
        for i in range(10)
    ]
    segments, chapters = _make(lines)
    report = lint(segments, chapters, SPORTS)
    assert any(f.rule == "turn_variance" and f.severity == "revise"
               for f in report.flags)


def test_finance_jargon_in_sports_episode_flagged():
    lines = list(GOOD_LINES)
    lines[4] = ("MAYA", "The club's valuation jumped after the match.", "neutral")
    segments, chapters = _make(lines)
    report = lint(segments, chapters, SPORTS)
    assert any(f.rule == "register_mismatch" for f in report.flags)


def test_finance_jargon_ok_in_finance_episode():
    lines = list(GOOD_LINES)
    lines[4] = ("MAYA", "The company's valuation jumped after earnings.", "neutral")
    segments, chapters = _make(lines)
    finance = EditorialDecision(
        topic_category="finance_markets", register="analytical",
        chosen_angle="earnings",
    )
    report = lint(segments, chapters, finance)
    assert not any(f.rule == "register_mismatch" for f in report.flags)


def test_digits_flagged():
    lines = list(GOOD_LINES)
    lines[4] = ("MAYA", "It starts in the 96th minute, 2-0 down.", "neutral")
    segments, chapters = _make(lines)
    report = lint(segments, chapters, SPORTS)
    assert any(f.rule == "unspeakable" and f.severity == "revise"
               for f in report.flags)


def test_stock_reaction_flagged():
    lines = list(GOOD_LINES)
    lines[7] = ("DEV", "Absolutely.", "reaction")
    segments, chapters = _make(lines)
    report = lint(segments, chapters, SPORTS)
    assert any(f.rule == "banned_phrases" for f in report.flags)


def test_no_questions_warns():
    lines = [(s, t.replace("?", "."), d) for s, t, d in GOOD_LINES]
    segments, chapters = _make(lines)
    report = lint(segments, chapters, SPORTS)
    assert any(f.rule == "missing_questions" for f in report.flags)


def test_no_short_reactions_warns():
    lines = [
        ("MAYA" if i % 2 == 0 else "DEV",
         f"Here is a fairly long explanatory sentence number {'x' * (i + 1)} "
         "that keeps going for a while and never lets the other host breathe "
         "or react to anything at all today?",
         "neutral")
        for i in range(6)
    ]
    segments, chapters = _make(lines)
    report = lint(segments, chapters, SPORTS)
    assert any(f.rule == "missing_reactions" for f in report.flags)
