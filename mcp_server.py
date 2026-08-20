#!/usr/bin/env python3
"""MCP server wrapping transcribe.py and to_score.py as tools."""
from pathlib import Path

from mcp.server import MCPServer

from transcribe import transcribe
from to_score import to_score
from midi_to_notes import midi_to_notes as convert_midi_to_notes
from score_to_midi import score_to_midi as convert_score_to_midi
from score_to_pdf import score_to_pdf as convert_score_to_pdf

mcp = MCPServer("audio2score", version="1.3.0")


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


@mcp.tool()
def score_to_midi(score_path: str) -> str:
    """Convert a MusicXML (or other music21-readable score) file to MIDI. Returns the written .mid path."""
    return str(convert_score_to_midi(Path(score_path)))


@mcp.tool()
def score_to_pdf(score_path: str) -> str:
    """Render a MIDI/MusicXML file to PDF via MuseScore. Returns the written .pdf path."""
    return str(convert_score_to_pdf(Path(score_path)))


if __name__ == "__main__":
    mcp.run()
