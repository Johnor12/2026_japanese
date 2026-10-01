# Card rules

Every deck in this repo follows these rules. `make_deck.py` enforces the
checkable ones (required fields, word breakdowns, deck size warning).

## Content

- **One phrase or one word per card.** Never a list of unrelated words.
- **Small decks: 5–7 phrases**, each built around one real situation (a
  "playbook"), for example small talk or asking for help on transit.
- **Don't repeat phrases the learner already has.** The phrases in
  `essential_phrases/` (こんにちは, すみません, えきは どこですか,
  もういちど おねがいします, etc.) and `service_getting_around/` are already
  known.

## Japanese side

- **Hiragana**, written with spaces between words to make it easier to read.
  Loanwords and foreign names are written in katakana, as they are in Japan,
  with hiragana furigana over them: `アメリカ[あめりか]から きました`.
- **Audio** of the phrase, generated once with OpenAI text-to-speech and
  stored in the repo.
- **Tonality**, when it helps: a pitch-accent line drawn over the kana (`pitch`)
  and/or a one-line note on how to say it (`pitch_note`). Only include a pitch
  line when the accent is known for sure. When it isn't, use a note alone.

## English side

- **English meaning.**
- **Short explanation**, with:
  - **Word by word:** the meaning of each word (kana, romaji, kanji if any).
    Required for every phrase.
  - **Japanese context** for every card: when to use it, what you'll hear
    back, and any etiquette.
  - **Tonality.** The tonality from the Japanese side is shown on every answer.

## Both directions

Each phrase makes two cards:

1. **Japanese → English:** the front has the kana, pitch and audio (plays
   automatically). The back has the English meaning and the explanation.
2. **English → Japanese:** the front has the English meaning only. The back
   has the kana, pitch, audio and explanation. The word breakdown stays on the
   back so it doesn't give away the answer.

## Personalization

Write phrases and context for this trip: an American couple from
Charleston, SC, on their honeymoon, spending 5 days in Tokyo, 2 nights at a
ryokan in Hakone, and 6 days in Kyoto. They're beginners who know about 20
phrases. Use polite (です/ます) forms.
