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
audio2score-mcp: score_to_notes(song.mid) -> song.notes.json
                        |
                        v
daw-mcp: batch_set_notes(notes=<song.notes.json contents>) writes the clip
```

`score_to_notes` is the bridge script: it reads a `.mid` *or* `.musicxml`
file's notes via music21 and writes them out already shaped as
`batch_set_notes`' ultra-lean `[x, y, velocity, duration]` array - format-
agnostic on purpose, so an Audiveris-derived `.mxl` (see "Explicitly out
of scope" below) needs no separate conversion step either. Still a manual
last step — Claude (or you) reads the `.notes.json` file and passes its
contents into `batch_set_notes` — but the format translation itself is no
longer hand-done. Verified live against a running Bitwig instance (see
CHANGELOG.md v1.1.0) — chords, beat units, and velocity all round-trip
exact.

## Explicitly out of scope

- Anything past MusicXML - PDF, audio, tab, or MIDI export, in any
  direction. `score_to_midi.py` and `score_to_pdf.py` both existed
  briefly (fully built and verified working, not just planned) and were
  removed once checked against what's actually needed: notation apps
  already open MusicXML and export all of these themselves once it
  exists, and `score_to_notes.py` never needed the MIDI hop `score_to_midi.py`
  was built for in the first place. See CHANGELOG.md v1.2.0 through v2.0.0
  for the full built-then-removed history, and CLAUDE.md for the technical
  findings from that attempt (MuseScore's real `-j` converter-mode
  behavior, Guitar Pro's total lack of a CLI) - worth knowing before
  re-proposing this, even though the code is gone.
- PDF (scanned/typeset sheet music) → MusicXML *isn't* out of scope in the
  sense of "impossible" - Audiveris (already installed) does real OMR,
  confirmed working on real sheet music. It's out of scope for *this
  project to wrap*: it's a manual one-off command
  (`Audiveris.exe -batch -export ...`), not something worth scripting
  when its output feeds `score_to_notes.py` directly with no glue needed.
- No stem separation, no multi-instrument splitting
