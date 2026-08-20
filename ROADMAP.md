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

- Score/MIDI → **audio** — tested wrapping MuseScore's converter mode
  (`-j job.json`, the same mechanism that makes PDF export reliable) for
  wav/mp3 output; it produces nothing and no error. Audio needs
  MuseScore's audio engine, a different subsystem than PDF's pure layout
  rendering. Stays manual (MuseScore's own File → Export). Note: PDF
  export in the *other* direction (MIDI/MusicXML → PDF) is **not** out of
  scope any more - see CHANGELOG.md v1.3.0, it's `score_to_pdf.py` now.
- Driving Guitar Pro — no CLI exists at all (confirmed:
  `GuitarPro.exe --help` just opens the GUI), so there's nothing to wrap.
- No stem separation, no multi-instrument splitting
