#!/usr/bin/env python3
"""Convert a MusicXML (or other music21-readable score) file to MIDI using music21."""
import argparse
import pathlib
import sys

from music21 import converter


def score_to_midi(score_path: pathlib.Path) -> pathlib.Path:
    """Parse score_path with music21 and write it out as MIDI, return the output path."""
    if not score_path.is_file():
        raise FileNotFoundError(f"Score file not found: {score_path}")

    try:
        score = converter.parse(str(score_path))
    except Exception as e:
        raise RuntimeError(f"music21 failed to parse {score_path}: {e}") from e

    target = score_path.with_suffix(".mid")
    if target.exists():
        raise RuntimeError(f"{target} already exists; move or delete it first")
    score.write("midi", fp=str(target))
    return target


def main() -> None:
    parser = argparse.ArgumentParser(description="Convert a MusicXML file to MIDI.")
    parser.add_argument("score_path", type=pathlib.Path, help="Path to the input score file (.musicxml, .mxl, .xml)")
    args = parser.parse_args()

    try:
        output_path = score_to_midi(args.score_path)
    except (FileNotFoundError, RuntimeError) as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    print(f"Wrote {output_path}")


if __name__ == "__main__":
    main()
