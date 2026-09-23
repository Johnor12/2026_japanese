# CLAUDE.md

- New or edited decks must follow [CARD_RULES.md](CARD_RULES.md). The
  `deck.json` format and pitch notation are in [README.md](README.md).
- Build with `.venv/Scripts/python make_deck.py <folder>`. New audio needs
  `OPENAI_API_KEY` in the environment. Never write the key to a file in the repo.
- Only mark pitch accent (`pitch`) where you're sure of it; otherwise write a
  `pitch_note` alone.
- After generating audio, check it by transcribing the clips
  (`gpt-4o-transcribe` or `whisper-1`) and comparing them to `written`.
