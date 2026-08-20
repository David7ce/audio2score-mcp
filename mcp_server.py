#!/usr/bin/env python3
"""MCP server wrapping transcribe.py and to_score.py as tools."""
from pathlib import Path

from mcp.server import MCPServer

from transcribe import transcribe
from to_score import to_score
from midi_to_notes import midi_to_notes as convert_midi_to_notes

mcp = MCPServer("audio2score", version="1.1.2")


@mcp.tool()
def transcribe_audio(audio_path: str) -> str:
    """Transcribe an audio file to MIDI. Returns the path to the written .mid file."""
    return str(transcribe(Path(audio_path)))


@mcp.tool()
def midi_to_score(midi_path: str) -> str:
    """Convert a MIDI file to MusicXML. Returns the path to the written .musicxml file."""
    return str(to_score(Path(midi_path)))


@mcp.tool()
def midi_to_notes(midi_path: str) -> str:
    """Convert a MIDI file to daw-mcp's batch_set_notes note-array JSON. Returns the written .notes.json path."""
    return str(convert_midi_to_notes(Path(midi_path)))


if __name__ == "__main__":
    mcp.run()
