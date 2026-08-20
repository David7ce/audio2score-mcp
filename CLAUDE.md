# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

Audio → MIDI → MusicXML pipeline. Two independent conversion steps, each a
real file on disk, plus an MCP server wrapping both as tools. No reverse
direction, no stem separation, no notation-app driving — see README.md's
"What this doesn't do" and ROADMAP.md's "Explicitly out of scope" for the
full boundary list before proposing that kind of feature.

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
venv/Scripts/python.exe transcribe.py "path\to\song.mp3"   # -> song.mid
venv/Scripts/python.exe to_score.py "path\to\song.mid"     # -> song.musicxml
```

No lint/build/test commands — this project has none by design. Verification
is always a real run against real audio (see "Testing" below).

## Architecture

Four files, each a thin layer over one library:

- `transcribe.py` — `transcribe(audio_path)`: calls basic-pitch's
  `predict_and_save`, then renames its fixed `<stem>_basic_pitch.mid` output
  to `<stem>.mid` to match this project's naming convention.
- `to_score.py` — `to_score(midi_path)`: calls music21's `converter.parse`
  then `.write("musicxml")`.
- `midi_to_notes.py` — `midi_to_notes(midi_path)`: calls music21's
  `converter.parse`, flattens all parts/chords into one note list, and
  writes `[x, y, velocity, duration]` JSON — `x`/`duration` are music21
  `offset`/`quarterLength` (beats), which is exactly the unit daw-mcp's
  `batch_set_notes` expects, so no unit conversion is needed.
- `mcp_server.py` — imports all three functions directly and exposes them as
  MCP tools (`transcribe_audio`, `midi_to_score`, `midi_to_notes`) with no
  added logic. Registered in Claude Code's config under the name
  `audio2score`.

Both conversion functions share the same shape: validate input exists,
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

## Testing

No automated test suite by design (per README/ROADMAP). Verify changes by
running the actual scripts (or MCP tools) against a real audio file and
checking the output, not by writing unit tests around these two functions.

## Relationship to daw-mcp

Deliberately a separate repo (pure Python + ~2GB TensorFlow dep vs.
daw-mcp's Node+Java, no shared install target). Workflow: `transcribe_audio`
→ `midi_to_notes` → the resulting `.notes.json` is passed as-is into
daw-mcp's `batch_set_notes(notes=...)` to populate a DAW clip. The format
translation is automated; invoking `batch_set_notes` itself is still a
manual/Claude-driven last step, since that tool lives in the other repo.
