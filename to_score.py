#!/usr/bin/env python3
"""Convert a MIDI file to MusicXML using music21."""
import argparse
import pathlib
import sys

from music21 import converter


def to_score(midi_path: pathlib.Path) -> pathlib.Path:
    """Parse midi_path with music21 and write it out as MusicXML, return the output path."""
    if not midi_path.is_file():
        raise FileNotFoundError(f"MIDI file not found: {midi_path}")

    try:
        score = converter.parse(str(midi_path))
    except Exception as e:
        raise RuntimeError(f"music21 failed to parse {midi_path}: {e}") from e

    target = midi_path.with_suffix(".musicxml")
    score.write("musicxml", fp=str(target))
    return target


def main() -> None:
    parser = argparse.ArgumentParser(description="Convert a MIDI file to MusicXML.")
    parser.add_argument("midi_path", type=pathlib.Path, help="Path to the input MIDI file")
    args = parser.parse_args()

    try:
        output_path = to_score(args.midi_path)
    except (FileNotFoundError, RuntimeError) as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    print(f"Wrote {output_path}")


if __name__ == "__main__":
    main()
