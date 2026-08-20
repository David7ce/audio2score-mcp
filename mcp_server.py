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
