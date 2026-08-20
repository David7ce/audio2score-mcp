# Changelog

## v1.1.4 — 2026-08-20

- Added a "Where files go" section to README.md, up front before Setup -
  there was no fixed input/output convention documented in one place
  (it was implied by the CLI examples but never stated plainly): any path
  works for input, output always lands next to it, view the `.musicxml`
  by opening it directly in a notation app since nothing here launches one.

## v1.1.3 — 2026-08-20

- **Root-caused and documented a real user-reported bug**: MuseScore
  Studio refused to open `o_tannenbaum.musicxml` (from the README's
  worked example, real 45s recording), calling it "corrupted." Found the
  cause: music21's MusicXML writer omits the `<voice>` tag on 38 of 610
  `<note>` elements, only in this file's heavily polyphonic passages (up
  to 5 simultaneous voices, from basic-pitch detecting harmonics/artifacts
  on real audio) - the clean single-voice `alle_meine_entchen.musicxml`
  from the same test batch has zero voice-tag issues. Confirmed this is
  music21's writer, not `to_score.py`: explicitly calling
  `score.makeNotation()` before `write()` doesn't fix it, and re-parsing
  the file with music21 itself only warns and silently defaults those
  notes to voice 1 - MuseScore is simply stricter about it. Documented as
  a known limitation with a workaround ("Open anyway" loads it correctly)
  in README.md and CLAUDE.md, rather than patching the XML post-write to
  inject missing voice tags - that would be exactly the kind of added
  logic this project's thin-wrapper design deliberately avoids.

## v1.1.2 — 2026-08-20

- Added a worked example to `README.md`: a real run of all three scripts
  against a synthetic C-major-arpeggio WAV, actual terminal output and
  actual `.notes.json` contents included, not paraphrased. Caught a real
  transcription artifact in the process (worth documenting, not a bug) -
  basic-pitch split the decaying final note into two tied notes instead of
  one, which is exactly the "check the MIDI before trusting the score"
  lossiness the README already warned about, now shown rather than just
  asserted.

## v1.1.1 — 2026-08-20

- **Fixed a real crash in `transcribe.py`**: basic-pitch's `predict_and_save`
  prints unconditionally to stdout, including emoji status lines — this
  crashes with `UnicodeEncodeError` on a non-UTF-8 Windows console, and (more
  seriously) would corrupt `mcp_server.py`'s stdio JSON-RPC stream if a
  `transcribe_audio` call let it through uncaptured. Fixed by redirecting
  stdout with `contextlib.redirect_stdout` around the `predict_and_save`
  call. Found and verified via a synthetic 3-note WAV run through the full
  `transcribe.py` → `to_score.py` → `midi_to_notes.py` pipeline (correctly
  detected C4/E4/G4) — first real reproduction of the crash, since v1.0.0's
  verification MP3 apparently never hit this console-encoding path.

## v1.1.0 — 2026-08-20

- Added `midi_to_notes.py`: MIDI file → JSON note array in daw-mcp's
  `batch_set_notes` format (`[x, y, velocity, duration]`, beat-position
  units matching music21's `offset`/`quarterLength` exactly). Wired into
  `mcp_server.py` as a third tool (`midi_to_notes`) — completes the
  workflow bridge to daw-mcp.
- Added `CLAUDE.md` for future Claude Code instances working in this repo.
- **Verified the full bridge live**: a synthetic MIDI (note + 3-note chord +
  note, exercising the chord-flatten path) → `midi_to_notes.py` →
  `batch_set_notes` against a running Bitwig instance → `batch_get_notes`
  read back the identical 5-note array. Chord expansion, beat units, and
  velocity all round-tripped exact. Test track/clip deleted afterward.

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
