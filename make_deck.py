#!/usr/bin/env python3
"""Build an Anki deck (.apkg) from a deck folder.

    python make_deck.py <deck_folder> [--regen-audio]

The folder holds a deck.json (format in README.md, card rules in CARD_RULES.md).
Audio that doesn't exist yet is generated once with OpenAI text-to-speech
(needs OPENAI_API_KEY) and saved to <deck_folder>/audio/, so later builds reuse
it. The finished deck is written to <deck_folder>/<deck_folder>.apkg.
"""

import argparse
import hashlib
import html
import json
import os
import re
import sys
from pathlib import Path

import genanki

# Fixed so re-imports update existing notes instead of creating a new note type.
MODEL_ID = 1740318295

DEFAULT_TTS = {
    "model": "gpt-4o-mini-tts",
    "voice": "coral",
    "instructions": (
        "Speak natural, standard Tokyo Japanese like a friendly native speaker "
        "talking to a beginner. Pronounce clearly, a little slower than normal, "
        "with natural pitch accent and intonation. Say only the given text."
    ),
}

RECOMMENDED_SIZE = range(5, 8)
ID_RE = re.compile(r"^[a-z0-9][a-z0-9_]*$")
CJK_RE = re.compile(r"[　-ヿ㐀-鿿＀-￯]+")
SMALL_KANA = set("ゃゅょぁぃぅぇぉゎャュョァィゥェォヮ")
DOWNSTEP = "ꜜ"
RISE = "↗"


# ---------------------------------------------------------------- loading

def load_deck(folder: Path) -> dict:
    path = folder / "deck.json"
    if not path.exists():
        sys.exit(f"error: {path} not found")
    deck = json.loads(path.read_text(encoding="utf-8"))

    errors = []
    for key in ("name", "phrases"):
        if not deck.get(key):
            errors.append(f"deck is missing '{key}'")
    seen = set()
    for i, p in enumerate(deck.get("phrases", [])):
        where = f"phrase {i} ({p.get('id', '?')})"
        for key in ("id", "kana", "written", "english", "context"):
            if not p.get(key):
                errors.append(f"{where}: missing '{key}'")
        pid = p.get("id", "")
        if pid and not ID_RE.match(pid):
            errors.append(f"{where}: id must be lowercase letters, digits, underscores")
        if pid in seen:
            errors.append(f"{where}: duplicate id")
        seen.add(pid)
        if " " in p.get("kana", "") and not p.get("words"):
            errors.append(f"{where}: phrases need a 'words' breakdown")
    if errors:
        sys.exit("error: invalid deck.json\n  " + "\n  ".join(errors))

    n = len(deck["phrases"])
    if n not in RECOMMENDED_SIZE:
        print(f"warning: {n} phrases; decks should have "
              f"{RECOMMENDED_SIZE.start}-{RECOMMENDED_SIZE.stop - 1}")
    return deck


# ---------------------------------------------------------------- audio

def tts_settings(deck: dict) -> dict:
    return {**DEFAULT_TTS, **deck.get("tts", {})}


def audio_name(slug: str, phrase: dict, tts: dict) -> str:
    # The hash changes whenever the spoken text or voice settings change, so
    # edited phrases get fresh audio instead of silently keeping the old clip.
    key = json.dumps([phrase["written"], tts["model"], tts["voice"], tts["instructions"]],
                     ensure_ascii=False)
    digest = hashlib.sha256(key.encode("utf-8")).hexdigest()[:8]
    return f"{slug}_{phrase['id']}_{digest}.mp3"


def synthesize(client, text: str, tts: dict, dest: Path) -> None:
    tmp = dest.with_suffix(".part")
    with client.audio.speech.with_streaming_response.create(
        model=tts["model"],
        voice=tts["voice"],
        input=text,
        instructions=tts["instructions"],
        response_format="mp3",
    ) as response:
        response.stream_to_file(tmp)
    tmp.replace(dest)


def ensure_audio(folder: Path, deck: dict, regen: bool) -> dict:
    """Return {phrase id: audio path}, generating any clips that are missing."""
    slug = folder.name
    tts = tts_settings(deck)
    audio_dir = folder / "audio"
    audio_dir.mkdir(exist_ok=True)

    paths = {p["id"]: audio_dir / audio_name(slug, p, tts) for p in deck["phrases"]}
    todo = [p for p in deck["phrases"] if regen or not paths[p["id"]].exists()]

    if todo:
        if not os.environ.get("OPENAI_API_KEY"):
            sys.exit(f"error: {len(todo)} audio clip(s) need generating; set OPENAI_API_KEY")
        from openai import OpenAI
        client = OpenAI()
        for p in todo:
            print(f"  generating audio: {paths[p['id']].name}")
            synthesize(client, p["written"], tts, paths[p["id"]])

    # Drop clips for phrases that were removed or whose text changed.
    keep = {path.name for path in paths.values()}
    for old in audio_dir.glob(f"{slug}_*.mp3"):
        if old.name not in keep:
            print(f"  removing stale audio: {old.name}")
            old.unlink()
    return paths


# ---------------------------------------------------------------- rendering

def ja(text: str) -> str:
    """HTML-escape text and tag Japanese runs so phones pick Japanese glyphs."""
    return CJK_RE.sub(lambda m: f'<span lang="ja">{m.group()}</span>', html.escape(text))


def morae(kana: str) -> list:
    out = []
    for ch in kana:
        if ch in SMALL_KANA and out:
            out[-1] += ch
        else:
            out.append(ch)
    return out


def render_pitch(notation: str) -> str:
    """Draw Tokyo pitch accent as a line over the kana.

    Notation: words/phrases separated by spaces; ꜜ marks where pitch drops
    (after that mora); no ꜜ means flat (heiban); a trailing ↗ is question rise.
    """
    parts = []
    for word in notation.split():
        rise = word.endswith(RISE)
        word = word.rstrip(RISE)
        if word.count(DOWNSTEP) > 1:
            sys.exit(f"error: pitch '{word}' has more than one {DOWNSTEP}")
        before, _, _ = word.partition(DOWNSTEP)
        accent = len(morae(before)) if DOWNSTEP in word else 0
        mora = morae(word.replace(DOWNSTEP, ""))

        heights = []
        for i in range(1, len(mora) + 1):
            if accent == 1:
                heights.append(i == 1)
            else:
                heights.append(i > 1 and (accent == 0 or i <= accent))

        spans = []
        for i, (m, high) in enumerate(zip(mora, heights)):
            cls = ["hi" if high else "lo"]
            if high and i > 0 and not heights[i - 1]:
                cls.append("up")
            if high and i + 1 < len(mora) and not heights[i + 1]:
                cls.append("down")
            spans.append(f'<span class="{" ".join(cls)}">{html.escape(m)}</span>')
        if rise:
            spans.append(f'<span class="rise">{RISE}</span>')
        parts.append(f'<span class="pw">{"".join(spans)}</span>')
    return " ".join(parts)


def render_words(words: list) -> str:
    rows = []
    for w in words:
        kanji = f'<span class="w-kanji">{ja(w["kanji"])}</span>' if w.get("kanji") else ""
        romaji = f'<span class="w-romaji">{html.escape(w["romaji"])}</span>' if w.get("romaji") else ""
        rows.append(
            f'<div class="w-jp"><span class="w-kana" lang="ja">{html.escape(w["kana"])}</span>{kanji}</div>'
            f'<div class="w-en">{romaji}{ja(w["meaning"])}</div>'
        )
    return f'<div class="words">{"".join(rows)}</div>'


# ---------------------------------------------------------------- anki

JP_BLOCK = """
<div class="jp">
  <div class="kana" lang="ja">{{furigana:Kana}}</div>
  {{#Pitch}}<div class="pitch" lang="ja">{{Pitch}}</div>{{/Pitch}}
  {{#PitchNote}}<div class="pitch-note">{{PitchNote}}</div>{{/PitchNote}}
  <div class="audio">{{Audio}}</div>
</div>
"""

EXPLANATION = """
{{#Words}}<div class="label">Word by word</div>{{Words}}{{/Words}}
{{#Context}}<div class="label">In Japan</div><div class="context">{{Context}}</div>{{/Context}}
"""

CSS = """
.card {
  --bg: #fbf8f3; --fg: #22252a; --muted: #6d7179; --line: #e4ded4;
  --accent: #c2410c; --panel: #f3eee6;
  font-family: system-ui, -apple-system, "Segoe UI", Roboto, sans-serif;
  font-size: 17px; line-height: 1.5; text-align: center;
  color: var(--fg); background: var(--bg); padding: 12px 16px;
}
.card.nightMode, .card.night_mode, .nightMode .card, .night_mode .card {
  --bg: #1d1f23; --fg: #ebe7e0; --muted: #9a9ea6; --line: #3a3d44;
  --accent: #fb923c; --panel: #26292e;
}
.prompt { font-size: 12px; letter-spacing: .1em; text-transform: uppercase;
  color: var(--muted); margin-bottom: 14px; }
.kana { font-size: 32px; line-height: 1.8; }
.kana rt { font-size: .42em; color: var(--muted); }
.pitch { font-size: 19px; margin-top: 6px; color: var(--muted); }
.pw { display: inline-block; margin: 0 .25em; white-space: nowrap; }
.pw span { display: inline-block; padding: 1px 1px 2px; border: 0 solid var(--accent); }
.pw .hi { border-top-width: 2px; }
.pw .lo { border-bottom-width: 2px; }
.pw .up { border-left-width: 2px; }
.pw .down { border-right-width: 2px; }
.pw .rise { color: var(--accent); font-weight: 700; }
.pitch-note { font-size: 14px; color: var(--muted); max-width: 30em;
  margin: 6px auto 0; }
.audio { margin-top: 10px; }
hr#answer { border: 0; border-top: 1px solid var(--line); margin: 18px 0; }
.english { font-size: 23px; font-weight: 600; }
.label { font-size: 12px; letter-spacing: .1em; text-transform: uppercase;
  color: var(--muted); text-align: left; margin: 20px 0 6px; }
.words { display: grid; grid-template-columns: auto 1fr; gap: 6px 14px;
  text-align: left; background: var(--panel); border-radius: 10px; padding: 10px 12px; }
.w-kana { font-size: 18px; }
.w-kanji { display: block; font-size: 13px; color: var(--muted); }
.w-romaji { font-style: italic; color: var(--accent); margin-right: 6px; }
.context { text-align: left; }
"""


def build_model() -> genanki.Model:
    return genanki.Model(
        MODEL_ID,
        "Japan Playbook (audio, pitch, both directions)",
        fields=[{"name": n} for n in
                ("Kana", "Audio", "Pitch", "PitchNote", "English", "Words", "Context")],
        templates=[
            {
                "name": "Japanese → English",
                "qfmt": '<div class="prompt">What does this mean?</div>' + JP_BLOCK,
                "afmt": '{{FrontSide}}<hr id="answer"><div class="english">{{English}}</div>'
                        + EXPLANATION,
            },
            {
                "name": "English → Japanese",
                "qfmt": '<div class="prompt">Say it in Japanese</div>'
                        '<div class="english">{{English}}</div>',
                "afmt": '{{FrontSide}}<hr id="answer">' + JP_BLOCK + EXPLANATION,
            },
        ],
        css=CSS,
    )


def stable_id(text: str) -> int:
    return (1 << 30) | int(hashlib.sha256(text.encode("utf-8")).hexdigest()[:7], 16)


def build_package(folder: Path, deck: dict, audio: dict) -> Path:
    slug = folder.name
    model = build_model()
    anki_deck = genanki.Deck(stable_id(deck["name"]), deck["name"], deck.get("description", ""))
    tags = deck.get("tags", [])

    for p in deck["phrases"]:
        anki_deck.add_note(genanki.Note(
            model=model,
            fields=[
                html.escape(p["kana"]),
                f"[sound:{audio[p['id']].name}]",
                render_pitch(p["pitch"]) if p.get("pitch") else "",
                ja(p.get("pitch_note", "")),
                ja(p["english"]),
                render_words(p["words"]) if p.get("words") else "",
                ja(p["context"]),
            ],
            guid=genanki.guid_for(slug, p["id"]),
            tags=tags,
        ))

    out = folder / f"{slug}.apkg"
    package = genanki.Package(anki_deck)
    package.media_files = [str(path) for path in audio.values()]
    package.write_to_file(str(out))
    return out


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("folder", type=Path, help="deck folder containing deck.json")
    parser.add_argument("--regen-audio", action="store_true",
                        help="regenerate every audio clip, even ones that exist")
    args = parser.parse_args()

    folder = args.folder.resolve()
    deck = load_deck(folder)
    print(f"{deck['name']}: {len(deck['phrases'])} phrases")
    audio = ensure_audio(folder, deck, args.regen_audio)
    out = build_package(folder, deck, audio)
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
