# Roadmap

## Shipped

- **Stage 1** — `transcribe.py` (audio→MIDI via basic-pitch) and
  `to_score.py` (MIDI→MusicXML via music21), plain CLI scripts. Verified
  end-to-end against a real 320kbps MP3.
- **Stage 2** — `mcp_server.py` wraps both as MCP tools (`transcribe_audio`,
  `midi_to_score`), registered in Claude Code's config as `audio2score`.
- `README.md` covering setup, CLI usage, MCP usage, and the known
  retry/overwrite-guard caveat.

## Near-term

- **No release process exists yet.** Deliberately not building one until
  its shape is decided — see open question below.
- **README could use a worked example** — a full transcript of running
  both scripts (or both tools) against a real file, output included, so a
  new reader can tell what "working" looks like without running it
  themselves first.

## Open question: what does a "release" mean for this project?

Unlike `daw-mcp` (a sibling project with a compiled Java extension and a
bundled JS server, packaged into a distributable zip via `scripts/release.sh`),
this project has no compiled artifacts and no install step beyond a venv +
`pip install`. A "release" here is likely much lighter — a git tag plus a
version number, maybe a source archive excluding `venv/` — but the exact
shape hasn't been decided. Resolve this before building a release script,
not after.

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
daw-mcp: batch_set_notes(...) reads song.mid's notes into a Bitwig/Ableton clip
```

No tooling exists yet to automate that hand-off (reading a `.mid` file's
notes and translating them into `batch_set_notes`' note-array format) — for
now it's a manual step, or something Claude does by reading one tool's
output and calling the other. Worth a small bridge script only if this
hand-off turns out to happen often enough to be worth automating.

## Explicitly out of scope

- No reverse direction (score/MIDI → audio) — needs a synth/soundfont,
  not built
- No stem separation, no multi-instrument splitting
- Doesn't drive MuseScore/Guitar Pro/Sibelius directly — those already have
  their own separate MCP servers; this project only produces the
  interchange files
