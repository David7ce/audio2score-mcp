# audio2score-mcp Stage 2 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Wrap Stage 1's `transcribe()` and `to_score()` functions as an MCP server (`mcp_server.py`) exposing two tools, `transcribe_audio` and `midi_to_score`.

**Architecture:** One new file that imports the two existing functions as-is and registers them as MCP tools via the Python MCP SDK's `MCPServer` class. No changes to `transcribe.py`/`to_score.py`. No manual exception handling needed in the tool wrappers — verified against the installed SDK that it already converts an uncaught exception into a clean client-visible error.

**Tech Stack:** Python (same venv as Stage 1, 3.11), `mcp` (Python MCP SDK, version 2.0.0 — verified installed and introspected directly, not assumed from docs).

**Spec:** `docs/superpowers/specs/2026-08-20-mcp-server-stage2-design.md`

## Global Constraints

- **No changes to `transcribe.py` or `to_score.py`.** Both already have the right shape for this (`Path -> Path`, raise exceptions instead of `sys.exit`) — Stage 1's final review said explicitly not to refactor them for this stage.
- **No manual try/except in the tool wrapper functions.** Verified against the installed `mcp` 2.0.0 source
  (`venv/Lib/site-packages/mcp/server/mcpserver/tools/base.py:180-181`): any exception raised inside a tool
  function is caught by the SDK's tool-execution layer and re-raised as `ToolError(f"Error executing tool
  {self.name}: {e}") from e`, which is an MCP protocol error the client sees cleanly. Adding a redundant
  try/except in the wrapper would only produce a worse, duplicated error message.
- **Sync functions, not async.** `transcribe()`/`to_score()` are synchronous; the SDK's tool-registration code
  (`FuncMetadata`/`is_async_callable`, same file) detects and correctly calls sync tool functions — no `async
  def`, no `asyncio.to_thread` wrapping needed.
- **Two tools, not one combined tool.** Preserves the pause between MIDI and notation that Stage 1's two-script
  design is built around.
- **No automated test suite** — same stance as Stage 1. Verification is real invocations, but for an MCP server
  that means calling the server's own `list_tools()`/`call_tool()` methods directly (both are public `async`
  methods on `MCPServer`, confirmed via introspection) rather than standing up a full stdio subprocess + client
  harness for two tools.
- **Config registration is NOT part of this plan.** Adding the server to Claude Code's MCP config
  (`C:\Users\d7\.claude.json`, top-level `mcpServers` key) touches shared global state outside this repo, used
  across every other project session — the controller performs that step directly after this plan's task review
  passes, not a dispatched implementer. This plan's scope ends at "the server works when called directly."

---

## File Structure

```
audio2score-mcp/
├── requirements.txt    # gets one new line: mcp==2.0.0
├── mcp_server.py        # new: the MCP server
├── transcribe.py         # unchanged
└── to_score.py            # unchanged
```

---

### Task 1: `mcp_server.py` — MCP server wrapping both scripts

**Files:**
- Modify: `requirements.txt` (add `mcp==2.0.0`)
- Create: `mcp_server.py`

**Interfaces:**
- Consumes: `transcribe(audio_path: pathlib.Path) -> pathlib.Path` from `transcribe.py`, `to_score(midi_path: pathlib.Path) -> pathlib.Path` from `to_score.py` (both already exist, unchanged, imported directly).
- Produces: a module-level `mcp` object (an `MCPServer` instance) with two registered tools, `transcribe_audio(audio_path: str) -> str` and `midi_to_score(midi_path: str) -> str`. Nothing downstream in this plan consumes these — Task 1 is the whole plan.

- [ ] **Step 1: Add `mcp` to `requirements.txt`**

Add this line to the existing `requirements.txt` (keep the existing three lines exactly as they are):
```
mcp==2.0.0
```

- [ ] **Step 2: Confirm `mcp` is installed in the venv**

Run:
```bash
venv/Scripts/python.exe -m pip show mcp
```
Expected: `Version: 2.0.0` (already installed during plan research — this step just confirms it's still there and matches the pin, not a fresh install).

- [ ] **Step 3: Write `mcp_server.py`**

```python
#!/usr/bin/env python3
"""MCP server wrapping transcribe.py and to_score.py as tools."""
from pathlib import Path

from mcp.server import MCPServer

from transcribe import transcribe
from to_score import to_score

mcp = MCPServer("audio2score")


@mcp.tool()
def transcribe_audio(audio_path: str) -> str:
    """Transcribe an audio file to MIDI. Returns the path to the written .mid file."""
    return str(transcribe(Path(audio_path)))


@mcp.tool()
def midi_to_score(midi_path: str) -> str:
    """Convert a MIDI file to MusicXML. Returns the path to the written .musicxml file."""
    return str(to_score(Path(midi_path)))


if __name__ == "__main__":
    mcp.run()
```

- [ ] **Step 4: Verify both tools are registered correctly**

Run (from `audio2score-mcp/`):
```bash
venv/Scripts/python.exe -c "
import asyncio
from mcp_server import mcp

async def main():
    tools = await mcp.list_tools()
    for t in tools:
        print(t.name, '-', t.description)

asyncio.run(main())
"
```
Expected output (order may vary):
```
transcribe_audio - Transcribe an audio file to MIDI. Returns the path to the written .mid file.
midi_to_score - Convert a MIDI file to MusicXML. Returns the path to the written .musicxml file.
```

- [ ] **Step 5: Verify `transcribe_audio`'s error path**

Delete any existing `C:\Users\d7\Downloads\Curiosity__320kbps_.mid` and `.musicxml` from Stage 1's testing
first if they're still present (Stage 1's overwrite guard would otherwise make the real-run step below fail
immediately) — check with:
```bash
venv/Scripts/python.exe -c "import pathlib; print(pathlib.Path(r'C:\Users\d7\Downloads\Curiosity__320kbps_.mid').exists())"
```
If `True`, delete that file (and the `.musicxml` one) before continuing — these are regenerable artifacts from
Stage 1's own verification, not source.

Then run:
```bash
venv/Scripts/python.exe -c "
import asyncio
from mcp_server import mcp

async def main():
    try:
        result = await mcp.call_tool('transcribe_audio', {'audio_path': 'does-not-exist.mp3'})
        print('UNEXPECTED SUCCESS:', result)
    except Exception as e:
        print(f'{type(e).__name__}: {e}')

asyncio.run(main())
"
```
Expected: an exception is printed whose message contains `Audio file not found: does-not-exist.mp3` (the
message `transcribe()` raises) — not a raw unhandled traceback, and not a silent success.

- [ ] **Step 6: Verify `transcribe_audio`'s real path**

Run:
```bash
venv/Scripts/python.exe -c "
import asyncio
from mcp_server import mcp

async def main():
    result = await mcp.call_tool('transcribe_audio', {'audio_path': r'C:\Users\d7\Downloads\Curiosity__320kbps_.mp3'})
    print(result)

asyncio.run(main())
"
```
Expected: a `CallToolResult` whose content includes the text
`C:\Users\d7\Downloads\Curiosity__320kbps_.mid`, and that file exists on disk afterward with a non-zero size
(same real transcription pass as Stage 1 — several seconds to a couple of minutes, not a hang).

- [ ] **Step 7: Verify `midi_to_score`'s real path, chained from Step 6's output**

Run:
```bash
venv/Scripts/python.exe -c "
import asyncio
from mcp_server import mcp

async def main():
    result = await mcp.call_tool('midi_to_score', {'midi_path': r'C:\Users\d7\Downloads\Curiosity__320kbps_.mid'})
    print(result)

asyncio.run(main())
"
```
Expected: a `CallToolResult` whose content includes the text
`C:\Users\d7\Downloads\Curiosity__320kbps_.musicxml`, and that file exists on disk afterward.

- [ ] **Step 8: Confirm the CLI scripts still work standalone, unaffected**

The `.mid`/`.musicxml` files now exist from Steps 6-7, so this step only needs the overwrite guard's error path
(cheaper than a full re-run) to prove `transcribe.py`/`to_score.py` still import and run correctly on their own:
```bash
venv/Scripts/python.exe transcribe.py "C:\Users\d7\Downloads\Curiosity__320kbps_.mp3"
```
Expected: `Error: C:\Users\d7\Downloads\Curiosity__320kbps_.mid already exists; move or delete it first` on
stderr, exit code 1 — proving `transcribe.py` runs standalone exactly as it did at the end of Stage 1, with
`mcp_server.py`'s existence in the same directory having no effect on it.

- [ ] **Step 9: Commit**

```bash
git add requirements.txt mcp_server.py
git commit -m "Add mcp_server.py: MCP server wrapping transcribe.py and to_score.py as tools"
```

---

## End-to-end note

Task 1 is the entire plan — a single new file wrapping two already-tested functions is not large enough to
split further. After this task's review passes, the controller (not a dispatched subagent) registers the
server in Claude Code's MCP config, per the Global Constraints note above.
