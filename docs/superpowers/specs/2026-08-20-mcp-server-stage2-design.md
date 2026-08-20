# audio2score-mcp — Stage 2 design: MCP server

## Purpose

Wrap Stage 1's two CLI scripts (`transcribe.py`, `to_score.py`) as an MCP
server, so the audio→MIDI→MusicXML pipeline is callable as a discoverable
tool instead of a manually-run command. This is a thin protocol layer, not
a rewrite: `transcribe()` and `to_score()` already have the right shape for
this (`Path -> Path`, exceptions instead of `sys.exit`) — Stage 1's final
code review noted this explicitly and said not to refactor them for this
stage. This spec doesn't.

## Non-goals

- No change to `transcribe.py`/`to_score.py`'s internal logic — Stage 2
  imports their functions as-is
- No combined "do both steps in one call" tool — the two-tool split
  preserves the pause between MIDI and notation that Stage 1's design is
  built around (inspect/fix the MIDI before it becomes a score)
- No reverse direction (score/MIDI → audio) — still out of scope, same as
  Stage 1
- No subprocess bridging to a different language — the server is Python,
  same as the scripts it wraps, using the Python MCP SDK (`mcp` on PyPI)
- No README yet — this spec is Stage 2 only; documentation is a separate,
  smaller follow-up once the tools exist to document

## Architecture

One new file, `mcp_server.py`, at the repo root next to the two scripts it
wraps. It imports `transcribe` from `transcribe.py` and `to_score` from
`to_score.py` as plain Python functions — no subprocess, no CLI
invocation of the existing scripts.

```
Claude ──(MCP, stdio)──► mcp_server.py ──imports──► transcribe.py, to_score.py
```

### Tools

**`transcribe_audio`**
- Input: `audio_path` (string, path to an audio file)
- Behavior: calls `transcribe(Path(audio_path))`
- Output: the resulting `.mid` path, as a string
- Error: `FileNotFoundError`/`RuntimeError` from `transcribe()` becomes an
  MCP error result carrying the exception's message — no new error text
  invented at this layer, just passed through

**`midi_to_score`**
- Input: `midi_path` (string, path to a MIDI file)
- Behavior: calls `to_score(Path(midi_path))`
- Output: the resulting `.musicxml` path, as a string
- Error: same pass-through pattern as `transcribe_audio`

Both tools are one-to-one wrappers. Neither tool chains into the other —
the caller (Claude, in practice) decides whether and when to call the
second tool with the first tool's output path, same manual chaining Stage
1 already has, just through MCP instead of two CLI invocations.

### Transport and registration

Stdio transport (the standard for a locally-run MCP server invoked by
Claude Code) — no networking, no port, no daemon beyond the process
Claude's MCP client starts and manages itself. Registered in Claude Code's
MCP config using this project's own venv interpreter
(`venv/Scripts/python.exe mcp_server.py`), matching the existing pattern
used for the `daw` MCP server in a sibling project — the plan will find
and match that config's actual format rather than assuming one.

## Data flow / error handling

- No files are read/written by `mcp_server.py` itself beyond what
  `transcribe()`/`to_score()` already do — same "next to the input, same
  base filename" behavior as Stage 1, no new output-location logic
- The overwrite guard and the "fail loudly, no silent fallback" behavior
  from Stage 1 apply unchanged, since this layer calls the same functions
  that already enforce them

## Environment

- Add `mcp` (Python MCP SDK) to `requirements.txt`, pinned to whatever
  version resolves cleanly in the existing venv — same pinning discipline
  as Stage 1's dependencies, for the same reason (this project's only
  verification method is real runs, so floating versions are a real risk,
  not a theoretical one)
- Same venv as Stage 1 (`venv/`, Python 3.11) — no new interpreter, no new
  venv

## Testing / verification

Real, not automated, matching Stage 1's stance:

1. Start the server and confirm it advertises both tools correctly (MCP
   client tool listing)
2. Call `transcribe_audio` with a real audio file, confirm it returns the
   correct `.mid` path and the file exists
3. Call `midi_to_score` with that `.mid` path, confirm it returns the
   correct `.musicxml` path and the file exists
4. Call either tool with a bad path, confirm the error surfaces clearly
   through MCP (not a crash, not a silent failure)
5. Confirm the CLI scripts (`transcribe.py`, `to_score.py`) still work
   standalone, unaffected by the new file's existence

## Future stages (not this spec)

- README / user-facing documentation (separate, smaller follow-up)
- Stage 3: reverse direction (MusicXML/MIDI → audio via a synth/soundfont)
