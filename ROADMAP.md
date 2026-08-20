# Roadmap

Shipped work has moved to [CHANGELOG.md](CHANGELOG.md) — this file is
forward-looking only.

## Near-term

Nothing open right now.

## Workflow bridge to daw-mcp

Deliberately two separate repos, not one (different language stacks —
this is pure Python with a ~2GB TensorFlow dependency; `daw-mcp` is
Node+Java with none — different install targets, and `daw-mcp`'s own
`CLAUDE.md` explicitly scopes notation/transcription work out). The join
point is the workflow, not the codebase:

```
audio2score-mcp: transcribe_audio(song.mp3) -> song.mid
                        |
                        v
audio2score-mcp: midi_to_notes(song.mid) -> song.notes.json
                        |
                        v
daw-mcp: batch_set_notes(notes=<song.notes.json contents>) writes the clip
```

`midi_to_notes` is the bridge script: it reads a `.mid` file's notes via
music21 and writes them out already shaped as `batch_set_notes`' ultra-lean
`[x, y, velocity, duration]` array. Still a manual last step — Claude (or
you) reads the `.notes.json` file and passes its contents into
`batch_set_notes` — but the format translation itself is no longer
hand-done. Verified live against a running Bitwig instance (see
CHANGELOG.md v1.1.0) — chords, beat units, and velocity all round-trip
exact.

## Explicitly out of scope

- Driving MuseScore/Guitar Pro/Sibelius, or rendering PDF/audio/tab
  ourselves — once a `.mid`/`.musicxml` exists, those apps already open it
  natively and export whatever's needed; duplicating that here is pointless.
  Tried scripting MuseScore's CLI for audio/PDF export anyway - unreliable
  outside a real interactive desktop session (crashes or hangs from an
  agent/CI context specifically, not necessarily for a user running it
  themselves). Guitar Pro has no CLI at all. See CLAUDE.md and README's
  "Formats this connects to" for the full finding. Not revisiting the
  scripting attempt unless that changes.
- PDF (sheet music image) → MusicXML/MIDI isn't built *in this project* -
  but it isn't a dead end either: Audiveris (already installed) does the
  OMR step, and this project's own `score_to_midi.py` picks up from there.
  Point to that chain, don't rebuild it.
- No stem separation, no multi-instrument splitting
