# 2026_japanese

Anki "playbook" decks of Japanese phrases for the trip, with audio and pitch
accent, built for AnkiDroid. The card rules are in [CARD_RULES.md](CARD_RULES.md).

| Folder | Deck | Phrases |
|---|---|---|
| `essential_phrases/` | Japan Playbooks::Essential Phrases | 21 |
| `service_getting_around/` | Japan Playbooks::Service & Getting Around | 32 |
| `small_talk/` | Japan Playbooks::Small Talk | 7 |
| `transit_help/` | Japan Playbooks::Transit Help | 7 |

`essential_phrases/` and `service_getting_around/` were converted from the
original Travel Japanese decks, so they're bigger than the 5–7 phrase
guideline for new playbooks.

Each folder holds `deck.json` (phrases and metadata), `audio/` (generated
clips) and the built `<folder>.apkg`.

## Put a deck on your phone

Copy the `.apkg` to the phone (Drive, email, USB) and open it. AnkiDroid
imports it. Re-importing an updated build updates the existing cards; it
doesn't create duplicates.

## Build a deck

One-time setup:

```powershell
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
```

Build:

```powershell
$env:OPENAI_API_KEY = "sk-..."   # only needed if audio is missing
.venv\Scripts\python make_deck.py small_talk
```

The script validates `deck.json` and generates audio for any phrase that
doesn't have it yet. Existing clips are reused, so you only pay for TTS once.
It then writes `small_talk/small_talk.apkg`. Clip filenames include a hash of
the spoken text and voice settings. If you edit a phrase, its audio is
regenerated and the old clip is deleted. `--regen-audio` regenerates every
clip.

## deck.json

```json
{
  "name": "Japan Playbooks::Small Talk",
  "description": "Shown on the deck overview screen.",
  "tags": ["japan-playbook", "small-talk"],
  "tts": {"voice": "coral"},
  "phrases": [
    {
      "id": "shinkon_ryokou",
      "kana": "しんこんりょこうです",
      "written": "新婚旅行です。",
      "english": "We're on our honeymoon",
      "pitch": "しんこんりょꜜこうです",
      "pitch_note": "Low し, then high and level through りょ, dropping on こう.",
      "words": [
        {"kana": "しんこん", "romaji": "shinkon", "kanji": "新婚", "meaning": "newlywed"}
      ],
      "context": "When to use it, what you'll hear back, etiquette."
    }
  ]
}
```

| Field | Required | Notes |
|---|---|---|
| `id` | yes | Lowercase, digits, underscores. Keeps the card and audio stable across edits. |
| `kana` | yes | What's shown. `カタカナ[かたかな]` puts hiragana furigana over katakana. |
| `written` | yes | Normal Japanese spelling with kanji. Sent to text-to-speech so it reads the phrase correctly. |
| `english` | yes | Meaning. It's also the front of the English → Japanese card. |
| `words` | for phrases | Word-by-word breakdown. `kanji` and `romaji` are optional. |
| `context` | yes | Japanese context. |
| `pitch` | no | Pitch accent, drawn as a line over the kana (see below). |
| `pitch_note` | no | How to say it, in plain English. |
| `tts` (deck) | no | Overrides `model` (`gpt-4o-mini-tts`), `voice` (`coral`), `instructions`. |

### Pitch notation

This is Tokyo pitch accent, one entry per word, separated by spaces:

- `ꜜ` goes right after the sound where the pitch drops: `はじめまꜜして`
  becomes low は, high じめま, then low して.
- A word with no `ꜜ` is flat: low first sound, then high to the end
  (`のりかえは`).
- A trailing `↗` is the rise at the end of a question: `どꜜこですか↗`.

Particles belong to the word before them (`これは`, `しんじゅくに`). You can
leave out a word whose accent you're unsure of, or skip `pitch` and write a
`pitch_note` only.
