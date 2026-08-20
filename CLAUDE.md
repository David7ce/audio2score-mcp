# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

Audio → MIDI ⇄ MusicXML pipeline, plus a MIDI → daw-mcp note-array bridge.
Four independent conversion steps, each a real file on disk, plus an MCP
server wrapping all four as tools. No audio *output* direction
(score/MIDI → audio), no PDF input (needs OMR), no stem separation, no
notation-app driving — see README.md's "What this doesn't do" /
"Audio and PDF export" and ROADMAP.md's "Explicitly out of scope" for the
full boundary list, and what to point to instead (MuseScore, Audiveris),
before proposing that kind of feature.

## Setup

Requires **Python 3.11 exactly** — `basic-pitch` pulls in TensorFlow 2.15,
whose wheels stop at cp311.

```bash
uv venv --python 3.11 venv
uv pip install -r requirements.txt --python venv/Scripts/python.exe
```

Dependencies are pinned exactly in requirements.txt (basic-pitch, music21,
setuptools, mcp) — there is no automated test suite, so a fresh venv
matching these exact pins is the substitute for one. Don't bump a pin
without re-verifying end-to-end against a real audio file. `setuptools` is
pinned specifically because newer versions break a transitive `resampy`
import `basic-pitch` needs.

## Commands

```bash
venv/Scripts/python.exe transcribe.py "path\to\song.mp3"        # -> song.mid
venv/Scripts/python.exe to_score.py "path\to\song.mid"          # -> song.musicxml
venv/Scripts/python.exe score_to_midi.py "path\to\song.musicxml" # -> song.mid
venv/Scripts/python.exe midi_to_notes.py "path\to\song.mid"     # -> song.notes.json
```

No lint/build/test commands — this project has none by design. Verification
is always a real run against real audio (see "Testing" below).

## Architecture

Five files, each a thin layer over one library:

- `transcribe.py` — `transcribe(audio_path)`: calls basic-pitch's
  `predict_and_save`, then renames its fixed `<stem>_basic_pitch.mid` output
  to `<stem>.mid` to match this project's naming convention.
- `to_score.py` — `to_score(midi_path)`: calls music21's `converter.parse`
  then `.write("musicxml")`.
- `score_to_midi.py` — `score_to_midi(score_path)`: the reverse of
  `to_score.py` - `converter.parse` then `.write("midi")`. Symbolic-to-
  symbolic, pure music21, no external process - unlike the audio/PDF
  export directions below, this one stays inside this project because it
  doesn't need a renderer or synth.
- `midi_to_notes.py` — `midi_to_notes(midi_path)`: calls music21's
  `converter.parse`, flattens all parts/chords into one note list, and
  writes `[x, y, velocity, duration]` JSON — `x`/`duration` are music21
  `offset`/`quarterLength` (beats), which is exactly the unit daw-mcp's
  `batch_set_notes` expects, so no unit conversion is needed.
- `mcp_server.py` — imports all four functions directly and exposes them as
  MCP tools (`transcribe_audio`, `midi_to_score`, `score_to_midi`,
  `midi_to_notes`) with no added logic. Registered in Claude Code's config
  under the name `audio2score`.

All four conversion functions share the same shape: validate input exists,
call the library, refuse to overwrite an existing output file, return the
output `pathlib.Path`. `main()` in each script is just an argparse wrapper
that catches `(FileNotFoundError, RuntimeError)` and prints to stderr with
exit code 1. Keep new tools/scripts consistent with this shape rather than
introducing a different error-handling style.

Output always lands next to the input, same base filename, different
extension — never write elsewhere.

**MCP server gotcha:** if a `transcribe_audio` call times out or gets
cancelled client-side, basic-pitch may still be running in the background
and will finish writing the `.mid` file regardless. A retry then hits the
overwrite guard even though the first call looked like it failed — check
whether the `.mid` already exists before treating that as a bug.

**`to_score.py` gotcha:** on heavily polyphonic input (5+ simultaneous
voices, typically from real-audio transcription noise rather than a clean
melody), music21's MusicXML writer can omit the `<voice>` tag on some
`<note>` elements. Confirmed as a music21 writer limitation, not something
in this file's two-line parse+write logic - `score.makeNotation()` before
write doesn't fix it, and music21 re-parses its own output fine (just
warns and defaults those notes to voice 1). MuseScore Studio is stricter
and refuses to open the file, calling it "corrupted" - "Open anyway" loads
it correctly. See README.md's "What this doesn't do" for the full writeup.
Don't try to patch this by injecting `<voice>` tags post-write - that's
real logic this project deliberately doesn't carry (see "Keep new
tools/scripts consistent with this shape" above).

**Don't build a MuseScore-CLI-based tool in this repo.** Tested directly:
`MuseScore4.exe -o out.wav in.mid` crashes (fails a network call, `503 Host
requires authentication`) without `QT_QPA_PLATFORM=offscreen`, and hangs
indefinitely with it set. It launches a full GUI session (D3D11 context,
WASAPI, soundfont load) for a plain export - not a lightweight headless
converter, and not reliably scriptable from an agent/CI context on this
machine. Audio/PDF export via MuseScore stays a manual, documented step
(README's "Audio and PDF export") - don't re-attempt automating it without
new evidence it's fixed. Audiveris (OMR, `C:\Program Files\Audiveris\`),
by contrast, has a genuine `-batch` CLI that responds cleanly - confirmed
via `-help` - but building an OMR pipeline is still out of this project's
scope; point users to it, don't wrap it.

## Testing

No automated test suite by design (per README/ROADMAP). Verify changes by
running the actual scripts (or MCP tools) against a real audio file and
checking the output, not by writing unit tests around these functions.

## Releases

VERSION file + matching `version=` on the `MCPServer` instance + a
CHANGELOG.md entry + a git tag — no compiled artifacts, so that's the whole
release. See CHANGELOG.md for the format of past entries.

## Relationship to daw-mcp

Deliberately a separate repo (pure Python + ~2GB TensorFlow dep vs.
daw-mcp's Node+Java, no shared install target). Workflow: `transcribe_audio`
→ `midi_to_notes` → the resulting `.notes.json` is passed as-is into
daw-mcp's `batch_set_notes(notes=...)` to populate a DAW clip. The format
translation is automated; invoking `batch_set_notes` itself is still a
manual/Claude-driven last step, since that tool lives in the other repo.
