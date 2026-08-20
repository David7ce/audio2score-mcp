#!/usr/bin/env python3
"""MCP server wrapping transcribe.py, to_score.py, and score_to_notes.py as tools."""
from pathlib import Path

from mcp.server import MCPServer

from transcribe import transcribe
from to_score import to_score
from score_to_notes import score_to_notes as convert_score_to_notes

mcp = MCPServer("audio2score", version="2.0.0")


@mcp.tool()
def transcribe_audio(audio_path: str) -> str:
    """Transcribe an audio file to MIDI. Returns the path to the written .mid file."""
    return str(transcribe(Path(audio_path)))


@mcp.tool()
def midi_to_score(midi_path: str) -> str:
    """Convert a MIDI file to MusicXML. Returns the path to the written .musicxml file."""
    return str(to_score(Path(midi_path)))


@mcp.tool()
def score_to_notes(score_path: str) -> str:
    """Convert a score file (MIDI, MusicXML, or anything music21 can read) to daw-mcp's batch_set_notes note-array JSON. Returns the written .notes.json path."""
    return str(convert_score_to_notes(Path(score_path)))


if __name__ == "__main__":
    mcp.run()
