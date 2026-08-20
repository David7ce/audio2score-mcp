# audio2score-mcp — Stage 1 design

## Purpose

Turn a recorded audio file into an editable music score, as two discrete,
inspectable steps rather than one opaque conversion.

Scope is deliberately narrow: **audio → MIDI → MusicXML**, one direction
only. No multi-app suite, no MCP server yet, no reverse direction
(score/MIDI → audio). Those are later stages, not this one.

MusicXML is the target end format because it's the "SVG of music notation" —
an open, text-based format any notation app (MuseScore, Sibelius, Guitar
Pro, Finale, Dorico) can open, edit, and re-export without owning the
pipeline that produced it. This project does not open or drive any of those
apps; it only produces a `.musicxml` file for you to open in whichever one
you choose, by hand.

## Non-goals (Stage 1)

- No MCP server / no persistent process — plain CLI scripts, run manually
- No score/MIDI → audio (reverse direction)
- No stem separation, no multi-instrument splitting
- No automatic opening of MuseScore/Guitar Pro/Sibelius
- No unit tests — nothing here has business logic worth unit-testing; the
  two scripts are thin wrappers around external libraries. Verification is
  a real end-to-end run against real audio.

## Architecture

Two independent CLI scripts, chained manually, each producing one artifact
on disk. The pause between them is intentional: automatic music
transcription is lossy, so the raw MIDI is worth a look (or a manual fix)
before it gets quantized into notation.

```
audio.mp3 ──[transcribe.py]──► audio.mid ──[to_score.py]──► audio.musicxml
              (basic-pitch)                   (music21)
```

### `transcribe.py`

- Input: path to an audio file (`.mp3`, `.wav`, etc. — whatever basic-pitch
  accepts)
- Runs Spotify's `basic-pitch` polyphonic pitch-detection model over it
- Output: `<input-stem>.mid` written next to the input file
- On missing input file or a basic-pitch failure: fail loudly with a clear
  message, no silent fallback

### `to_score.py`

- Input: path to a MIDI file (normally `transcribe.py`'s output)
- Uses `music21` to parse the MIDI into a `Stream` and write it out as
  MusicXML
- Output: `<input-stem>.musicxml` written next to the input file
- On missing input file or a parse failure: fail loudly with a clear
  message, no silent fallback

## Data flow / file conventions

- Output files are always written next to their input, same directory,
  same base filename, different extension. No dedicated output folder, no
  configuration.
- Nothing is deleted or overwritten silently — if the target output file
  already exists, that's the user's problem to notice (Stage 1 has no
  `--force` flag or overwrite prompt; this is a manual, supervised tool).

## Environment

- Python virtual environment inside the project (`venv/`, gitignored)
- `requirements.txt` pinning `basic-pitch` and `music21`
- No other runtime dependencies

## Testing / verification

Real end-to-end run against `C:\Users\d7\Downloads\Curiosity__320kbps_.mp3`:

1. `transcribe.py` on the MP3 → confirm a `.mid` file appears and is
   non-empty / loads in a MIDI-aware tool
2. `to_score.py` on the resulting `.mid` → confirm a `.musicxml` file
   appears and opens cleanly (structurally valid XML, parseable by
   music21's own reader as a sanity check)

No automated test suite for Stage 1 — see Non-goals.

## Future stages (not this spec)

- Stage 2: wrap both scripts as one small MCP server
  (`transcribe_audio_to_score`, `score_to_midi` tools)
- Stage 3: reverse direction (MusicXML/MIDI → audio via a synth/soundfont),
  full round-trip
