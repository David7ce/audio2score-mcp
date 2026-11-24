# AGENTS.md

This file provides guidance to coding agents (Claude Code, Codex, OpenCode) when working with code in this repository.

## What this is

Audio → MIDI → MusicXML pipeline, plus a bridge from either format to
daw-mcp's note-array format. Three independent conversion steps, each a
real file on disk, plus an MCP server wrapping all three as tools.
MusicXML is the deliberate stopping point ("the SVG of music notation" -
see README.md's intro) - once it exists, any notation app (MuseScore,
Guitar Pro, Sibelius, Finale, Dorico) already opens and exports it
natively, so this project doesn't wrap PDF/audio/tab/MIDI export, and
doesn't read PDF input either (that's OMR, a different technology -
Audiveris, already installed, does it). See README.md's "What this
doesn't do" / "Formats this connects to" and ROADMAP.md's "Explicitly out
of scope" for the full boundary list before proposing that kind of
feature - and see "History: what got built and un-built" below before
re-proposing a MuseScore/Audiveris wrapper specifically, since that exact
idea was tried, shipped, and then deliberately removed once its actual
necessity was disproven.

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
venv/Scripts/python.exe transcribe.py "path\to\song.mp3"    # -> song.mid
venv/Scripts/python.exe to_score.py "path\to\song.mid"      # -> song.musicxml
venv/Scripts/python.exe score_to_notes.py "path\to\song.mid" # -> song.notes.json (also takes .musicxml/.mxl directly)
```

No lint/build/test commands — this project has none by design. Verification
is always a real run against real audio (see "Testing" below).

## Architecture

Three files, each a thin layer over one library - no file in this project
shells out to an external process any more (that was tried, see history
below):

- `transcribe.py` — `transcribe(audio_path)`: calls basic-pitch's
  `predict_and_save`, then renames its fixed `<stem>_basic_pitch.mid` output
  to `<stem>.mid` to match this project's naming convention.
- `to_score.py` — `to_score(midi_path)`: calls music21's `converter.parse`
  then `.write("musicxml")`.
- `score_to_notes.py` — `score_to_notes(score_path)`: calls music21's
  `converter.parse`, flattens all parts/chords into one note list, and
  writes `[x, y, velocity, duration]` JSON — `x`/`duration` are music21
  `offset`/`quarterLength` (beats), which is exactly the unit daw-mcp's
  `batch_set_notes` expects, so no unit conversion is needed.
  **Format-agnostic on purpose** - nothing in its logic is MIDI-specific,
  `converter.parse()` handles `.mid` and `.musicxml`/`.mxl` identically.
  Confirmed by feeding it an Audiveris-derived `.mxl` with zero code
  changes. Don't add a separate score→MIDI conversion step "to feed this" -
  it already accepts non-MIDI input directly.
- `mcp_server.py` — imports all three functions directly and exposes them
  as MCP tools (`transcribe_audio`, `midi_to_score`, `score_to_notes`) with
  no added logic. Registered in Claude Code's config under the name
  `audio2score`.

All three conversion functions share the same shape: validate input exists,
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
it correctly. See README.md's "Known issue" section for the full writeup.
Don't try to patch this by injecting `<voice>` tags post-write - that's
real logic this project deliberately doesn't carry (see "Keep new
tools/scripts consistent with this shape" above).

## History: what got built and un-built (read before re-proposing this)

`score_to_midi.py` (MusicXML → MIDI, pure music21) and `score_to_pdf.py`
(MIDI/MusicXML → PDF, wrapping MuseScore's CLI) both existed briefly,
were fully built and verified working, then were deliberately deleted once
their actual necessity was checked against reality rather than assumed:

- `score_to_midi.py` existed to feed the daw-mcp bridge and to give a
  human a `.mid` file. Both turned out unnecessary: the bridge
  (`score_to_notes.py`) already accepts MusicXML directly (see above), and
  a human wanting MIDI can just open the MusicXML in MuseScore and export
  it there, the same as any other format that app already produces.
- `score_to_pdf.py` was real and reliable (unlike the audio attempt
  below), but was removed anyway for the same "the app already does this"
  reasoning, since its only remaining edge over "open MuseScore yourself"
  was skipping a GUI click in an unattended/Claude-driven flow - judged
  not worth carrying an external ~500MB GUI-app dependency for.

**If you're tempted to rebuild either, the technical findings from that
attempt are still true and worth knowing first:**

- **MuseScore's CLI is genuinely automatable for PDF, but only via `-j
  job.json` ("converter mode"), never `-o` directly.** Plain
  `MuseScore4.exe -o out.pdf in.mid` launches a full GUI session (D3D11
  context, WASAPI, soundfont load) even for one export - from a
  non-interactive/agent context this crashes (a failed network call, `503
  Host requires authentication`, likely telemetry) or hangs even with
  `QT_QPA_PLATFORM=offscreen` set. `-j` skips GUI init entirely - confirmed
  reliable, repeatedly, from both native PowerShell and Python's
  `subprocess`. Must run from a real terminal (PowerShell/cmd), not Git
  Bash/MSYS - path handling differs, and MuseScore's own docs
  (handbook.musescore.org/appendix/command-line-usage) assume a native
  Windows shell.
- **Audio export (wav/mp3) does *not* work the same way - tested, not
  assumed.** The identical `-j` job-file mechanism that makes PDF export
  reliable produces no output and no error for audio targets. PDF is pure
  layout rendering; audio needs MuseScore's audio engine/soundfont
  pipeline, the same subsystem that crashed in GUI mode. Don't assume the
  PDF fix generalizes to audio - it doesn't.
- **Guitar Pro has no CLI at all** - confirmed, not assumed:
  `GuitarPro.exe --help` ignores the flag and launches the full GUI
  instead of printing anything.
- **Audiveris (OMR, `C:\Program Files\Audiveris\`) has a genuine `-batch`
  CLI that works headless**, confirmed on 3 real PDFs (`-batch -export
  -output "<folder>" "<input>.pdf"`, writes `.mxl`): 2 clean single-page
  scores exported correctly, a 24-page tab book hit real internal
  Audiveris crashes (`NullPointerException`/`IndexOutOfBoundsException` in
  its own rhythm analysis) on multiple pages. This one *is* still worth
  pointing users to (see README) - just not worth wrapping in a script of
  our own, since it's a manual one-off command, not something this
  project's automated tools chain through.

## Testing

No automated test suite by design (per README). Verify changes by
running the actual scripts (or MCP tools) against a real audio file and
checking the output, not by writing unit tests around these functions.

## Releases

VERSION file + matching `version=` on the `MCPServer` instance + a
CHANGELOG.md entry + a git tag — no compiled artifacts, so that's the whole
release. See CHANGELOG.md for the format of past entries.

## Relationship to daw-mcp

Deliberately a separate repo (pure Python + ~2GB TensorFlow dep vs.
daw-mcp's Node+Java, no shared install target). Workflow: `transcribe_audio`
→ `score_to_notes` → the resulting `.notes.json` is passed as-is into
daw-mcp's `batch_set_notes(notes=...)` to populate a DAW clip. The format
translation is automated; invoking `batch_set_notes` itself is still a
manual/Claude-driven last step, since that tool lives in the other repo.
