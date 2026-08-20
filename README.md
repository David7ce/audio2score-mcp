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
- `mcp_server.py` — MCP server wrapping both as tools (`transcribe_audio`, `midi_to_score`)

Each step is a separate, real artifact on disk — not a hidden intermediate.
The pause between MIDI and notation is deliberate: automatic transcription
is lossy, so the raw MIDI is worth a look (or a manual fix) before it
becomes a score.

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
```

Output always lands next to the input, same base filename, different
extension. Both scripts **refuse to overwrite an existing output file** —
delete or move it first if you want to re-run. Errors (missing input, a
library failure) print a clear message to stderr and exit non-zero; nothing
fails silently.

## Usage: MCP server

Registered in Claude Code's config as `audio2score` — restart Claude Code
after a fresh install for it to appear (MCP servers load at startup).

Two tools, mirroring the two scripts exactly:

- `transcribe_audio(audio_path)` → returns the `.mid` path
- `midi_to_score(midi_path)` → returns the `.musicxml` path

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
