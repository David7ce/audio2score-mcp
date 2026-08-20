# Changelog

## v2.0.1 — 2026-08-20

- Added a "run only what your goal needs" table to README.md. Audited all
  four files line-by-line for unused code first (imports, branches,
  requirements.txt pins) - found nothing to remove, every remaining line
  is load-bearing. The only real simplification left was documentation:
  nothing stops running all three tools in a chain, but only one goal
  (viewing scanned sheet music) ever needs zero of this project's own
  tools, and PDF→daw-mcp never needs the MIDI step. Wasn't written down
  anywhere before this.

## v2.0.0 — 2026-08-20

- **Removed `score_to_midi.py` and `score_to_pdf.py`**, both added earlier
  today (v1.2.0, v1.3.0), after checking their actual necessity against
  reality instead of assuming it: MusicXML is meant to be this project's
  hub format ("the SVG of music notation," per the README's own framing) -
  once it exists, notation apps already open and export it to anything
  (PDF, audio, tab, MIDI) themselves. Two specific things proved this
  wasn't hypothetical:
  - `midi_to_notes.py` (renamed `score_to_notes.py` in this release) was
    checked and confirmed **already format-agnostic** - `music21.converter.parse()`
    handles `.musicxml`/`.mxl` identically to `.mid`, verified by feeding
    it Audiveris OMR output directly with zero code changes. This removed
    `score_to_midi.py`'s entire reason for existing (it was built to
    bridge OMR output into a MIDI shape the notes-bridge supposedly
    needed - it never needed that shape at all).
  - `score_to_pdf.py` was genuinely reliable (see v1.3.0), but its only
    edge over "open MuseScore yourself" was skipping a GUI click in an
    unattended flow - not enough to justify carrying an external ~500MB
    GUI-app process dependency, once minimalism was the explicit goal.
  **Breaking change** (major version bump): `score_to_midi`/`score_to_pdf`
  MCP tools no longer exist, and `midi_to_notes` was renamed to
  `score_to_notes`.
- **Renamed `midi_to_notes.py` → `score_to_notes.py`** (function too:
  `midi_to_notes` → `score_to_notes`) to match what the code already did -
  the old name actively hid the redundancy above by implying a MIDI-only
  tool that would need a MusicXML→MIDI hop first. Verified after rename:
  ran directly on a real `.mxl` (OMR output), correct `.notes.json`
  produced, identical to before the rename.
- Rewrote README.md/CLAUDE.md/ROADMAP.md around the simplified 3-tool
  shape, keeping the MuseScore `-j`/Audiveris technical findings from the
  built-then-removed tools as reference material (CLAUDE.md's "History"
  section) rather than deleting hard-won knowledge along with the code.

## v1.3.0 — 2026-08-20

- **Corrected v1.2.1's own correction**: MuseScore's CLI *is* reliably
  automatable after all - the earlier fix ("it's sandbox-specific, try it
  yourself") undersold it. The real issue was using `-o out.pdf` (which
  always launches a full GUI session) and running it via Git Bash/MSYS.
  Switching to `-j job.json` ("converter mode", per MuseScore's own docs
  at handbook.musescore.org/appendix/command-line-usage - it explicitly
  "avoids the graphical user interface") from native PowerShell fixed it
  immediately: a real PDF, verified valid (`%PDF-1.4` header, correct page
  count).
- **Added `score_to_pdf.py`**: MIDI/MusicXML → PDF via MuseScore's
  converter mode, `subprocess.run`, a temp job-file. The one script in
  this project that shells out to an external executable rather than
  calling a Python library - documented clearly as the exception. Wired
  into `mcp_server.py` as a fifth tool. Verified via the real script (not
  just a manual PowerShell command) on a real transcribed song.
- **Tested audio export the same way and it does NOT work** - `-j`
  targeting `.wav`/`.mp3` produces no output and no error, unlike PDF.
  Audio needs MuseScore's audio engine/soundfont pipeline, the same
  subsystem that crashed in GUI mode - PDF's pure layout rendering doesn't
  touch it. Not building `score_to_audio.py`; documented as a real,
  tested negative result, not an assumption.
- **Ran the full pipeline on real files for the first time** (a real
  MP3 the user provided, and real downloaded Ode to Joy sheet music PDFs,
  not synthetic fixtures):
  - `Curiosity__320kbps_.mp3` → `transcribe_audio` → `midi_to_score` →
    `midi_to_notes` → `score_to_pdf`, all four steps producing real,
    verified output.
  - Two "Ode to Joy" PDFs → Audiveris OMR (`-batch -export`) → `.mxl` →
    `score_to_midi.py` → `.mid`. Sanity-checked the result: recognizable
    Ode to Joy melody (C-D-E-E-D-D-C-B...) with plausible left-hand chord
    accompaniment (G3+D4, A2+D3) - genuine OMR success on real sheet
    music, not just a clean synthetic test.
  - A third PDF (a 24-page guitar tab book, "back-in-black.pdf") failed -
    real internal Audiveris crashes on several pages. Kept as documented
    evidence of OMR's real failure mode (complex/multi-page/tab input),
    not glossed over.

## v1.2.1 — 2026-08-20

- **Corrected an overclaim**: v1.2.0 said scripting MuseScore's CLI is
  "unreliable" without qualification. Actually confirmed sandbox-specific
  - the crash/hang was tested from an agent's Bash tool with no normal
    interactive desktop/GPU session attached; a user running the same
  command from their own terminal may well have it work, since MuseScore's
  `-o` export is a real, commonly-documented feature. Reworded in
  README.md and CLAUDE.md to say so plainly, so a future reader doesn't
  conclude MuseScore's CLI is broken in general.
- **Added the confirmed Guitar Pro finding**: no CLI at all -
  `GuitarPro.exe --help` ignores the flag and opens the full GUI instead
  of printing help. Worse than MuseScore for automation, not equivalent.
- **Added PDF → MIDI as a named two-step workflow**: Audiveris OMR export
  → this project's own `score_to_midi.py`. Both pieces already existed
  separately; this just states the chain explicitly instead of leaving the
  reader to infer it.
- Restructured README.md: merged "What this doesn't do" and the old
  "Audio and PDF export" section into one tighter "Formats this connects
  to" table, removed duplicated crash-forensics narrative (kept in
  CLAUDE.md for future Claude sessions, trimmed to the essential fact for
  README's human readers), gave the MuseScore voice-tag bug its own
  heading instead of running on after the table.

## v1.2.0 — 2026-08-20

- **Added `score_to_midi.py`**: MusicXML (or other music21-readable score)
  → MIDI, the reverse of `to_score.py`. Pure music21 `parse()`/`write()`,
  same shape as every other script here. Wired into `mcp_server.py` as a
  fourth tool, `score_to_midi`. Verified round-trip on a synthetic 4-note
  fixture (C4-D4-E4-F4): MusicXML written, converted back to MIDI,
  re-parsed - exact pitches and durations preserved.
- **Decided against building automated audio-export or PDF-OMR tools** in
  this project, after actually attempting the audio-export one first:
  scripting MuseScore Studio's CLI (`-o out.wav`/`-o out.pdf`) is
  unreliable outside an interactive desktop session - without
  `QT_QPA_PLATFORM=offscreen` it crashed on a failed network call (`503
  Host requires authentication`); with it set, it hung indefinitely and
  had to be killed. MuseScore 4 spins up a full GUI session (D3D11
  context, WASAPI audio, soundfont loading) even for a plain export.
  Documented both directions instead, pointing at already-installed
  software for manual use: MuseScore Studio's own export menu for
  MIDI/MusicXML → audio or PDF, and Audiveris (confirmed present, and its
  `-batch -export` CLI genuinely works cleanly, unlike MuseScore's) for
  PDF → MusicXML via OMR. See README.md's new "Audio and PDF export"
  section and CLAUDE.md for the full writeup and the do-not-re-attempt
  note.

## v1.1.5 — 2026-08-20

- Added `workspace/` as the recommended input/output folder, replacing the
  ad-hoc use of `~/Downloads` from the previous session's testing -
  repo-local, gitignored (`workspace/*` with `.gitkeep` kept), survives
  a fresh clone without ever risking a committed audio file. Updated
  README.md's "Where files go" section and moved the existing test
  artifacts (`o_tannenbaum.*`, `alle_meine_entchen.*`) there.

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
