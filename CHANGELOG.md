# Changelog

## v1.1.0 — 2026-08-20

- Added `midi_to_notes.py`: MIDI file → JSON note array in daw-mcp's
  `batch_set_notes` format (`[x, y, velocity, duration]`, beat-position
  units matching music21's `offset`/`quarterLength` exactly). Wired into
  `mcp_server.py` as a third tool (`midi_to_notes`) — completes the
  workflow bridge to daw-mcp.
- Added `CLAUDE.md` for future Claude Code instances working in this repo.

## v1.0.0 — 2026-08-20

- **Stage 1** — `transcribe.py` (audio→MIDI via basic-pitch) and
  `to_score.py` (MIDI→MusicXML via music21), plain CLI scripts. Verified
  end-to-end against a real 320kbps MP3.
- **Stage 2** — `mcp_server.py` wraps both as MCP tools (`transcribe_audio`,
  `midi_to_score`), registered in Claude Code's config as `audio2score`.
- `README.md` covering setup, CLI usage, MCP usage, and the known
  retry/overwrite-guard caveat.
- First tagged release. No compiled artifacts here (unlike `daw-mcp`'s Java
  jar + bundled JS), so a release is just a `VERSION` file, a matching
  `version=` on the `MCPServer` instance, and a git tag — anyone using it
  clones the repo and follows the README's setup steps.
