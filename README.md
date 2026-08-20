# audio2score-mcp

Turn a recorded audio file into an editable music score: **audio → MIDI → MusicXML**.

MusicXML is the target because it's the "SVG of music notation" — an open,
text-based format any notation app (MuseScore, Sibelius, Guitar Pro, Finale,
Dorico) can open, edit, and re-export without owning the pipeline that
produced it. This project only produces the `.mid` and `.musicxml` files;
opening and editing them happens in whichever notation app you choose, by
hand.

Two ways to run it: as plain CLI scripts, or as an MCP server exposing the
same two steps as tools Claude can call.

## What's here

- `transcribe.py` — audio file → MIDI, via Spotify's [basic-pitch](https://github.com/spotify/basic-pitch)
- `to_score.py` — MIDI file → MusicXML, via [music21](https://www.music21.org/)
- `midi_to_notes.py` — MIDI file → JSON note array in daw-mcp's `batch_set_notes` format, via music21
- `mcp_server.py` — MCP server wrapping all three as tools (`transcribe_audio`, `midi_to_score`, `midi_to_notes`)

Each step is a separate, real artifact on disk — not a hidden intermediate.
The pause between MIDI and notation is deliberate: automatic transcription
is lossy, so the raw MIDI is worth a look (or a manual fix) before it
becomes a score.

## Where files go

There's no fixed input folder - point `audio_path`/`midi_path` at any file,
anywhere (e.g. `~/Downloads/song.mp3`). Every output lands **next to that
input file**, same base name, different extension:

```
~/Downloads/song.mp3          <- you put this here (any format basic-pitch/librosa reads: mp3, wav, ogg, flac...)
~/Downloads/song.mid          <- transcribe_audio writes this
~/Downloads/song.musicxml     <- midi_to_score writes this (open in MuseScore/Guitar Pro/Sibelius/Finale/Dorico)
~/Downloads/song.notes.json   <- midi_to_notes writes this (feed into daw-mcp's batch_set_notes)
```

To view: open the `.mid` or `.musicxml` directly in whatever notation app
you have - nothing here launches one for you (see "What this doesn't do").
If MuseScore calls the `.musicxml` "corrupted," see the polyphony caveat
below before assuming the file is broken.

## Setup

Requires **Python 3.11** specifically — `basic-pitch` pulls in TensorFlow
2.15, whose wheels stop at `cp311`; 3.12 and 3.13 will fail to resolve. The
resulting venv is ~2GB (full TensorFlow, not a lighter backend).

```bash
uv venv --python 3.11 venv
uv pip install -r requirements.txt --python venv/Scripts/python.exe
```

Dependencies are pinned exactly (`basic-pitch==0.4.0`, `music21==10.5.0`,
`setuptools==65.5.0`, `mcp==2.0.0`) — this project has no automated test
suite, so a fresh environment matching exactly what was verified is the
substitute. `setuptools` specifically is pinned because newer versions
break a transitive `resampy` import that `basic-pitch` needs.

## Usage: CLI

```bash
venv/Scripts/python.exe transcribe.py "C:\path\to\song.mp3"
# -> C:\path\to\song.mid

venv/Scripts/python.exe to_score.py "C:\path\to\song.mid"
# -> C:\path\to\song.musicxml

venv/Scripts/python.exe midi_to_notes.py "C:\path\to\song.mid"
# -> C:\path\to\song.notes.json  (daw-mcp's batch_set_notes format)
```

Output always lands next to the input, same base filename, different
extension. Both scripts **refuse to overwrite an existing output file** —
delete or move it first if you want to re-run. Errors (missing input, a
library failure) print a clear message to stderr and exit non-zero; nothing
fails silently.

## Worked example

A real run, not a hypothetical one. Input: a synthetic mono WAV, a C major
arpeggio (C4-E4-G4-C5, quarter notes with a short decaying envelope so
onsets are clean) - "real audio" in the sense this project cares about
(an actual waveform on disk, not hand-typed MIDI), just synthesized instead
of recorded, so the transcript is reproducible without a copyrighted file
lying around in a public repo.

```
$ venv/Scripts/python.exe transcribe.py c_major_arpeggio.wav
WARNING:root:Coremltools is not installed. ...
WARNING:root:tflite-runtime is not installed. ...
WARNING:root:onnxruntime is not installed. ...
Wrote c_major_arpeggio.mid

$ venv/Scripts/python.exe to_score.py c_major_arpeggio.mid
Wrote c_major_arpeggio.musicxml

$ venv/Scripts/python.exe midi_to_notes.py c_major_arpeggio.mid
Wrote c_major_arpeggio.notes.json
```

The three `WARNING:root` lines are basic-pitch noting that optional
backends (CoreML, TFLite, ONNX) aren't installed - harmless, TensorFlow is
the backend actually used, and this is exactly what `transcribe.py` v1.1.1
now correctly hides *without* corrupting `mcp_server.py`'s stdout stream
(see CHANGELOG.md) - it only lands on the terminal, not the MCP protocol
channel.

`c_major_arpeggio.notes.json`, the daw-mcp-ready output:

```json
[[0.0, 60, 83, 1.0], [1.25, 64, 80, 1.0], [2.3333, 67, 80, 1.0], [3.5, 72, 78, 0.5], [4.0, 72, 78, 0.5]]
```

Four notes went in (C4, E4, G4, C5); basic-pitch correctly detected pitch
and velocity for all four (60/64/67/72, matching the arpeggio exactly) but
split the last note (C5) into two consecutive entries instead of one -
the decaying envelope's tail apparently read as a second onset. This is
the automatic-transcription lossiness the "What's here" section above
warns about, caught in the wild on the very first note that had a
naturalistic (non-flat) volume shape: check the `.mid` before trusting the
`.musicxml`/`.notes.json` blindly, especially around sustained or decaying
notes.

`c_major_arpeggio.musicxml` opens cleanly in any notation app (verified
well-formed: correct MusicXML 4.0 DOCTYPE, `<step>`/`<octave>` pitches for
C4/E4/G4/G4/C5/C5/C5 - the split C5 shows up as tied notes across a
measure boundary, which is standard MusicXML for a note that doesn't fit
in one measure, not a second bug).

## Usage: MCP server

Registered in Claude Code's config as `audio2score` — restart Claude Code
after a fresh install for it to appear (MCP servers load at startup).

Three tools, mirroring the three scripts exactly:

- `transcribe_audio(audio_path)` → returns the `.mid` path
- `midi_to_score(midi_path)` → returns the `.musicxml` path
- `midi_to_notes(midi_path)` → returns the `.notes.json` path (daw-mcp's `batch_set_notes` note-array format)

Same behavior as the CLI underneath (same overwrite guard, same errors) —
the MCP server is a thin wrapper, not a different implementation.

**One thing to know if a call seems to hang:** if a `transcribe_audio` call
appears to time out or gets cancelled, the transcription may still be
running in the background and will finish writing the `.mid` file
regardless. A retry will then hit the overwrite guard ("already exists")
even though the first call looked like it never succeeded. This isn't a
bug — check whether the `.mid` already exists before retrying.

To register the server yourself elsewhere, add this to your MCP config
(`mcpServers`), using **absolute paths** for both fields — the client
launches stdio servers without a defined working directory, so relative
paths won't resolve:

```json
"audio2score": {
  "type": "stdio",
  "command": "<absolute path to>\\venv\\Scripts\\python.exe",
  "args": ["<absolute path to>\\mcp_server.py"],
  "env": {}
}
```

## What this doesn't do

- No reverse direction yet (score/MIDI → audio) — MIDI→audio needs a synth/soundfont, not built
- No stem separation or multi-instrument splitting
- Doesn't open or drive MuseScore/Guitar Pro/Sibelius — it produces `.musicxml`, you open it yourself
- No automated test suite by design — verification is always a real run against real audio

**Heavily polyphonic transcriptions can produce a `.musicxml` that MuseScore
Studio refuses to open, calling it "corrupted."** Root cause: music21's own
MusicXML writer omits the `<voice>` tag on some `<note>` elements when a
piece needs many simultaneous voices (5+) - verified on a real 45-second
recording that transcribed into dense, often-overlapping notes (a side
effect of basic-pitch picking up harmonics/artifacts on real audio, not a
clean single melodic line). Confirmed this is music21's writer, not this
project's code: `to_score.py` is a two-line `parse()` + `write()` call with
no note/voice logic of its own, and explicitly calling `score.makeNotation()`
before writing doesn't fix it either. Re-parsing the same file with music21
itself only warns (`Cannot put in an element with a missing voice tag`) and
recovers by defaulting those notes to voice 1 - MuseScore's importer is
simply stricter and rejects outright instead of tolerating it.
**Workaround: click "Open anyway"** - it loads fine, just with those specific
notes in voice 1 instead of their originally-detected voice, a minor layout
quirk, not lost data. Not seen on clean, low-polyphony input (a hand-authored
melody MIDI transcribed and re-verified with zero voice-tag issues) - this is
specific to messy, dense, real-audio-transcription output.
