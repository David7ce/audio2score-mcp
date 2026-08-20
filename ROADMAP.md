# Roadmap

## Shipped

- **Stage 1** — `transcribe.py` (audio→MIDI via basic-pitch) and
  `to_score.py` (MIDI→MusicXML via music21), plain CLI scripts. Verified
  end-to-end against a real 320kbps MP3.
- **Stage 2** — `mcp_server.py` wraps both as MCP tools (`transcribe_audio`,
  `midi_to_score`), registered in Claude Code's config as `audio2score`.
- `README.md` covering setup, CLI usage, MCP usage, and the known
  retry/overwrite-guard caveat.
- **v1.0.0** — first tagged release. No compiled artifacts here (unlike
  `daw-mcp`'s Java jar + bundled JS), so a release is just a `VERSION`
  file, a matching `version=` on the `MCPServer` instance, and a git tag —
  anyone using it clones the repo and follows the README's setup steps.

## Near-term

- **README could use a worked example** — a full transcript of running
  both scripts (or both tools) against a real file, output included, so a
  new reader can tell what "working" looks like without running it
  themselves first.

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
