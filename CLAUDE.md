# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

Audio → MIDI ⇄ MusicXML ⇄ PDF pipeline, plus a MIDI → daw-mcp note-array
bridge. Five independent conversion steps, each a real file on disk, plus
an MCP server wrapping all five as tools. No audio *output* direction
(score/MIDI → audio - tried it, doesn't work reliably even via the
mechanism that makes PDF export work) and no PDF-*reading* code of its own
(OMR is a different technology - Audiveris, already installed, does it and
hands off cleanly to this project's `score_to_midi.py`). No stem
separation, no driving Guitar Pro (no CLI exists to drive). See README.md's
"What this doesn't do" / "Formats this connects to" and ROADMAP.md's
"Explicitly out of scope" for the full boundary list before proposing that
kind of feature.

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
venv/Scripts/python.exe transcribe.py "path\to\song.mp3"         # -> song.mid
venv/Scripts/python.exe to_score.py "path\to\song.mid"           # -> song.musicxml
venv/Scripts/python.exe score_to_midi.py "path\to\song.musicxml" # -> song.mid
venv/Scripts/python.exe score_to_pdf.py "path\to\song.mid"       # -> song.pdf
venv/Scripts/python.exe midi_to_notes.py "path\to\song.mid"      # -> song.notes.json
```

No lint/build/test commands — this project has none by design. Verification
is always a real run against real audio (see "Testing" below).

## Architecture

Six files. Four are a thin layer over one Python library each; `score_to_pdf.py`
is the one exception, wrapping an external executable instead:

- `transcribe.py` — `transcribe(audio_path)`: calls basic-pitch's
  `predict_and_save`, then renames its fixed `<stem>_basic_pitch.mid` output
  to `<stem>.mid` to match this project's naming convention.
- `to_score.py` — `to_score(midi_path)`: calls music21's `converter.parse`
  then `.write("musicxml")`.
- `score_to_midi.py` — `score_to_midi(score_path)`: the reverse of
  `to_score.py` - `converter.parse` then `.write("midi")`. Symbolic-to-
  symbolic, pure music21, no external process.
- `score_to_pdf.py` — `score_to_pdf(score_path)`: writes a temporary
  MuseScore converter-mode job JSON (`[{"in": ..., "out": ...}]`) and runs
  `MuseScore4.exe -j <job.json>` via `subprocess.run`. The one script here
  that shells out - see the gotcha below for exactly why `-j` and not `-o`.
- `midi_to_notes.py` — `midi_to_notes(midi_path)`: calls music21's
  `converter.parse`, flattens all parts/chords into one note list, and
  writes `[x, y, velocity, duration]` JSON — `x`/`duration` are music21
  `offset`/`quarterLength` (beats), which is exactly the unit daw-mcp's
  `batch_set_notes` expects, so no unit conversion is needed.
- `mcp_server.py` — imports all five functions directly and exposes them as
  MCP tools (`transcribe_audio`, `midi_to_score`, `score_to_midi`,
  `score_to_pdf`, `midi_to_notes`) with no added logic. Registered in
  Claude Code's config under the name `audio2score`.

All five conversion functions share the same shape: validate input exists,
do the conversion, refuse to overwrite an existing output file, return the
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

**`score_to_pdf.py` gotcha - use `-j job.json`, never `-o` directly.**
Plain `MuseScore4.exe -o out.pdf in.mid` launches a full GUI session
(D3D11 context, WASAPI, soundfont load) even for one export - from a
non-interactive/agent context this is where it crashes (a failed network
call, `503 Host requires authentication`, likely telemetry) or hangs even
with `QT_QPA_PLATFORM=offscreen` set. `-j` ("converter mode") skips the
GUI init entirely and is what `score_to_pdf.py` actually uses - confirmed
reliable, repeatedly, from both native PowerShell and Python's
`subprocess`. Run it from a real terminal (PowerShell/cmd), not Git
Bash/MSYS - path handling differs and MuseScore's own docs
(handbook.musescore.org/appendix/command-line-usage) assume a native
Windows shell.

**Audio export (wav/mp3) does *not* work the same way - tested, not
assumed.** The identical `-j` job-file mechanism that makes PDF export
reliable produces no output and no error for audio targets. PDF is pure
layout rendering; audio needs MuseScore's audio engine/soundfont pipeline,
which is exactly the subsystem that was crashing in GUI mode too. Don't
build a `score_to_audio.py` assuming the PDF fix generalizes - it was
tried and it doesn't. Audio export stays manual (MuseScore's own File →
Export menu).

**Guitar Pro has no CLI at all** - confirmed, not assumed:
`GuitarPro.exe --help` ignores the flag and launches the full GUI instead
of printing anything. No batch/automation path exists to point to, unlike
MuseScore.

Audiveris (OMR, `C:\Program Files\Audiveris\`) has a genuine `-batch` CLI
that works headless, confirmed on 3 real PDFs (`-batch -export -output
"<folder>" "<input>.pdf"`, writes `.mxl`): 2 clean single-page scores
exported correctly, a 24-page tab book hit real internal Audiveris crashes
(`NullPointerException`/`IndexOutOfBoundsException` in its own rhythm
analysis) on multiple pages. Building an OMR pipeline is still out of this
project's scope - point users to Audiveris, then `score_to_midi.py` picks
up its `.mxl` output - but don't assume Audiveris succeeds on everything;
complex/multi-page/tab-heavy input is a real failure mode, not a
hypothetical one.

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
