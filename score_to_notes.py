#!/usr/bin/env python3
"""Convert a score file (MIDI, MusicXML, or anything music21 can read) to daw-mcp's batch_set_notes note-array format."""
import argparse
import json
import pathlib
import sys

from music21 import converter


def score_to_notes(score_path: pathlib.Path) -> pathlib.Path:
    """Parse score_path and write its notes as [x, y, velocity, duration] JSON, return the output path.

    Format-agnostic - music21's converter.parse handles MIDI, MusicXML,
    and its other supported formats identically here, so this works on a
    transcribed .mid or an OMR-derived .mxl with no distinction.

    x/duration are beat positions (music21 quarterLength), matching
    daw-mcp's batch_set_notes ultra-lean note format exactly.
    """
    if not score_path.is_file():
        raise FileNotFoundError(f"Score file not found: {score_path}")

    try:
        score = converter.parse(str(score_path))
    except Exception as e:
        raise RuntimeError(f"music21 failed to parse {score_path}: {e}") from e

    notes = []
    for el in score.flatten().notes:
        pitches = el.pitches if hasattr(el, "pitches") else [el.pitch]
        velocity = el.volume.velocity if el.volume.velocity is not None else 100
        for p in pitches:
            notes.append([
                round(float(el.offset), 4),
                p.midi,
                velocity,
                round(float(el.duration.quarterLength), 4),
            ])
    notes.sort(key=lambda n: n[0])

    target = score_path.with_suffix(".notes.json")
    if target.exists():
        raise RuntimeError(f"{target} already exists; move or delete it first")
    target.write_text(json.dumps(notes))
    return target


def main() -> None:
    parser = argparse.ArgumentParser(description="Convert a score file to a batch_set_notes note array.")
    parser.add_argument("score_path", type=pathlib.Path, help="Path to the input score file (.mid, .musicxml, .mxl)")
    args = parser.parse_args()

    try:
        output_path = score_to_notes(args.score_path)
    except (FileNotFoundError, RuntimeError) as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    print(f"Wrote {output_path}")


if __name__ == "__main__":
    main()
